"""
LLMクライアント
llama-cpp-pythonを使用してローカルLLMモデルとのインターフェースを提供
"""
import os
import logging
import threading
import queue
import platform
import traceback
from pathlib import Path
from typing import Optional, Iterator, Dict, Any, List
from dataclasses import dataclass

# 安全なロガーを使用
try:
    from . import get_safe_logger
    logger = get_safe_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.NullHandler())


def detect_gpu_availability() -> int:
    """
    GPUの利用可能性を検出し、推奨されるGPUレイヤー数を返す
    
    Returns:
        int: GPU使用レイヤー数（0=CPU only, -1=全レイヤーをGPUに配置）
    """
    try:
        # CUDA環境変数をチェック
        cuda_visible_devices = os.environ.get('CUDA_VISIBLE_DEVICES', '')
        if cuda_visible_devices == '-1':
            logger.info("CUDA_VISIBLE_DEVICES=-1: GPU disabled by environment")
            return 0
        
        # プラットフォームチェック
        system = platform.system()
        
        if system == "Windows" or system == "Linux":
            # NVIDIAドライバーの存在をチェック
            try:
                import subprocess
                result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info("NVIDIA GPU detected via nvidia-smi")
                    return -1  # 全レイヤーをGPUに配置
            except (FileNotFoundError, subprocess.SubprocessError):
                pass
        
        elif system == "Darwin":  # macOS
            # Apple Siliconの場合、Metalを使用可能
            try:
                import subprocess
                result = subprocess.run(['system_profiler', 'SPDisplaysDataType'], 
                                      capture_output=True, text=True)
                if 'Metal' in result.stdout or 'M1' in result.stdout or 'M2' in result.stdout or 'M3' in result.stdout:
                    logger.info("Apple Silicon GPU detected")
                    return -1  # 全レイヤーをGPUに配置
            except:
                pass
        
        # llama-cpp-pythonのビルド情報をチェック
        try:
            from llama_cpp import llama_cpp
            if hasattr(llama_cpp, 'GGML_USE_CUBLAS') and llama_cpp.GGML_USE_CUBLAS:
                logger.info("llama-cpp-python built with CUDA support")
                return -1
            elif hasattr(llama_cpp, 'GGML_USE_METAL') and llama_cpp.GGML_USE_METAL:
                logger.info("llama-cpp-python built with Metal support")
                return -1
        except:
            pass
        
    except Exception as e:
        logger.debug(f"Error detecting GPU: {e}")
        logger.debug(f"GPU detection stack trace:\n{traceback.format_exc()}")
    
    logger.info("No GPU detected, using CPU")
    return 0


@dataclass
class ModelConfig:
    """モデル設定"""
    model_path: str
    n_ctx: int = 4096  # コンテキストサイズ
    n_gpu_layers: int = -2  # GPU使用レイヤー数（-2=自動検出, -1=全て, 0=CPU only）
    temperature: float = 0.3
    max_tokens: int = 2048
    top_p: float = 0.95
    top_k: int = 40
    repeat_penalty: float = 1.1
    n_threads: Optional[int] = None  # None = auto


class LLMClient:
    """
    ローカルLLMとの通信を管理するクライアント
    遅延読み込みとストリーミング応答をサポート
    外部プロバイダー（ChatGPT、Ollama、OpenRouter）もサポート
    """
    
    def __init__(self, config: Optional[ModelConfig] = None):
        self._model = None
        self._config = config
        self._loading = False
        self._load_lock = threading.Lock()
        self._load_error: Optional[Exception] = None
        self._load_thread = None
        self._shutdown = False
        
        # ストリーミング用のキュー
        self._response_queue: queue.Queue = queue.Queue()
        self._streaming = False
        
        # 外部プロバイダー
        self._external_provider = None
        self._current_provider = None  # 現在設定されているプロバイダーを追跡
        
        # デフォルトシステムプロンプト（統合版）
        self.default_system_prompt = """You are an expert programming assistant integrated into Thonny IDE.

Core principles:
- Be concise and direct in your responses
- Provide code examples without lengthy explanations unless asked
- Focus on solving the immediate problem
- Adapt complexity to user's skill level
- Detect and work with the programming language being used

When generating code:
- Write clean, readable code following the language's best practices
- Include only essential comments
- Handle edge cases appropriately

When explaining:
- Keep explanations brief and to the point
- Use simple language for beginners
- Provide more detail only when specifically requested

Remember: Prioritize clarity and brevity. Get straight to the solution."""

        # デフォルトプロンプトを使用
        self.system_prompt = self.default_system_prompt
    
    @property
    def is_loaded(self) -> bool:
        """モデルがロードされているか（外部プロバイダーの場合は常にTrue）"""
        if self._external_provider:
            return True
        return self._model is not None
    
    @property
    def is_loading(self) -> bool:
        """モデルをロード中か"""
        return self._loading
    
    def get_config(self) -> ModelConfig:
        """現在の設定を取得"""
        # 毎回プロバイダーをチェック
        from thonny import get_workbench
        workbench = get_workbench()
        provider = workbench.get_option("llm.provider", "local")
        
        # プロバイダーが変更された場合は再設定
        if provider != self._current_provider:
            self._current_provider = provider
            self._external_provider = None  # 古いプロバイダーをクリア
            if provider != "local":
                self._setup_external_provider(provider)
        
        if self._config is None:
            
            model_path = workbench.get_option("llm.model_path", "")
            if not model_path and provider == "local":
                # モデルディレクトリから最初のGGUFファイルを探す
                models_dir = Path(__file__).parent.parent.parent / "models"
                if models_dir.exists():
                    gguf_files = list(models_dir.glob("*.gguf"))
                    if gguf_files:
                        model_path = str(gguf_files[0])
            
            self._config = ModelConfig(
                model_path=model_path,
                n_ctx=workbench.get_option("llm.context_size", 4096),
                temperature=workbench.get_option("llm.temperature", 0.3),
                max_tokens=workbench.get_option("llm.max_tokens", 2048),
                repeat_penalty=workbench.get_option("llm.repeat_penalty", 1.1),
            )
            
            # プロンプトタイプを適用
            prompt_type = workbench.get_option("llm.prompt_type", "default")
            
            if prompt_type == "custom":
                custom_prompt = workbench.get_option("llm.custom_prompt", "")
                if custom_prompt:
                    self.set_system_prompt(custom_prompt)
            else:
                # デフォルトプロンプトを使用
                self.use_default_prompt()
        
        return self._config
    
    def _detect_programming_language(self) -> str:
        """現在のエディタファイルからプログラミング言語を検出"""
        try:
            from thonny import get_workbench
            workbench = get_workbench()
            editor = workbench.get_editor_notebook().get_current_editor()
            
            if editor:
                filename = editor.get_filename()
                if filename:
                    file_ext = Path(filename).suffix.lower()
                    # ファイル拡張子から言語を判定
                    from .utils.constants import LANGUAGE_EXTENSIONS
                    return LANGUAGE_EXTENSIONS.get(file_ext, 'Python')  # デフォルトはPython
        except Exception:
            pass
        
        return 'Python'  # エラー時のデフォルト
    
    def _get_language_instruction(self) -> str:
        """言語設定に基づく指示を取得"""
        from thonny import get_workbench
        workbench = get_workbench()
        
        output_language = workbench.get_option("llm.output_language", "auto")
        
        if output_language == "auto":
            # Thonnyの言語設定に従う
            thonny_language = workbench.get_option("general.language", None)
            if thonny_language and thonny_language.startswith("ja"):
                return "\nPlease respond in Japanese (日本語で回答してください)."
            elif thonny_language and thonny_language.startswith("zh"):
                if "TW" in thonny_language or "HK" in thonny_language:
                    return "\nPlease respond in Traditional Chinese (請用繁體中文回答)."
                else:
                    return "\nPlease respond in Simplified Chinese (请用简体中文回答)."
            else:
                return ""  # 英語はデフォルトなので指示不要
        elif output_language == "ja":
            return "\nPlease respond in Japanese (日本語で回答してください)."
        elif output_language == "en":
            return ""  # 英語はデフォルトなので指示不要
        elif output_language == "zh-CN":
            return "\nPlease respond in Simplified Chinese (请用简体中文回答)."
        elif output_language == "zh-TW":
            return "\nPlease respond in Traditional Chinese (請用繁體中文回答)."
        elif output_language == "other":
            custom_code = workbench.get_option("llm.custom_language_code", "")
            if custom_code:
                return f"\nPlease respond in {custom_code}."
        
        return ""
    
    def _build_system_prompt(self) -> str:
        """言語設定とスキルレベルを含むシステムプロンプトを構築"""
        from thonny import get_workbench
        workbench = get_workbench()
        
        # 基本のシステムプロンプトを取得
        base_prompt = self.system_prompt
        
        # プログラミング言語を検出
        prog_language = self._detect_programming_language()
        
        # プロンプトタイプを確認
        prompt_type = workbench.get_option("llm.prompt_type", "default")
        skill_level = workbench.get_option("llm.skill_level", "beginner")
        output_language = workbench.get_option("llm.output_language", "auto")
        
        if prompt_type == "custom":
            # カスタムプロンプトの場合は、変数を置換
            enhanced_prompt = base_prompt
            
            # スキルレベルの詳細な説明を作成
            skill_level_descriptions = {
                "beginner": "beginner (new to programming, needs detailed explanations, simple examples, and encouragement)",
                "intermediate": "intermediate (familiar with basics, can understand technical terms, needs guidance on best practices)",
                "advanced": "advanced (experienced developer, prefers concise technical explanations, interested in optimization and design patterns)"
            }
            
            # 変数を置換
            enhanced_prompt = enhanced_prompt.replace("{skill_level}", skill_level_descriptions.get(skill_level, skill_level))
            enhanced_prompt = enhanced_prompt.replace("{language}", output_language if output_language != "auto" else "the user's language")
            
            # プログラミング言語を追加
            enhanced_prompt += f"\n\nCurrent programming language: {prog_language}"
            
            # 出力言語指示を追加
            language_instruction = self._get_language_instruction()
            if language_instruction:
                enhanced_prompt += language_instruction
            
            return enhanced_prompt
        
        # デフォルトプロンプトの場合は、スキルレベル、プログラミング言語、出力言語を統合
        
        # プログラミング言語の指示を追加
        enhanced_prompt = base_prompt + f"\n\nCurrent programming language: {prog_language}"
        
        # スキルレベルの詳細な説明を追加
        skill_instructions = {
            "beginner": """\n\nIMPORTANT: The user is a BEGINNER programmer. Follow these guidelines:
- Use simple, everyday language and avoid technical jargon
- Explain concepts step-by-step with clear examples
- Provide encouragement and positive reinforcement
- Anticipate common mistakes and explain how to avoid them
- Use analogies to relate programming concepts to real-world scenarios
- Keep code examples short and well-commented
- Explain what each line of code does""",
            "intermediate": """\n\nIMPORTANT: The user has INTERMEDIATE programming knowledge. Follow these guidelines:
- Balance technical accuracy with clarity
- Introduce best practices and coding standards
- Explain the 'why' behind recommendations
- Provide multiple solution approaches when relevant
- Include error handling and edge cases
- Reference documentation and useful resources
- Encourage exploration of advanced features""",
            "advanced": """\n\nIMPORTANT: The user is an ADVANCED programmer. Follow these guidelines:
- Be concise and technically precise
- Focus on optimization, performance, and design patterns
- Discuss trade-offs and architectural decisions
- Assume familiarity with programming concepts
- Include advanced techniques and idioms
- Reference relevant specifications and standards
- Skip basic explanations unless specifically asked"""
        }
        
        # スキルレベルの指示を追加
        enhanced_prompt += skill_instructions.get(skill_level, "")
        
        # 出力言語指示を追加
        language_instruction = self._get_language_instruction()
        if language_instruction:
            enhanced_prompt += language_instruction
        
        return enhanced_prompt
    
    def _setup_external_provider(self, provider: str):
        """外部プロバイダーをセットアップ"""
        from thonny import get_workbench
        from .external_providers import ChatGPTProvider, OllamaProvider, OpenRouterProvider
        
        workbench = get_workbench()
        
        if provider == "chatgpt":
            self._external_provider = ChatGPTProvider(
                api_key=workbench.get_option("llm.chatgpt_api_key", ""),
                model=workbench.get_option("llm.external_model", "gpt-3.5-turbo")
            )
        elif provider == "ollama":
            self._external_provider = OllamaProvider(
                base_url=workbench.get_option("llm.base_url", "http://localhost:11434"),
                model=workbench.get_option("llm.external_model", "llama3")
            )
        elif provider == "openrouter":
            self._external_provider = OpenRouterProvider(
                api_key=workbench.get_option("llm.openrouter_api_key", ""),
                model=workbench.get_option("llm.external_model", "meta-llama/llama-3.2-3b-instruct:free")
            )
    
    def set_config(self, config: ModelConfig):
        """設定を更新（モデルの再読み込みが必要）"""
        self._config = config
        if self._model is not None:
            # 既存のモデルをアンロード
            self.unload_model()
    
    def load_model(self, force: bool = False) -> bool:
        """
        モデルを同期的に読み込む
        
        Args:
            force: 既にロードされていても再読み込みする
            
        Returns:
            読み込みに成功したらTrue
        """
        # 外部プロバイダーの場合はモデルロード不要
        if self._external_provider:
            return True
        
        if self._model is not None and not force:
            return True
        
        with self._load_lock:
            if self._loading:
                return False
            
            self._loading = True
            self._load_error = None
            
            try:
                config = self.get_config()
                if not config.model_path or not Path(config.model_path).exists():
                    raise FileNotFoundError(f"Model file not found: {config.model_path}")
                
                logger.info(f"Loading model from: {config.model_path}")
                
                try:
                    from llama_cpp import Llama
                except ImportError:
                    raise ImportError(
                        "llama-cpp-python is not installed. "
                        "Please run: uv pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu"
                    )
                
                # GPU自動検出
                n_gpu_layers = config.n_gpu_layers
                if n_gpu_layers == -2:  # 自動検出
                    n_gpu_layers = detect_gpu_availability()
                    logger.info(f"Auto-detected GPU layers: {n_gpu_layers}")
                
                # モデルを読み込む
                self._model = Llama(
                    model_path=config.model_path,
                    n_ctx=config.n_ctx,
                    n_gpu_layers=n_gpu_layers,
                    n_threads=config.n_threads,
                    verbose=False,
                )
                
                # 実際に使用されているGPUレイヤー数をログ出力
                if n_gpu_layers > 0:
                    logger.info(f"Model loaded with {n_gpu_layers} GPU layers")
                elif n_gpu_layers == -1:
                    logger.info("Model loaded with all layers on GPU")
                else:
                    logger.info("Model loaded on CPU")
                
                logger.info("Model loaded successfully")
                return True
                
            except ImportError as e:
                error_msg = f"Failed to import llama-cpp-python: {e}"
                logger.error(error_msg)
                logger.error(f"Import error stack trace:\n{traceback.format_exc()}")
                self._load_error = e
                return False
            except FileNotFoundError as e:
                error_msg = f"Model file not found at {config.model_path}: {e}"
                logger.error(error_msg)
                self._load_error = e
                return False
            except Exception as e:
                error_msg = f"Failed to load model from {config.model_path}: {e}"
                logger.error(error_msg)
                logger.error(f"Model loading stack trace:\n{traceback.format_exc()}")
                logger.error(f"Model config: n_ctx={config.n_ctx}, n_gpu_layers={n_gpu_layers}")
                self._load_error = e
                return False
            finally:
                self._loading = False
    
    def load_model_async(self, callback=None):
        """
        モデルを非同期で読み込む
        
        Args:
            callback: 読み込み完了時に呼ばれるコールバック(success: bool, error: Optional[Exception])
        """
        def _load():
            if self._shutdown:
                return
            success = self.load_model()
            if callback and not self._shutdown:
                callback(success, self._load_error)
        
        self._load_thread = threading.Thread(target=_load, daemon=True)
        self._load_thread.start()
    
    def unload_model(self):
        """モデルをアンロード"""
        if self._model is not None:
            del self._model
            self._model = None
            logger.info("Model unloaded")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        プロンプトに対する応答を生成（同期）
        
        Args:
            prompt: 入力プロンプト
            **kwargs: 生成パラメータのオーバーライド
            
        Returns:
            生成されたテキスト
        """
        # 外部プロバイダーを使用する場合
        if self._external_provider:
            # システムプロンプトを構築
            system_content = self._build_system_prompt()
            
            messages = [
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ]
            return self._external_provider.generate(
                prompt=prompt,
                messages=messages,
                temperature=kwargs.get("temperature", self.get_config().temperature),
                max_tokens=kwargs.get("max_tokens", self.get_config().max_tokens)
            )
        
        # ローカルモデルを使用する場合
        if self._model is None:
            if not self.load_model():
                raise RuntimeError(f"Failed to load model: {self._load_error}")
        
        config = self.get_config()
        
        # パラメータをマージ
        params = {
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "top_k": config.top_k,
            "repeat_penalty": config.repeat_penalty,
            "stop": ["</s>", "\n\n\n"],
        }
        # messagesパラメータは除外（ローカルモデルでは使用しない）
        kwargs_without_messages = {k: v for k, v in kwargs.items() if k != "messages"}
        params.update(kwargs_without_messages)
        
        # フルプロンプトを作成
        full_prompt = self._format_prompt(prompt)
        
        # 生成
        response = self._model(full_prompt, **params)
        return response["choices"][0]["text"].strip()
    
    def generate_stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """
        プロンプトに対する応答をストリーミング生成
        
        Args:
            prompt: 入力プロンプト
            **kwargs: 生成パラメータのオーバーライド
            
        Yields:
            生成されたテキストのチャンク
        """
        # 外部プロバイダーを使用する場合
        if self._external_provider:
            # システムプロンプトを構築
            system_content = self._build_system_prompt()
            
            # 会話履歴を含むメッセージリストを構築
            messages = [{"role": "system", "content": system_content}]
            
            # 既存の会話履歴があれば追加
            if "messages" in kwargs:
                for msg in kwargs["messages"]:
                    # システムメッセージは除外（既に追加済み）
                    if msg.get("role") != "system":
                        messages.append(msg)
            
            # 現在のユーザーメッセージを追加
            messages.append({"role": "user", "content": prompt})
            
            for token in self._external_provider.generate_stream(
                prompt=prompt,
                messages=messages,
                temperature=kwargs.get("temperature", self.get_config().temperature),
                max_tokens=kwargs.get("max_tokens", self.get_config().max_tokens)
            ):
                yield token
            return
        
        # ローカルモデルを使用する場合
        if self._model is None:
            if not self.load_model():
                raise RuntimeError(f"Failed to load model: {self._load_error}")
        
        config = self.get_config()
        
        # パラメータをマージ
        params = {
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "top_k": config.top_k,
            "repeat_penalty": config.repeat_penalty,
            "stop": ["</s>", "\n\n\n"],
            "stream": True,
        }
        # messagesパラメータは除外（ローカルモデルでは使用しない）
        kwargs_without_messages = {k: v for k, v in kwargs.items() if k != "messages"}
        params.update(kwargs_without_messages)
        
        # 会話履歴がある場合は、chat completion APIを使用
        if "messages" in kwargs:
            # メッセージリストを構築
            messages = []
            
            # システムプロンプトを追加
            system_prompt = self._build_system_prompt()
            messages.append({"role": "system", "content": system_prompt})
            
            # 既存の会話履歴を追加
            for msg in kwargs["messages"]:
                if msg.get("role") != "system":  # システムプロンプトは既に追加済み
                    messages.append(msg)
            
            # 現在のメッセージを追加
            messages.append({"role": "user", "content": prompt})
            
            # Chat completion APIを使用（llama-cpp-pythonがサポートしている場合）
            try:
                # create_chat_completionメソッドが利用可能か確認
                if hasattr(self._model, 'create_chat_completion'):
                    # stopパラメータを調整（chat completion用）
                    params_for_chat = params.copy()
                    params_for_chat['stop'] = ["</s>"]  # chat completion用のストップトークン
                    
                    for output in self._model.create_chat_completion(messages, **params_for_chat):
                        if "choices" in output and len(output["choices"]) > 0:
                            delta = output["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                else:
                    # フォールバック: 従来の方法でプロンプトを構築
                    full_prompt = self._format_messages_as_prompt(messages)
                    for output in self._model(full_prompt, **params):
                        token = output["choices"][0]["text"]
                        if token:
                            yield token
            except Exception as e:
                logger.warning(f"Chat completion failed, falling back to text completion: {e}")
                # エラー時のフォールバック
                full_prompt = self._format_messages_as_prompt(messages)
                for output in self._model(full_prompt, **params):
                    token = output["choices"][0]["text"]
                    if token:
                        yield token
        else:
            # 従来の単一プロンプト形式
            full_prompt = self._format_prompt(prompt)
            for output in self._model(full_prompt, **params):
                token = output["choices"][0]["text"]
                if token:
                    yield token
    
    def _format_messages_as_prompt(self, messages: list) -> str:
        """
        OpenAI形式のメッセージリストをプロンプト文字列に変換
        
        Args:
            messages: [{"role": "system/user/assistant", "content": "..."}, ...]
            
        Returns:
            フォーマットされたプロンプト文字列
        """
        parts = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "system":
                parts.append(content)
            elif role == "user":
                parts.append(f"\n\nHuman: {content}")
            elif role == "assistant":
                parts.append(f"\n\nAssistant: {content}")
        
        # 最後にアシスタントの応答を促す
        parts.append("\n\nAssistant:")
        
        return "".join(parts)
    
    def set_system_prompt(self, prompt: str):
        """カスタムシステムプロンプトを設定"""
        self.system_prompt = prompt
    
    def use_default_prompt(self):
        """デフォルトシステムプロンプトを使用"""
        self.system_prompt = self.default_system_prompt
    
    def get_current_system_prompt(self) -> str:
        """現在のシステムプロンプトを取得"""
        return self.system_prompt
    
    def explain_code(self, code: str, skill_level: str = "beginner") -> str:
        """
        コードを説明する特化したメソッド
        
        Args:
            code: 説明するコード
            skill_level: ユーザーのスキルレベル (beginner/intermediate/advanced)
            
        Returns:
            コードの説明
        """
        skill_descriptions = {
            "beginner": "a complete beginner who is just learning programming",
            "intermediate": "someone with basic programming knowledge",
            "advanced": "an experienced programmer"
        }
        
        # プログラミング言語を検出
        prog_language = self._detect_programming_language()
        lang_lower = prog_language.lower()
        
        prompt = f"""Explain this {prog_language} code for {skill_descriptions.get(skill_level, skill_descriptions['beginner'])}:

```{lang_lower}
{code}
```

Be concise. Focus on what the code does and key concepts."""
        
        return self.generate(prompt, temperature=0.3)  # 低めの温度で一貫性のある説明を生成
    
    def fix_error(self, code: str, error_message: str) -> str:
        """
        エラーを修正する提案を生成
        
        Args:
            code: エラーが発生したコード
            error_message: エラーメッセージ
            
        Returns:
            修正提案
        """
        # プログラミング言語を検出
        prog_language = self._detect_programming_language()
        lang_lower = prog_language.lower()
        
        prompt = f"""Fix this {prog_language} error:

```{lang_lower}
{code}
```

Error:
```
{error_message}
```

Provide:
1. Brief explanation of the error
2. Corrected code
3. What changed"""
        
        return self.generate(prompt, temperature=0.3)
    
    def generate_with_context(self, prompt: str, context: str, **kwargs) -> str:
        """
        コンテキスト付きで応答を生成
        
        Args:
            prompt: ユーザープロンプト
            context: プロジェクトコンテキスト
            **kwargs: 生成パラメータ
            
        Returns:
            生成されたテキスト
        """
        # コンテキストを含むプロンプトを作成
        full_prompt = f"""Here is the context from the current project:

{context}

Based on this context, {prompt}"""
        
        return self.generate(full_prompt, **kwargs)
    
    def _format_prompt(self, user_prompt: str) -> str:
        """プロンプトをモデル用にフォーマット"""
        # システムプロンプトを構築
        system_content = self._build_system_prompt()
        
        # 簡単なChat MLフォーマット（モデルによって調整が必要）
        return f"""<|system|>
{system_content}
<|user|>
{user_prompt}
<|assistant|>
"""
    
    def test_connection(self) -> Dict[str, Any]:
        """
        接続とモデルをテスト
        
        Returns:
            テスト結果の辞書
        """
        # 外部プロバイダーの場合
        if self._external_provider:
            return self._external_provider.test_connection()
        
        # ローカルモデルの場合
        result = {
            "model_loaded": self.is_loaded,
            "model_path": self.get_config().model_path,
            "error": None,
            "test_response": None,
            "success": False
        }
        
        try:
            if not self.is_loaded:
                self.load_model()
            
            # 簡単なテストプロンプト
            test_response = self.generate(
                "Say 'Hello from LLM!' in exactly 5 words.",
                max_tokens=20,
                temperature=0.1
            )
            result["test_response"] = test_response
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def shutdown(self):
        """クライアントをシャットダウンして、すべてのスレッドを適切に終了"""
        self._shutdown = True
        self._stop_generation = True
        
        # ローディングスレッドの終了を待つ
        if self._load_thread and self._load_thread.is_alive():
            self._load_thread.join(timeout=5.0)
        
        # モデルをアンロード
        self.unload_model()
        
        # キューをクリア
        while not self._response_queue.empty():
            try:
                self._response_queue.get_nowait()
            except queue.Empty:
                break