"""
LLMクライアントのテスト
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from thonnycontrib.thonny_codemate.llm_client import LLMClient, ModelConfig


class TestLLMClient:
    """LLMClientのテストクラス"""
    
    def test_init(self):
        """初期化のテスト"""
        client = LLMClient()
        assert client._model is None
        assert not client.is_loaded
        assert not client.is_loading
    
    def test_get_config_default(self):
        """デフォルト設定の取得テスト"""
        with patch('thonnycontrib.thonny_codemate.llm_client.get_workbench') as mock_wb:
            mock_wb.return_value.get_option.side_effect = lambda key, default: default
            
            client = LLMClient()
            config = client.get_config()
            
            assert config.model_path == ""
            assert config.n_ctx == 4096
            assert config.temperature == 0.7
            assert config.max_tokens == 2048
    
    def test_set_config(self):
        """設定の更新テスト"""
        client = LLMClient()
        new_config = ModelConfig(
            model_path="/path/to/model.gguf",
            n_ctx=8192,
            temperature=0.5
        )
        
        client.set_config(new_config)
        assert client._config == new_config
    
    @patch('thonnycontrib.thonny_codemate.llm_client.Llama')
    def test_load_model_success(self, mock_llama):
        """モデル読み込み成功のテスト"""
        # モックの設定
        mock_model = Mock()
        mock_llama.return_value = mock_model
        
        client = LLMClient()
        config = ModelConfig(model_path="test_model.gguf")
        client.set_config(config)
        
        # ファイル存在チェックをモック
        with patch('pathlib.Path.exists', return_value=True):
            result = client.load_model()
        
        assert result is True
        assert client.is_loaded
        assert client._model == mock_model
        mock_llama.assert_called_once()
    
    def test_load_model_file_not_found(self):
        """モデルファイルが見つからない場合のテスト"""
        client = LLMClient()
        config = ModelConfig(model_path="nonexistent.gguf")
        client.set_config(config)
        
        with patch('pathlib.Path.exists', return_value=False):
            result = client.load_model()
        
        assert result is False
        assert not client.is_loaded
        assert client._load_error is not None
    
    @patch('thonnycontrib.thonny_codemate.llm_client.Llama')
    def test_generate(self, mock_llama):
        """テキスト生成のテスト"""
        # モックの設定
        mock_model = Mock()
        mock_model.return_value = {
            "choices": [{"text": "Generated response"}]
        }
        mock_llama.return_value = mock_model
        
        client = LLMClient()
        config = ModelConfig(model_path="test_model.gguf")
        client.set_config(config)
        
        with patch('pathlib.Path.exists', return_value=True):
            client.load_model()
            response = client.generate("Test prompt")
        
        assert response == "Generated response"
        mock_model.assert_called_once()
    
    def test_explain_code(self):
        """コード説明機能のテスト"""
        client = LLMClient()
        
        # generateメソッドをモック
        with patch.object(client, 'generate', return_value="Code explanation") as mock_generate:
            result = client.explain_code("print('hello')", skill_level="beginner")
        
        assert result == "Code explanation"
        mock_generate.assert_called_once()
        # プロンプトに適切なキーワードが含まれているかチェック
        call_args = mock_generate.call_args[0][0]
        assert "beginner" in call_args
        assert "print('hello')" in call_args
    
    def test_fix_error(self):
        """エラー修正機能のテスト"""
        client = LLMClient()
        
        with patch.object(client, 'generate', return_value="Fixed code") as mock_generate:
            result = client.fix_error("bad code", "SyntaxError: invalid syntax")
        
        assert result == "Fixed code"
        mock_generate.assert_called_once()
        # プロンプトにコードとエラーが含まれているかチェック
        call_args = mock_generate.call_args[0][0]
        assert "bad code" in call_args
        assert "SyntaxError" in call_args


class TestModelConfig:
    """ModelConfigのテスト"""
    
    def test_default_values(self):
        """デフォルト値のテスト"""
        config = ModelConfig(model_path="/path/to/model.gguf")
        
        assert config.model_path == "/path/to/model.gguf"
        assert config.n_ctx == 4096
        assert config.n_gpu_layers == 0
        assert config.temperature == 0.7
        assert config.max_tokens == 2048
        assert config.top_p == 0.95
        assert config.top_k == 40
        assert config.repeat_penalty == 1.1
        assert config.n_threads is None
    
    def test_custom_values(self):
        """カスタム値のテスト"""
        config = ModelConfig(
            model_path="/path/to/model.gguf",
            n_ctx=8192,
            temperature=0.5,
            n_gpu_layers=20
        )
        
        assert config.n_ctx == 8192
        assert config.temperature == 0.5
        assert config.n_gpu_layers == 20