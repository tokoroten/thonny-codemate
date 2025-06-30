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

# OpenAI library support
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

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
        
        # OpenAI client (if available)
        self.openai_client = None
        if OPENAI_AVAILABLE:
            try:
                # OpenAI clientの初期化（base_urlがデフォルトでない場合も対応）
                if base_url and base_url != "https://api.openai.com/v1":
                    self.openai_client = OpenAI(api_key=api_key, base_url=base_url)
                else:
                    self.openai_client = OpenAI(api_key=api_key)
                logger.info("Using OpenAI official library")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.openai_client = None
    
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
        
        # OpenAI公式ライブラリを使用
        if not self.openai_client:
            raise Exception("OpenAI library is not available. Please install it with: pip install openai")
        
        try:
            stream = self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2048),
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"ChatGPT streaming failed: {e}")
            yield f"[Error: {str(e)}]"
    
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
    """Ollama/LM Studio APIプロバイダー（OpenAI互換）"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.headers = {"Content-Type": "application/json"}
        
        # OpenAI client - both Ollama and LM Studio support OpenAI compatible API
        self.openai_client = None
        if OPENAI_AVAILABLE:
            try:
                # Determine API base URL
                if base_url.endswith('/v1'):
                    api_base = base_url
                else:
                    api_base = f"{self.base_url}/v1"
                
                self.openai_client = OpenAI(
                    api_key="not-needed",  # Ollama/LM Studio don't require real API key
                    base_url=api_base
                )
                logger.info(f"Initialized OpenAI client for {base_url} with API base: {api_base}")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
    
    
    def generate(self, prompt: str, **kwargs) -> str:
        """テキスト生成（非ストリーミング）"""
        messages = kwargs.get("messages", [])
        if not messages:
            messages = [{"role": "user", "content": prompt}]
        
        if not self.openai_client:
            raise Exception("OpenAI library is not available. Please install it with: pip install openai")
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2048),
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Failed to generate: {e}")
            raise
    
    def generate_stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """ストリーミング生成"""
        messages = kwargs.get("messages", [])
        if not messages:
            messages = [{"role": "user", "content": prompt}]
        
        if not self.openai_client:
            raise Exception("OpenAI library is not available. Please install it with: pip install openai")
        
        try:
            stream = self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2048),
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield f"[Error: {str(e)}]"
    
    @retry_network_operation
    def get_models(self) -> list[str]:
        """利用可能なモデルのリストを取得"""
        try:
            if self.openai_client:
                models = self.openai_client.models.list()
                return [m.id for m in models.data]
            else:
                # Fallback: Try Ollama native API if OpenAI client not available
                req = urllib.request.Request(f"{self.base_url}/api/tags")
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    return [m['name'] for m in data.get('models', [])]
        except Exception as e:
            logger.error(f"Failed to fetch models: {e}")
            return []
    
    def get_model_info(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """モデルの詳細情報を取得"""
        model = model_name or self.model
        
        try:
            # Try OpenAI compatible endpoint first
            if self.openai_client:
                try:
                    models = self.openai_client.models.list()
                    for model_data in models.data:
                        if model_data.id == model:
                            # Extract context size from various possible fields
                            context_size = None
                            for attr in ['context_window', 'context_length', 'max_context_length']:
                                if hasattr(model_data, attr):
                                    context_size = getattr(model_data, attr)
                                    if context_size:
                                        break
                            
                            return {
                                "context_size": context_size,
                                "model_data": model_data.model_dump() if hasattr(model_data, 'model_dump') else model_data
                            }
                except Exception as e:
                    logger.debug(f"OpenAI API model info failed, trying native API: {e}")
            
            # Fallback: Ollama native API
            data = {"name": model}
            req = urllib.request.Request(
                f"{self.base_url}/api/show",
                data=json.dumps(data).encode('utf-8'),
                headers=self.headers
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                # Extract context size from parameters
                parameters = result.get('parameters', '')
                context_size = 2048  # default
                
                if parameters:
                    import re
                    match = re.search(r'num_ctx\s+(\d+)', parameters)
                    if match:
                        context_size = int(match.group(1))
                
                return {
                    "context_size": context_size,
                    "model_data": result
                }
                
        except Exception as e:
            logger.error(f"Failed to get model info for {model}: {e}")
            return {"context_size": None, "error": str(e)}
    
    def test_connection(self) -> Dict[str, Any]:
        """接続テスト"""
        try:
            # Get available models
            models = self.get_models()
            
            if not models:
                return {
                    "success": False,
                    "provider": "Ollama/LM Studio",
                    "base_url": self.base_url,
                    "error": "No models found"
                }
            
            # Try a simple completion
            test_model = self.model if self.model in models else models[0]
            
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=test_model,
                    messages=[{"role": "user", "content": "Say 'Hello' in one word."}],
                    max_tokens=10
                )
                response_text = response.choices[0].message.content
            else:
                response_text = self.generate("Say 'Hello' in one word.", max_tokens=10)
            
            return {
                "success": True,
                "provider": "Ollama/LM Studio",
                "base_url": self.base_url,
                "model": test_model,
                "available_models": models,
                "response": response_text
            }
        except Exception as e:
            return {
                "success": False,
                "provider": "Ollama/LM Studio",
                "base_url": self.base_url,
                "model": self.model,
                "error": str(e)
            }


class OpenRouterProvider(ExternalProvider):
    """OpenRouter APIプロバイダー"""
    
    def __init__(self, api_key: str, model: str = "meta-llama/llama-3.2-1b-instruct:free"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/thonny/thonny",
            "X-Title": "Thonny Local LLM Plugin"
        }
        
        # OpenRouter is OpenAI compatible
        self.openai_client = None
        if OPENAI_AVAILABLE:
            try:
                # カスタムヘッダーを設定
                from openai import DefaultHttpxClient
                import httpx
                
                client = DefaultHttpxClient(
                    headers={
                        "HTTP-Referer": "https://github.com/thonny/thonny",
                        "X-Title": "Thonny Local LLM Plugin"
                    }
                )
                
                self.openai_client = OpenAI(
                    api_key=api_key,
                    base_url=self.base_url,
                    http_client=client
                )
                logger.info("Using OpenAI library for OpenRouter")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client for OpenRouter: {e}")
    
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
        
        # OpenAIライブラリを使用
        if not self.openai_client:
            raise Exception("OpenAI library is not available. Please install it with: pip install openai")
        
        try:
            stream = self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2048),
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"OpenRouter streaming failed: {e}")
            yield f"[Error: {str(e)}]"
    
    def get_models(self, free_only: bool = True) -> list[str]:
        """利用可能なモデルのリストを取得
        
        Args:
            free_only: Trueの場合、無料モデルのみを返す
        """
        try:
            req = urllib.request.Request(
                f"{self.base_url}/models",
                headers={
                    "Content-Type": "application/json"
                }
            )
            
            context = ssl.create_default_context()
            
            with urllib.request.urlopen(req, context=context, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                models = []
                for model in data.get('data', []):
                    model_id = model.get('id', '')
                    
                    if free_only:
                        # 無料モデルをフィルタリング
                        pricing = model.get('pricing', {})
                        prompt_price = pricing.get('prompt', '')
                        
                        # :free サフィックスまたは価格が0のモデル
                        if ':free' in model_id or str(prompt_price) == '0':
                            models.append(model_id)
                    else:
                        models.append(model_id)
                
                return sorted(models)
                
        except Exception as e:
            logger.error(f"Failed to fetch OpenRouter models: {e}")
            # フォールバック: デフォルトの無料モデルリストを返す
            return [
                "meta-llama/llama-3.2-1b-instruct:free",
                "meta-llama/llama-3.1-8b-instruct:free",
                "google/gemini-2.0-flash-exp:free",
                "mistralai/mistral-7b-instruct:free",
                "qwen/qwen-2.5-72b-instruct:free"
            ]
    
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