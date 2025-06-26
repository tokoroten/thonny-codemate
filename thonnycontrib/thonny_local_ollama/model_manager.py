"""
モデル管理モジュール
推奨モデルのダウンロードと管理機能を提供
"""
import os

# huggingface_hubのロギングを環境変数で無効化
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"

import threading
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass

# ロギングを無効化（Thonny環境での問題を回避）
import logging
logging.disable(logging.CRITICAL)

# huggingface_hubのロギングも無効化
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub.file_download").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("requests").setLevel(logging.ERROR)

# すべてのロガーにNullHandlerを設定
for logger_name in ["huggingface_hub", "huggingface_hub.file_download", "urllib3", "requests"]:
    logger = logging.getLogger(logger_name)
    logger.handlers = []
    logger.addHandler(logging.NullHandler())

# 推奨モデルの定義
RECOMMENDED_MODELS = {
    # Llama 3.2シリーズ（Meta公式の最新モデル）
    "llama3.2-1b": {
        "name": "Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        "repo_id": "bartowski/Llama-3.2-1B-Instruct-GGUF",
        "filename": "Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        "size": "0.8GB",
        "description": "Llama 3.2 1B - 最新の軽量モデル。高速で効率的。",
        "languages": ["en", "multi"]
    },
    "llama3.2-3b": {
        "name": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "repo_id": "bartowski/Llama-3.2-3B-Instruct-GGUF",
        "filename": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "size": "2.0GB",
        "description": "Llama 3.2 3B - バランスの良いモデル。品質と速度の両立。",
        "languages": ["en", "multi"]
    },
    "llama3.1-8b": {
        "name": "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        "repo_id": "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
        "filename": "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        "size": "4.9GB",
        "description": "Llama 3.1 8B - 高性能モデル。GPT-3.5相当の能力。",
        "languages": ["en", "multi"]
    },
    "llama3-13b": {
        "name": "Meta-Llama-3-13B-Instruct-Q4_K_M.gguf",
        "repo_id": "QuantFactory/Meta-Llama-3-13B-Instruct-GGUF",
        "filename": "Meta-Llama-3-13B-Instruct.Q4_K_M.gguf",
        "size": "7.9GB",
        "description": "Llama 3 13B - 大規模モデル。高度な推論能力。",
        "languages": ["en", "multi"]
    },
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
                "languages": model_info.get("languages", ["en"]),
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
                    "path": str(gguf_file),
                    "installed": True,
                    "downloading": False
                })
        
        return models
    
    def get_model_path(self, model_key: str = "llama3.2-1b") -> Optional[str]:
        """
        指定されたモデルのパスを取得
        
        Args:
            model_key: モデルのキー（"llama3.2-1b"など）
            
        Returns:
            モデルファイルのパス（存在する場合）
        """
        if model_key in RECOMMENDED_MODELS:
            model_info = RECOMMENDED_MODELS[model_key]
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
            # すでにダウンロード中
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
                # インポート前に追加のロギング無効化
                import sys
                if hasattr(sys.stderr, 'write') and sys.stderr is None:
                    # sys.stderrがNoneの場合、ダミーのファイルオブジェクトを設定
                    import io
                    sys.stderr = io.StringIO()
                
                from huggingface_hub import hf_hub_download
            except ImportError:
                error_msg = "huggingface_hub is not installed. Please run: pip install huggingface-hub"
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
            
            # ダウンロード開始通知
            if progress_callback:
                progress = DownloadProgress(
                    model_name=model_info["name"],
                    downloaded=0,
                    total=0,
                    status="downloading"
                )
                progress_callback(progress)
            
            # ダウンロード実行
            try:
                # ロギング出力を一時的にキャプチャ
                import io
                import sys
                old_stderr = sys.stderr
                sys.stderr = io.StringIO()
                
                try:
                    # 単一ファイルのダウンロード
                    downloaded_path = hf_hub_download(
                        repo_id=model_info["repo_id"],
                        filename=model_info["filename"],
                        local_dir=str(self.models_dir),
                        force_download=False,  # 既存ファイルがあればスキップ
                        resume_download=True,  # 中断されたダウンロードを再開
                        local_dir_use_symlinks=False  # シンボリックリンクを使わない
                    )
                finally:
                    # stderrを復元
                    sys.stderr = old_stderr
                    
            except AttributeError as e:
                if "'NoneType' object has no attribute 'write'" in str(e):
                    raise Exception("Logging error in huggingface_hub. This is a known issue in Thonny environment. Please try downloading the model manually.")
                else:
                    raise
            
            # ダウンロード完了
            
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
            # エラー発生
            import traceback
            error_detail = f"{str(e)}\n\nDetails:\n{traceback.format_exc()}"
            if progress_callback:
                progress = DownloadProgress(
                    model_name=model_info["name"],
                    downloaded=0,
                    total=0,
                    status="error",
                    error_message=error_detail
                )
                progress_callback(progress)
        finally:
            self._downloading.pop(model_key, None)
    
    def cancel_download(self, model_key: str):
        """ダウンロードをキャンセル（現在は未実装）"""
        # TODO: ダウンロードのキャンセル機能を実装
        pass
    
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
                # モデルを削除
                return True
            else:
                # ファイルが見つからないか無効なパス
                return False
        except Exception as e:
            # 削除に失敗
            return False