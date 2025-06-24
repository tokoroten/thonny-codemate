"""
LLMクライアント
llama-cpp-pythonを使用してローカルLLMモデルとのインターフェースを提供
"""
import os
import logging
import threading
import queue
from pathlib import Path
from typing import Optional, Iterator, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """モデル設定"""
    model_path: str
    n_ctx: int = 4096  # コンテキストサイズ
    n_gpu_layers: int = 0  # GPU使用レイヤー数（0=CPU only）
    temperature: float = 0.7
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
        
        # ストリーミング用のキュー
        self._response_queue: queue.Queue = queue.Queue()
        self._streaming = False
        
        # 外部プロバイダー
        self._external_provider = None
        
        # デフォルトシステムプロンプト（コーディング最適化版）
        self.coding_system_prompt = """You are an expert Python programming assistant integrated into Thonny IDE, designed to help users write clean, efficient, and well-structured code.

Your responsibilities:
1. Generate correct, idiomatic Python code that follows PEP 8 style guidelines
2. Write code that is readable, maintainable, and well-commented when necessary
3. Consider edge cases and error handling in your implementations
4. Use appropriate data structures and algorithms for the task
5. Prefer simple, clear solutions over complex ones unless complexity is justified

When generating code:
- Include type hints for function parameters and return values when it improves clarity
- Use descriptive variable and function names
- Add docstrings for functions and classes
- Handle common edge cases (empty inputs, None values, etc.)
- Avoid global variables and side effects when possible

When explaining code:
- Be concise but thorough
- Explain the "why" behind design decisions
- Point out potential improvements or alternatives
- Adapt explanations to the user's skill level

Remember: You're helping users learn and write better Python code. Focus on teaching good practices while solving their immediate needs."""

        # 解説用システムプロンプト
        self.explanation_system_prompt = """You are a patient and knowledgeable Python teacher integrated into Thonny IDE, specializing in explaining code and programming concepts clearly.

Your teaching approach:
1. Break down complex concepts into simple, understandable parts
2. Use analogies and real-world examples when helpful
3. Explain not just "what" the code does, but "why" it works that way
4. Anticipate common misconceptions and address them proactively
5. Encourage good programming practices and habits

When explaining code:
- Start with a high-level overview, then go into details
- Explain each important line or block of code
- Point out any Python-specific features or idioms
- Highlight potential pitfalls or common mistakes
- Suggest improvements or alternative approaches when relevant

Adapt your explanations based on the user's skill level:
- Beginner: Use simple language, avoid jargon, explain basic concepts
- Intermediate: Assume basic knowledge, introduce more advanced concepts gradually
- Advanced: Focus on optimization, design patterns, and best practices

Your goal is to help users not just understand the code, but become better programmers."""

        # デフォルトは用途に応じて選択
        self.system_prompt = self.coding_system_prompt
    
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
        if self._config is None:
            # デフォルト設定を作成
            from thonny import get_workbench
            workbench = get_workbench()
            
            # プロバイダーをチェック
            provider = workbench.get_option("llm.provider", "local")
            
            if provider != "local":
                # 外部プロバイダーを設定
                self._setup_external_provider(provider)
            
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
                temperature=workbench.get_option("llm.temperature", 0.7),
                max_tokens=workbench.get_option("llm.max_tokens", 2048),
            )
            
            # プロンプトタイプを適用
            prompt_type = workbench.get_option("llm.prompt_type", "coding")
            if prompt_type == "coding":
                self.use_coding_prompt()
            elif prompt_type == "explanation":
                self.use_explanation_prompt()
            elif prompt_type == "custom":
                custom_prompt = workbench.get_option("llm.custom_prompt", "")
                if custom_prompt:
                    self.set_system_prompt(custom_prompt)
        
        return self._config
    
    def _setup_external_provider(self, provider: str):
        """外部プロバイダーをセットアップ"""
        from thonny import get_workbench
        from .external_providers import ChatGPTProvider, OllamaProvider, OpenRouterProvider
        
        workbench = get_workbench()
        
        if provider == "chatgpt":
            self._external_provider = ChatGPTProvider(
                api_key=workbench.get_option("llm.api_key", ""),
                model=workbench.get_option("llm.external_model", "gpt-3.5-turbo")
            )
        elif provider == "ollama":
            self._external_provider = OllamaProvider(
                base_url=workbench.get_option("llm.base_url", "http://localhost:11434"),
                model=workbench.get_option("llm.external_model", "llama3")
            )
        elif provider == "openrouter":
            self._external_provider = OpenRouterProvider(
                api_key=workbench.get_option("llm.api_key", ""),
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
                
                # モデルを読み込む
                self._model = Llama(
                    model_path=config.model_path,
                    n_ctx=config.n_ctx,
                    n_gpu_layers=config.n_gpu_layers,
                    n_threads=config.n_threads,
                    verbose=False,
                )
                
                logger.info("Model loaded successfully")
                return True
                
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
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
            success = self.load_model()
            if callback:
                callback(success, self._load_error)
        
        thread = threading.Thread(target=_load, daemon=True)
        thread.start()
    
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
            messages = [
                {"role": "system", "content": self.system_prompt},
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
        params.update(kwargs)
        
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
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
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
        params.update(kwargs)
        
        # フルプロンプトを作成
        full_prompt = self._format_prompt(prompt)
        
        # ストリーミング生成
        for output in self._model(full_prompt, **params):
            token = output["choices"][0]["text"]
            if token:
                yield token
    
    def set_system_prompt(self, prompt: str):
        """カスタムシステムプロンプトを設定"""
        self.system_prompt = prompt
    
    def use_coding_prompt(self):
        """コーディング用システムプロンプトを使用"""
        self.system_prompt = self.coding_system_prompt
    
    def use_explanation_prompt(self):
        """解説用システムプロンプトを使用"""
        self.system_prompt = self.explanation_system_prompt
    
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
        # 一時的に解説用プロンプトを使用
        original_prompt = self.system_prompt
        self.system_prompt = self.explanation_system_prompt
        
        try:
            skill_descriptions = {
                "beginner": "a complete beginner who is just learning programming",
                "intermediate": "someone with basic programming knowledge",
                "advanced": "an experienced programmer"
            }
            
            prompt = f"""Please explain the following Python code for {skill_descriptions.get(skill_level, skill_descriptions['beginner'])}:

```python
{code}
```

Provide a clear, educational explanation that helps them understand:
1. What the code does overall
2. How each important part works
3. Any important concepts or patterns used

Keep the explanation concise but thorough."""
            
            return self.generate(prompt, temperature=0.3)  # 低めの温度で一貫性のある説明を生成
        finally:
            # 元のプロンプトに戻す
            self.system_prompt = original_prompt
    
    def fix_error(self, code: str, error_message: str) -> str:
        """
        エラーを修正する提案を生成
        
        Args:
            code: エラーが発生したコード
            error_message: エラーメッセージ
            
        Returns:
            修正提案
        """
        prompt = f"""The following Python code has an error:

```python
{code}
```

Error message:
```
{error_message}
```

Please:
1. Explain what causes this error
2. Provide the corrected code
3. Explain what was changed and why

Format your response clearly with the corrected code in a code block."""
        
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
        # 簡単なChat MLフォーマット（モデルによって調整が必要）
        return f"""<|system|>
{self.system_prompt}
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