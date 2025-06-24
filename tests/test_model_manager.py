"""
モデルマネージャーのテスト
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil

from thonnycontrib.thonny_local_ollama.model_manager import ModelManager, DownloadProgress, RECOMMENDED_MODELS


class TestModelManager:
    """ModelManagerのテストクラス"""
    
    @pytest.fixture
    def temp_models_dir(self):
        """一時的なモデルディレクトリを作成"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_init(self, temp_models_dir):
        """初期化のテスト"""
        manager = ModelManager(temp_models_dir)
        assert manager.models_dir == temp_models_dir
        assert temp_models_dir.exists()
    
    def test_list_available_models_empty(self, temp_models_dir):
        """モデルがない場合のリストテスト"""
        manager = ModelManager(temp_models_dir)
        models = manager.list_available_models()
        
        # 推奨モデルの数だけ存在
        assert len(models) == len(RECOMMENDED_MODELS)
        
        # すべて未インストール
        for model in models:
            assert not model["installed"]
            assert not model["downloading"]
    
    def test_list_available_models_with_files(self, temp_models_dir):
        """モデルファイルがある場合のリストテスト"""
        # テスト用のGGUFファイルを作成
        test_file = temp_models_dir / "test_model.gguf"
        test_file.write_text("dummy content")
        
        # 推奨モデルのファイルも作成
        recommended_file = temp_models_dir / RECOMMENDED_MODELS["explanation"]["filename"]
        recommended_file.write_text("dummy content")
        
        manager = ModelManager(temp_models_dir)
        models = manager.list_available_models()
        
        # 推奨モデル + カスタムモデル
        assert len(models) == len(RECOMMENDED_MODELS) + 1
        
        # インストール状態を確認
        installed_count = sum(1 for m in models if m["installed"])
        assert installed_count == 2  # test_model.gguf + recommended_file
    
    def test_get_model_path_with_purpose(self, temp_models_dir):
        """用途指定でのモデルパス取得テスト"""
        manager = ModelManager(temp_models_dir)
        
        # モデルがない場合
        assert manager.get_model_path("explanation") is None
        
        # 説明用モデルを作成
        explanation_file = temp_models_dir / RECOMMENDED_MODELS["explanation"]["filename"]
        explanation_file.write_text("dummy")
        
        # パスが取得できることを確認
        path = manager.get_model_path("explanation")
        assert path == str(explanation_file)
    
    def test_get_model_path_fallback(self, temp_models_dir):
        """フォールバック動作のテスト"""
        manager = ModelManager(temp_models_dir)
        
        # 任意のGGUFファイルを作成
        any_model = temp_models_dir / "any_model.gguf"
        any_model.write_text("dummy")
        
        # 存在しない用途でもファイルが返される
        path = manager.get_model_path("nonexistent")
        assert path == str(any_model)
    
    @patch('thonnycontrib.thonny_local_ollama.model_manager.hf_hub_download')
    def test_download_model_success(self, mock_download, temp_models_dir):
        """モデルダウンロード成功のテスト"""
        manager = ModelManager(temp_models_dir)
        
        # ダウンロード結果をモック
        expected_path = temp_models_dir / "model.gguf"
        mock_download.return_value = str(expected_path)
        
        # プログレスコールバックを記録
        progress_updates = []
        def progress_callback(progress):
            progress_updates.append(progress)
        
        # ダウンロード実行
        manager._download_model_thread("explanation", RECOMMENDED_MODELS["explanation"], progress_callback)
        
        # ダウンロードが呼ばれたことを確認
        mock_download.assert_called_once()
        
        # 完了通知があることを確認
        assert any(p.status == "completed" for p in progress_updates)
    
    def test_download_model_invalid_key(self, temp_models_dir):
        """無効なモデルキーでのダウンロードテスト"""
        manager = ModelManager(temp_models_dir)
        
        with pytest.raises(ValueError):
            manager.download_model("invalid_key")
    
    def test_delete_model_success(self, temp_models_dir):
        """モデル削除成功のテスト"""
        manager = ModelManager(temp_models_dir)
        
        # テストファイルを作成
        test_file = temp_models_dir / "test.gguf"
        test_file.write_text("dummy")
        
        # 削除実行
        result = manager.delete_model(str(test_file))
        
        assert result is True
        assert not test_file.exists()
    
    def test_delete_model_not_found(self, temp_models_dir):
        """存在しないモデルの削除テスト"""
        manager = ModelManager(temp_models_dir)
        
        result = manager.delete_model(str(temp_models_dir / "nonexistent.gguf"))
        
        assert result is False
    
    def test_delete_model_outside_directory(self, temp_models_dir):
        """ディレクトリ外のファイル削除を防ぐテスト"""
        manager = ModelManager(temp_models_dir)
        
        # 別の場所にファイルを作成
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            temp_file = Path(tf.name)
        
        try:
            # 削除を試みる
            result = manager.delete_model(str(temp_file))
            assert result is False
            assert temp_file.exists()  # ファイルは削除されていない
        finally:
            temp_file.unlink()


class TestDownloadProgress:
    """DownloadProgressのテスト"""
    
    def test_creation(self):
        """DownloadProgress作成のテスト"""
        progress = DownloadProgress(
            model_name="test_model",
            downloaded=50,
            total=100,
            status="downloading"
        )
        
        assert progress.model_name == "test_model"
        assert progress.downloaded == 50
        assert progress.total == 100
        assert progress.status == "downloading"
        assert progress.error_message is None
    
    def test_with_error(self):
        """エラー付きDownloadProgressのテスト"""
        progress = DownloadProgress(
            model_name="test_model",
            downloaded=0,
            total=0,
            status="error",
            error_message="Network error"
        )
        
        assert progress.status == "error"
        assert progress.error_message == "Network error"