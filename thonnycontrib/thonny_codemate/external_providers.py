"""
外部LLMプロバイダーのサポート
ChatGPT、Ollama API、OpenRouterに対応
"""
import os
import json
import logging
import time
from typing import Optional, Iterator, Dict, Any
from abc import ABC, abstractmethod
import urllib.request
import urllib.error
import ssl
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from ..utils.retry import retry_network_operation
except ImportError:
    # フォールバック: リトライなし
    def retry_network_operation(func):
        return func

logger = logging.getLogger(__name__)


def retry_on_network_error(max_attempts=3, delay=1.0, backoff=2.0):
    """ネットワークエラー時にリトライするデコレーター"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_error = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        logger.info(f"Network error, retrying in {current_delay}s: {e}")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise
            
            if last_error:
                raise last_error
        return wrapper
    return decorator


class ExternalProvider(ABC):
    """外部プロバイダーの基底クラス"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """テキスト生成"""
        pass
    
    @abstractmethod
    def generate_stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """ストリーミング生成"""
        pass
    
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """接続テスト"""
        pass


class ChatGPTProvider(ExternalProvider):
    """OpenAI ChatGPT APIプロバイダー"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", base_url: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    @retry_on_network_error()
    def generate(self, prompt: str, **kwargs) -> str:
        """ChatGPT APIを使用してテキスト生成"""
        messages = kwargs.get("messages", [{"role": "user", "content": prompt}])
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
            "stream": False
        }
        
        try:
            req = urllib.request.Request(
                f"{self.base_url}/chat/completions",
                data=json.dumps(data).encode('utf-8'),
                headers=self.headers
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result['choices'][0]['message']['content']
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            logger.error(f"ChatGPT API error: {e.code} - {error_body}")
            
            # より詳細なエラーメッセージ
            if e.code == 401:
                raise Exception("Invalid API key. Please check your ChatGPT API key.")
            elif e.code == 429:
                raise Exception("Rate limit exceeded. Please try again later.")
            elif e.code == 500:
                raise Exception("ChatGPT server error. Please try again later.")
            else:
                raise Exception(f"ChatGPT API error ({e.code}): {error_body}")
        except Exception as e:
            logger.error(f"ChatGPT request failed: {e}")
            raise
    
    def generate_stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """ChatGPT APIを使用してストリーミング生成"""
        messages = kwargs.get("messages", [{"role": "user", "content": prompt}])
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
            "stream": True
        }
        
        try:
            req = urllib.request.Request(
                f"{self.base_url}/chat/completions",
                data=json.dumps(data).encode('utf-8'),
                headers=self.headers
            )
            
            with urllib.request.urlopen(req) as response:
                for line in response:
                    line = line.decode('utf-8').strip()
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    yield delta['content']
                        except json.JSONDecodeError:
                            continue
                            
        except urllib.error.HTTPError as e:
            import traceback
            logger.error(f"ChatGPT streaming HTTP error: {e}\n{traceback.format_exc()}")
            if e.code == 401:
                yield "[Error: Invalid API key]"
            else:
                yield f"[Error: HTTP {e.code}]"
            return
        except Exception as e:
            import traceback
            logger.error(f"ChatGPT streaming failed: {e}\n{traceback.format_exc()}")
            yield f"[Error: {str(e)}]"
            return
    
    def get_model_info(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """モデルの詳細情報を取得（コンテキストサイズを含む）"""
        model = model_name or self.model
        
        # OpenAI/ChatGPTのコンテキストサイズは既知の値で判定
        openai_models = {
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
            "gpt-4-turbo": 128000,
            "gpt-4-turbo-preview": 128000,
            "gpt-4-0125-preview": 128000,
            "gpt-4-1106-preview": 128000,
            "gpt-4": 8192,
            "gpt-4-0613": 8192,
            "gpt-4-32k": 32768,
            "gpt-4-32k-0613": 32768,
            "gpt-3.5-turbo": 16385,
            "gpt-3.5-turbo-0125": 16385,
            "gpt-3.5-turbo-1106": 16385,
            "gpt-3.5-turbo-16k": 16385,
            "text-davinci-003": 4097,
            "text-davinci-002": 4097,
        }
        
        # 完全一致
        if model in openai_models:
            return {"context_size": openai_models[model]}
        
        # 部分一致（モデル名にバージョンが含まれる場合）
        for known_model, size in openai_models.items():
            if known_model in model:
                return {"context_size": size}
        
        # 不明なモデルの場合
        return {"context_size": None, "error": f"Unknown model: {model}"}
    
    @retry_network_operation
    def test_connection(self) -> Dict[str, Any]:
        """接続テスト（リトライ付き）"""
        try:
            response = self.generate("Say 'Hello!' in exactly one word.", max_tokens=10)
            return {
                "success": True,
                "provider": "ChatGPT",
                "model": self.model,
                "response": response
            }
        except Exception as e:
            return {
                "success": False,
                "provider": "ChatGPT",
                "model": self.model,
                "error": str(e)
            }


class OllamaProvider(ExternalProvider):
    """Ollama/LM Studio APIプロバイダー"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.headers = {"Content-Type": "application/json"}
        
        # LM Studioかどうかを判定（まずポート番号でヒント、後で確認）
        self._port_suggests_lmstudio = ":1234" in base_url
        self.is_lmstudio = None  # 実際の判定は遅延評価
    
    def _detect_server_type(self):
        """サーバータイプを検出（Ollama or LM Studio）"""
        if self.is_lmstudio is not None:
            return self.is_lmstudio
        
        # ポート番号からの初期推測を使用
        if self._port_suggests_lmstudio:
            # LM Studioの可能性が高い場合、OpenAI互換APIをチェック
            try:
                req = urllib.request.Request(f"{self.base_url}/v1/models")
                with urllib.request.urlopen(req, timeout=1) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    if 'data' in data:  # OpenAI互換レスポンス
                        self.is_lmstudio = True
                        logger.debug("Detected LM Studio server")
                        return True
            except:
                pass
        
        # Ollama APIをチェック
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=1) as response:
                data = json.loads(response.read().decode('utf-8'))
                if 'models' in data:  # Ollamaレスポンス
                    self.is_lmstudio = False
                    logger.debug("Detected Ollama server")
                    return False
        except:
            pass
        
        # デフォルトはポート番号からの推測を使用
        self.is_lmstudio = self._port_suggests_lmstudio
        return self.is_lmstudio
    
    def _build_prompt_from_messages(self, messages: list) -> str:
        """メッセージリストからOllama用のプロンプトを構築"""
        prompt_parts = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"\nUser: {content}")
            elif role == "assistant":
                prompt_parts.append(f"\nAssistant: {content}")
        
        # 最後にアシスタントの応答を促す
        prompt_parts.append("\nAssistant: ")
        
        return "\n".join(prompt_parts)
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Ollama/LM Studio APIを使用してテキスト生成"""
        if self._detect_server_type():
            # LM StudioはOpenAI互換API
            messages = kwargs.get("messages", [])
            if not messages:
                messages = [{"role": "user", "content": prompt}]
            
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 2048),
                "stream": False
            }
            
            try:
                req = urllib.request.Request(
                    f"{self.base_url}/v1/chat/completions",
                    data=json.dumps(data).encode('utf-8'),
                    headers=self.headers
                )
                
                with urllib.request.urlopen(req) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    return result['choices'][0]['message']['content']
                    
            except Exception as e:
                logger.error(f"LM Studio request failed: {e}")
                raise
        else:
            # Ollama API
            # messagesパラメータがある場合は会話履歴を含める
            messages = kwargs.get("messages", [])
            if messages:
                # システムメッセージとユーザーメッセージを含む完全なプロンプトを構築
                full_prompt = self._build_prompt_from_messages(messages)
            else:
                full_prompt = prompt
                
            data = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "num_predict": kwargs.get("max_tokens", 2048),
                }
            }
            
            try:
                req = urllib.request.Request(
                    f"{self.base_url}/api/generate",
                    data=json.dumps(data).encode('utf-8'),
                    headers=self.headers
                )
                
                with urllib.request.urlopen(req) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    return result['response']
                    
            except Exception as e:
                logger.error(f"Ollama request failed: {e}")
                raise
    
    def generate_stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """Ollama/LM Studio APIを使用してストリーミング生成"""
        if self._detect_server_type():
            # LM StudioはOpenAI互換API
            messages = kwargs.get("messages", [])
            if not messages:
                messages = [{"role": "user", "content": prompt}]
            
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 2048),
                "stream": True
            }
            
            try:
                req = urllib.request.Request(
                    f"{self.base_url}/v1/chat/completions",
                    data=json.dumps(data).encode('utf-8'),
                    headers=self.headers
                )
                
                with urllib.request.urlopen(req) as response:
                    for line in response:
                        line = line.decode('utf-8').strip()
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        yield delta['content']
                            except json.JSONDecodeError:
                                continue
                                
            except Exception as e:
                logger.error(f"LM Studio streaming failed: {e}")
                raise
        else:
            # Ollama API
            # messagesパラメータがある場合は会話履歴を含める
            messages = kwargs.get("messages", [])
            if messages:
                # システムメッセージとユーザーメッセージを含む完全なプロンプトを構築
                full_prompt = self._build_prompt_from_messages(messages)
            else:
                full_prompt = prompt
                
            data = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": True,
                "options": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "num_predict": kwargs.get("max_tokens", 2048),
                }
            }
            
            try:
                req = urllib.request.Request(
                    f"{self.base_url}/api/generate",
                    data=json.dumps(data).encode('utf-8'),
                    headers=self.headers
                )
                
                with urllib.request.urlopen(req) as response:
                    for line in response:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            if 'response' in data:
                                yield data['response']
                        except json.JSONDecodeError:
                            continue
                            
            except Exception as e:
                logger.error(f"Ollama streaming failed: {e}")
                raise
    
    @retry_network_operation
    def get_models(self) -> list[str]:
        """利用可能なモデルのリストを取得（リトライ付き）"""
        try:
            if self._detect_server_type():
                # LM StudioはOpenAI互換API
                req = urllib.request.Request(f"{self.base_url}/v1/models")
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    models = [m['id'] for m in data.get('data', [])]
                    return models
            else:
                # Ollama API
                req = urllib.request.Request(f"{self.base_url}/api/tags")
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    models = [m['name'] for m in data.get('models', [])]
                    return models
        except Exception as e:
            logger.error(f"Failed to fetch models: {e}")
            return []
    
    def get_model_info(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """モデルの詳細情報を取得（コンテキストサイズを含む）"""
        model = model_name or self.model
        
        try:
            if self._detect_server_type():
                # LM Studio: /api/v0/models エンドポイントを使用
                req = urllib.request.Request(f"{self.base_url}/api/v0/models")
                with urllib.request.urlopen(req, timeout=10) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    
                    # 指定されたモデルを検索
                    for model_data in result:
                        if model_data.get('id') == model or model_data.get('name') == model:
                            max_context_length = model_data.get('max_context_length')
                            return {
                                "context_size": max_context_length,
                                "model_data": model_data
                            }
                    
                    # モデルが見つからない場合
                    available_models = [m.get('id', m.get('name', 'unknown')) for m in result]
                    return {
                        "context_size": None,
                        "error": f"Model '{model}' not found in LM Studio models",
                        "available_models": available_models
                    }
            else:
                # Ollama: /api/show エンドポイントを使用
                data = {"name": model}
                req = urllib.request.Request(
                    f"{self.base_url}/api/show",
                    data=json.dumps(data).encode('utf-8'),
                    headers=self.headers
                )
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    
                    # モデル情報からコンテキストサイズを取得
                    model_info = result.get('model_info', {})
                    parameters = result.get('parameters', '')
                    template = result.get('template', '')
                    
                    # さまざまな場所からコンテキストサイズを探す
                    context_size = None
                    
                    # 1. model_info内のコンテキストサイズ
                    if isinstance(model_info, dict):
                        for key in ['context_length', 'max_position_embeddings', 'n_ctx']:
                            if key in model_info:
                                context_size = model_info[key]
                                break
                    
                    # 2. parametersからnum_ctxを探す
                    if context_size is None and parameters:
                        # parametersは文字列形式で "num_ctx 4096" のような形式
                        import re
                        match = re.search(r'num_ctx\s+(\d+)', parameters)
                        if match:
                            context_size = int(match.group(1))
                    
                    # 3. templateからコンテキストサイズのヒントを探す
                    if context_size is None and template:
                        # 一部のモデルではtemplateにヒントがある場合がある
                        if '128k' in template.lower() or '128000' in template:
                            context_size = 128000
                        elif '32k' in template.lower() or '32768' in template:
                            context_size = 32768
                        elif '8k' in template.lower() or '8192' in template:
                            context_size = 8192
                    
                    return {
                        "context_size": context_size,
                        "model_info": model_info,
                        "parameters": parameters,
                        "template": template
                    }
        except Exception as e:
            logger.error(f"Failed to get model info for {model}: {e}")
            return {"context_size": None, "error": str(e)}
    
    def test_connection(self) -> Dict[str, Any]:
        """接続テスト"""
        try:
            # モデルリストを取得してテスト
            models = self.get_models()
            
            if models:
                return {
                    "success": True,
                    "provider": "Ollama",
                    "base_url": self.base_url,
                    "available_models": models,
                    "current_model": self.model
                }
            else:
                return {
                    "success": False,
                    "provider": "Ollama",
                    "base_url": self.base_url,
                    "error": "No models found or connection failed"
                }
        except Exception as e:
            return {
                "success": False,
                "provider": "Ollama",
                "base_url": self.base_url,
                "error": str(e)
            }


class OpenRouterProvider(ExternalProvider):
    """OpenRouter APIプロバイダー"""
    
    def __init__(self, api_key: str, model: str = "meta-llama/llama-3.2-3b-instruct:free"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/thonny/thonny",
            "X-Title": "Thonny Local LLM Plugin"
        }
    
    def generate(self, prompt: str, **kwargs) -> str:
        """OpenRouter APIを使用してテキスト生成"""
        messages = kwargs.get("messages", [{"role": "user", "content": prompt}])
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
            "stream": False
        }
        
        try:
            req = urllib.request.Request(
                f"{self.base_url}/chat/completions",
                data=json.dumps(data).encode('utf-8'),
                headers=self.headers
            )
            
            # SSL証明書の検証を有効化
            context = ssl.create_default_context()
            
            with urllib.request.urlopen(req, context=context) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result['choices'][0]['message']['content']
                
        except Exception as e:
            logger.error(f"OpenRouter request failed: {e}")
            raise
    
    def generate_stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """OpenRouter APIを使用してストリーミング生成"""
        messages = kwargs.get("messages", [{"role": "user", "content": prompt}])
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
            "stream": True
        }
        
        try:
            req = urllib.request.Request(
                f"{self.base_url}/chat/completions",
                data=json.dumps(data).encode('utf-8'),
                headers=self.headers
            )
            
            context = ssl.create_default_context()
            
            with urllib.request.urlopen(req, context=context) as response:
                for line in response:
                    line = line.decode('utf-8').strip()
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    yield delta['content']
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"OpenRouter streaming failed: {e}")
            raise
    
    def get_model_info(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """モデルの詳細情報を取得（コンテキストサイズを含む）"""
        model = model_name or self.model
        
        try:
            # OpenRouter API /v1/models エンドポイントを使用
            req = urllib.request.Request(
                f"{self.base_url}/models",
                headers=self.headers
            )
            
            context = ssl.create_default_context()
            
            with urllib.request.urlopen(req, context=context, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                # 指定されたモデルを検索
                for model_data in result.get('data', []):
                    if model_data.get('id') == model:
                        context_length = model_data.get('context_length')
                        return {
                            "context_size": context_length,
                            "model_data": model_data
                        }
                
                # モデルが見つからない場合
                return {
                    "context_size": None,
                    "error": f"Model '{model}' not found in available models"
                }
                
        except Exception as e:
            logger.error(f"Failed to get model info for {model}: {e}")
            return {"context_size": None, "error": str(e)}
    
    def test_connection(self) -> Dict[str, Any]:
        """接続テスト"""
        try:
            response = self.generate("Say 'Hello!' in exactly one word.", max_tokens=10)
            return {
                "success": True,
                "provider": "OpenRouter",
                "model": self.model,
                "response": response
            }
        except Exception as e:
            return {
                "success": False,
                "provider": "OpenRouter",
                "model": self.model,
                "error": str(e)
            }