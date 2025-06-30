"""
外部プロバイダーのテスト
"""
import unittest
from unittest.mock import patch, MagicMock
import json

from thonnycontrib.thonny_codemate.external_providers import OllamaProvider



class TestOllamaProvider(unittest.TestCase):
    """Ollamaプロバイダーのテスト"""
    
    def setUp(self):
        # OpenAIがない場合でもテストできるようにモック
        with patch('thonnycontrib.thonny_codemate.external_providers.OPENAI_AVAILABLE', True):
            with patch('thonnycontrib.thonny_codemate.external_providers.OpenAI') as mock_openai_class:
                mock_client = MagicMock()
                mock_openai_class.return_value = mock_client
                self.provider = OllamaProvider("http://localhost:11434", "llama3")
    
    def test_generate(self):
        """通常の生成をテスト"""
        # OpenAI clientをモック
        if self.provider.openai_client:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Hello from Ollama!"
            
            with patch.object(self.provider.openai_client.chat.completions, 'create', return_value=mock_response):
                result = self.provider.generate("Say hello")
                self.assertEqual(result, "Hello from Ollama!")
        else:
            self.skipTest("OpenAI client not available")
    
    def test_generate_stream(self):
        """ストリーミング生成をテスト"""
        # OpenAI clientをモック
        if self.provider.openai_client:
            # ストリーミングレスポンスをモック
            mock_chunks = [
                MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
                MagicMock(choices=[MagicMock(delta=MagicMock(content=" from"))]),
                MagicMock(choices=[MagicMock(delta=MagicMock(content=" Ollama!"))])
            ]
            
            with patch.object(self.provider.openai_client.chat.completions, 'create', return_value=iter(mock_chunks)):
                result = list(self.provider.generate_stream("Say hello"))
                self.assertEqual(result, ["Hello", " from", " Ollama!"])
        else:
            self.skipTest("OpenAI client not available")
    
    def test_connection_success(self):
        """接続テスト成功"""
        # OpenAI clientをモック
        if self.provider.openai_client:
            # モデルリストをモック
            mock_models = MagicMock()
            mock_models.data = [
                MagicMock(id="llama3"),
                MagicMock(id="mistral")
            ]
            
            # チャット完了レスポンスをモック
            mock_chat_response = MagicMock()
            mock_chat_response.choices = [MagicMock()]
            mock_chat_response.choices[0].message.content = "Hello"
            
            with patch.object(self.provider.openai_client.models, 'list', return_value=mock_models):
                with patch.object(self.provider.openai_client.chat.completions, 'create', return_value=mock_chat_response):
                    result = self.provider.test_connection()
                    self.assertTrue(result["success"])
                    self.assertEqual(result["provider"], "Ollama/LM Studio")
                    self.assertEqual(result["available_models"], ["llama3", "mistral"])
        else:
            # OpenAI clientが使えない場合はfallbackのテスト
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = json.dumps({
                    "models": [
                        {"name": "llama3"},
                        {"name": "mistral"}
                    ]
                }).encode('utf-8')
                mock_urlopen.return_value.__enter__.return_value = mock_response
                
                result = self.provider.test_connection()
                self.assertIsNotNone(result)



if __name__ == "__main__":
    unittest.main()