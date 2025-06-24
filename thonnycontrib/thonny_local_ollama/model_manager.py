"""
モデル管理モジュール
推奨モデルのダウンロードと管理機能を提供
"""
import os
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# 推奨モデルの定義
RECOMMENDED_MODELS = {
    "explanation": {
        "name": "Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        "repo_id": "bartowski/Llama-3.2-1B-Instruct-GGUF",
        "filename": "Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        "size": "0.8GB",
        "description": "軽量で高速な解説用モデル。初心者向けの分かりやすい説明が得意。",
        "purpose": "explanation"
    },
    "coding": {
        "name": "DeepSeek-Coder-1.3B-Instruct-Q4_K_M.gguf", 
        "repo_id": "bartowski/DeepSeek-Coder-1.3B-Instruct-GGUF",
        "filename": "DeepSeek-Coder-1.3B-Instruct-Q4_K_M.gguf",
        "size": "0.9GB",
        "description": "コード生成に特化したモデル。高品質なPythonコードを生成。",
        "purpose": "coding"
    }
}

@dataclass
class DownloadProgress:
    """ダウンロード進捗情報"""
    model_name: str
    downloaded: int
    total: int
    status: str  # "downloading", "completed", "error"
    error_message: Optional[str] = None


class ModelManager:
    """モデルのダウンロードと管理を行うクラス"""
    
    def __init__(self, models_dir: Optional[Path] = None):
        if models_dir is None:
            # デフォルトはプロジェクトのmodelsディレクトリ
            self.models_dir = Path(__file__).parent.parent.parent / "models"
        else:
            self.models_dir = Path(models_dir)
        
        # モデルディレクトリを作成
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # ダウンロード状態
        self._downloading = {}
        self._download_callbacks = {}
    
    def get_models_dir(self) -> Path:
        """モデルディレクトリのパスを取得"""
        return self.models_dir
    
    def list_available_models(self) -> List[Dict]:
        """利用可能なモデルのリストを取得"""
        models = []
        
        # 推奨モデルの情報を追加
        for key, model_info in RECOMMENDED_MODELS.items():
            model_path = self.models_dir / model_info["filename"]
            model_data = {
                "key": key,
                "name": model_info["name"],
                "description": model_info["description"],
                "size": model_info["size"],
                "purpose": model_info["purpose"],
                "path": str(model_path),
                "installed": model_path.exists(),
                "downloading": key in self._downloading
            }
            models.append(model_data)
        
        # カスタムモデル（ディレクトリ内の他のGGUFファイル）も追加
        for gguf_file in self.models_dir.glob("*.gguf"):
            # 推奨モデルでない場合
            if not any(gguf_file.name == m["filename"] for m in RECOMMENDED_MODELS.values()):
                models.append({
                    "key": f"custom_{gguf_file.stem}",
                    "name": gguf_file.name,
                    "description": "Custom model",
                    "size": f"{gguf_file.stat().st_size / 1024 / 1024 / 1024:.1f}GB",
                    "purpose": "general",
                    "path": str(gguf_file),
                    "installed": True,
                    "downloading": False
                })
        
        return models
    
    def get_model_path(self, purpose: str = "explanation") -> Optional[str]:
        """
        指定された用途に適したモデルのパスを取得
        
        Args:
            purpose: "explanation" または "coding"
            
        Returns:
            モデルファイルのパス（存在する場合）
        """
        if purpose in RECOMMENDED_MODELS:
            model_info = RECOMMENDED_MODELS[purpose]
            model_path = self.models_dir / model_info["filename"]
            if model_path.exists():
                return str(model_path)
        
        # フォールバック：任意のGGUFファイルを返す
        for gguf_file in self.models_dir.glob("*.gguf"):
            return str(gguf_file)
        
        return None
    
    def download_model(self, model_key: str, progress_callback: Optional[Callable[[DownloadProgress], None]] = None):
        """
        モデルをダウンロード
        
        Args:
            model_key: RECOMMENDED_MODELSのキー
            progress_callback: 進捗コールバック関数
        """
        if model_key not in RECOMMENDED_MODELS:
            raise ValueError(f"Unknown model key: {model_key}")
        
        if model_key in self._downloading:
            logger.warning(f"Model {model_key} is already being downloaded")
            return
        
        model_info = RECOMMENDED_MODELS[model_key]
        
        # バックグラウンドでダウンロード
        thread = threading.Thread(
            target=self._download_model_thread,
            args=(model_key, model_info, progress_callback),
            daemon=True
        )
        thread.start()
    
    def _download_model_thread(self, model_key: str, model_info: Dict, progress_callback: Optional[Callable]):
        """モデルをダウンロードするスレッド関数"""
        self._downloading[model_key] = True
        
        try:
            # huggingface_hubをインポート
            try:
                from huggingface_hub import hf_hub_download
            except ImportError:
                error_msg = "huggingface_hub is not installed. Please run: uv pip install huggingface-hub"
                logger.error(error_msg)
                if progress_callback:
                    progress = DownloadProgress(
                        model_name=model_info["name"],
                        downloaded=0,
                        total=0,
                        status="error",
                        error_message=error_msg
                    )
                    progress_callback(progress)
                return
            
            # 進捗報告用のコールバック
            def hf_progress_callback(progress_dict):
                if progress_callback and "downloaded" in progress_dict:
                    progress = DownloadProgress(
                        model_name=model_info["name"],
                        downloaded=progress_dict.get("downloaded", 0),
                        total=progress_dict.get("total", 0),
                        status="downloading"
                    )
                    progress_callback(progress)
            
            logger.info(f"Downloading model: {model_info['name']}")
            
            # ダウンロード実行
            downloaded_path = hf_hub_download(
                repo_id=model_info["repo_id"],
                filename=model_info["filename"],
                local_dir=str(self.models_dir)
            )
            
            logger.info(f"Model downloaded successfully: {downloaded_path}")
            
            # 完了通知
            if progress_callback:
                progress = DownloadProgress(
                    model_name=model_info["name"],
                    downloaded=100,
                    total=100,
                    status="completed"
                )
                progress_callback(progress)
                
        except Exception as e:
            logger.error(f"Failed to download model {model_key}: {e}")
            if progress_callback:
                progress = DownloadProgress(
                    model_name=model_info["name"],
                    downloaded=0,
                    total=0,
                    status="error",
                    error_message=str(e)
                )
                progress_callback(progress)
        finally:
            self._downloading.pop(model_key, None)
    
    def cancel_download(self, model_key: str):
        """ダウンロードをキャンセル（現在は未実装）"""
        # TODO: ダウンロードのキャンセル機能を実装
        logger.warning("Download cancellation is not implemented yet")
    
    def delete_model(self, model_path: str) -> bool:
        """
        モデルを削除
        
        Args:
            model_path: モデルファイルのパス
            
        Returns:
            削除に成功したらTrue
        """
        try:
            path = Path(model_path)
            if path.exists() and path.parent == self.models_dir:
                path.unlink()
                logger.info(f"Model deleted: {model_path}")
                return True
            else:
                logger.warning(f"Model file not found or invalid path: {model_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete model: {e}")
            return False