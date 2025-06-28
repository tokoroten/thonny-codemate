"""
外部LLMプロバイダーのサポート
ChatGPT、Ollama API、OpenRouterに対応
"""
import os
import json
import logging
from typing import Optional, Iterator, Dict, Any
from abc import ABC, abstractmethod
import urllib.request
import urllib.error
import ssl

logger = logging.getLogger(__name__)


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
            raise Exception(f"ChatGPT API error: {error_body}")
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
                            
        except Exception as e:
            logger.error(f"ChatGPT streaming failed: {e}")
            raise
    
    def test_connection(self) -> Dict[str, Any]:
        """接続テスト"""
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
        
        # LM Studioかどうかを判定（ポート1234の場合）
        self.is_lmstudio = ":1234" in base_url
    
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
        if self.is_lmstudio:
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
        if self.is_lmstudio:
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
    
    def get_models(self) -> list[str]:
        """利用可能なモデルのリストを取得"""
        try:
            if self.is_lmstudio:
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