"""
外部プロバイダーのテスト
"""
import unittest
from unittest.mock import patch, MagicMock
import json

from thonnycontrib.thonny_codemate.external_providers import (
    ChatGPTProvider,
    OllamaProvider,
    OpenRouterProvider
)


class TestChatGPTProvider(unittest.TestCase):
    """ChatGPTプロバイダーのテスト"""
    
    def setUp(self):
        self.provider = ChatGPTProvider("test-api-key", "gpt-3.5-turbo")
    
    @patch('urllib.request.urlopen')
    def test_generate(self, mock_urlopen):
        """通常の生成をテスト"""
        # モックレスポンス
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{
                "message": {
                    "content": "Hello from ChatGPT!"
                }
            }]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = self.provider.generate("Say hello")
        self.assertEqual(result, "Hello from ChatGPT!")
    
    @patch('urllib.request.urlopen')
    def test_generate_stream(self, mock_urlopen):
        """ストリーミング生成をテスト"""
        # モックレスポンス
        mock_response = MagicMock()
        mock_response.__iter__.return_value = [
            b'data: {"choices":[{"delta":{"content":"Hello"}}]}\n',
            b'data: {"choices":[{"delta":{"content":" from"}}]}\n',
            b'data: {"choices":[{"delta":{"content":" ChatGPT!"}}]}\n',
            b'data: [DONE]\n'
        ]
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = list(self.provider.generate_stream("Say hello"))
        self.assertEqual(result, ["Hello", " from", " ChatGPT!"])
    
    @patch('urllib.request.urlopen')
    def test_connection_success(self, mock_urlopen):
        """接続テスト成功"""
        # モックレスポンス
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{
                "message": {
                    "content": "Hello!"
                }
            }]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = self.provider.test_connection()
        self.assertTrue(result["success"])
        self.assertEqual(result["provider"], "ChatGPT")
        self.assertEqual(result["response"], "Hello!")


class TestOllamaProvider(unittest.TestCase):
    """Ollamaプロバイダーのテスト"""
    
    def setUp(self):
        self.provider = OllamaProvider("http://localhost:11434", "llama3")
    
    @patch('urllib.request.urlopen')
    def test_generate(self, mock_urlopen):
        """通常の生成をテスト"""
        # モックレスポンス
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "response": "Hello from Ollama!"
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = self.provider.generate("Say hello")
        self.assertEqual(result, "Hello from Ollama!")
    
    @patch('urllib.request.urlopen')
    def test_generate_stream(self, mock_urlopen):
        """ストリーミング生成をテスト"""
        # モックレスポンス
        mock_response = MagicMock()
        mock_response.__iter__.return_value = [
            b'{"response":"Hello"}\n',
            b'{"response":" from"}\n',
            b'{"response":" Ollama!"}\n'
        ]
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = list(self.provider.generate_stream("Say hello"))
        self.assertEqual(result, ["Hello", " from", " Ollama!"])
    
    @patch('urllib.request.urlopen')
    def test_connection_success(self, mock_urlopen):
        """接続テスト成功"""
        # モックレスポンス
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "models": [
                {"name": "llama3"},
                {"name": "mistral"}
            ]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = self.provider.test_connection()
        self.assertTrue(result["success"])
        self.assertEqual(result["provider"], "Ollama")
        self.assertEqual(result["available_models"], ["llama3", "mistral"])


class TestOpenRouterProvider(unittest.TestCase):
    """OpenRouterプロバイダーのテスト"""
    
    def setUp(self):
        self.provider = OpenRouterProvider("test-api-key")
    
    @patch('urllib.request.urlopen')
    def test_generate(self, mock_urlopen):
        """通常の生成をテスト"""
        # モックレスポンス
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{
                "message": {
                    "content": "Hello from OpenRouter!"
                }
            }]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = self.provider.generate("Say hello")
        self.assertEqual(result, "Hello from OpenRouter!")
    
    def test_headers(self):
        """ヘッダーが正しく設定されているか確認"""
        self.assertIn("Authorization", self.provider.headers)
        self.assertIn("HTTP-Referer", self.provider.headers)
        self.assertIn("X-Title", self.provider.headers)


if __name__ == "__main__":
    unittest.main()