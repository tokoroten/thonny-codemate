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
    "llama3-elyza-jp-8b": {
        "name": "Llama-3-ELYZA-JP-8B-q4_k_m.gguf",
        "repo_id": "elyza/Llama-3-ELYZA-JP-8B-GGUF",
        "filename": "Llama-3-ELYZA-JP-8B-q4_k_m.gguf",
        "size": "4.9GB",
        "description": "Llama 3 ELYZA JP 8B - 日本語に特化した高性能モデル。",
        "languages": ["ja", "en"]
    },
    "qwen2.5-coder-14b": {
        "name": "Qwen2.5-Coder-14B-Instruct-Q4_K_M.gguf",
        "repo_id": "bartowski/Qwen2.5-Coder-14B-Instruct-GGUF",
        "filename": "Qwen2.5-Coder-14B-Instruct-Q4_K_M.gguf",
        "size": "8.8GB",
        "description": "Qwen2.5 Coder 14B - プログラミングに特化した最新の高性能モデル。",
        "languages": ["en", "zh", "multi", "code"]
    },
    # Gemma 3nモデルは現在llama-cpp-pythonが対応していないためコメントアウト
    # llama-cpp-pythonが最新のllama.cppに追従したら有効化する
    # "gemma-3n-e4b": {
    #     "name": "gemma-3n-E4B-it-Q4_K_M.gguf",
    #     "repo_id": "tripolskypetr/gemma-3n-e4b-it",
    #     "filename": "gemma-3n-E4B-it-Q4_K_M.gguf",
    #     "size": "4.2GB",
    #     "description": "Gemma 3n E4B - Google DeepMindの最新軽量モデル。マルチモーダル対応。",
    #     "languages": ["en", "multi"]
    # },
    # "gemma-3n-e2b": {
    #     "name": "gemma-3n-E2B-it-Q4_K_M.gguf",
    #     "repo_id": "tripolskypetr/gemma-3n-e2b-it",
    #     "filename": "gemma-3n-E2B-it-Q4_K_M.gguf",
    #     "size": "2.8GB",
    #     "description": "Gemma 3n E2B - 小規模版の軽量モデル。低リソース環境に最適。",
    #     "languages": ["en", "multi"]
    # },
}

@dataclass
class DownloadProgress:
    """ダウンロード進捗情報"""
    model_name: str
    downloaded: int
    total: int
    status: str  # "downloading", "completed", "error"
    error_message: Optional[str] = None
    speed: float = 0.0  # bytes per second
    eta: int = 0  # estimated time remaining in seconds
    
    @property
    def percentage(self) -> float:
        """ダウンロード進捗率を取得"""
        if self.total > 0:
            return (self.downloaded / self.total) * 100
        return 0.0
        
    @property
    def speed_str(self) -> str:
        """人間が読みやすい速度表示を取得"""
        if self.speed < 1024:
            return f"{self.speed:.0f} B/s"
        elif self.speed < 1024 * 1024:
            return f"{self.speed / 1024:.1f} KB/s"
        else:
            return f"{self.speed / (1024 * 1024):.1f} MB/s"
    
    @property
    def eta_str(self) -> str:
        """人間が読みやすい残り時間表示を取得"""
        if self.eta <= 0:
            return "Calculating..."
        elif self.eta < 60:
            return f"{self.eta}s"
        elif self.eta < 3600:
            return f"{self.eta // 60}m {self.eta % 60}s"
        else:
            hours = self.eta // 3600
            minutes = (self.eta % 3600) // 60
            return f"{hours}h {minutes}m"
    
    @property
    def size_str(self) -> str:
        """人間が読みやすいサイズ表示を取得"""
        def format_size(size):
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            elif size < 1024 * 1024 * 1024:
                return f"{size / (1024 * 1024):.1f} MB"
            else:
                return f"{size / (1024 * 1024 * 1024):.2f} GB"
        
        if self.total > 0:
            return f"{format_size(self.downloaded)} / {format_size(self.total)}"
        else:
            return format_size(self.downloaded)


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
                from huggingface_hub.utils import tqdm as hf_tqdm
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
            
            # 進捗追跡用の変数
            import time
            last_update_time = time.time()
            last_downloaded = 0
            
            # カスタム進捗コールバック
            def custom_progress_callback(progress_dict):
                nonlocal last_update_time, last_downloaded
                
                if progress_callback and progress_dict:
                    current_time = time.time()
                    time_diff = current_time - last_update_time
                    
                    # 0.5秒ごとに更新（頻繁すぎる更新を防ぐ）
                    if time_diff >= 0.5:
                        downloaded = progress_dict.get("downloaded", 0)
                        total = progress_dict.get("total", 0)
                        
                        # 速度計算
                        if time_diff > 0:
                            bytes_diff = downloaded - last_downloaded
                            speed = bytes_diff / time_diff
                        else:
                            speed = 0
                        
                        # 残り時間計算
                        if speed > 0 and total > downloaded:
                            eta = int((total - downloaded) / speed)
                        else:
                            eta = 0
                        
                        progress = DownloadProgress(
                            model_name=model_info["name"],
                            downloaded=downloaded,
                            total=total,
                            status="downloading",
                            speed=speed,
                            eta=eta
                        )
                        progress_callback(progress)
                        
                        last_update_time = current_time
                        last_downloaded = downloaded
            
            # ダウンロード実行
            try:
                # まずファイルが既に存在するかチェック
                target_path = self.models_dir / model_info["filename"]
                if target_path.exists():
                    # 既に存在する場合は完了を通知
                    if progress_callback:
                        progress = DownloadProgress(
                            model_name=model_info["name"],
                            downloaded=100,
                            total=100,
                            status="completed"
                        )
                        progress_callback(progress)
                    return
                
                # ロギング出力を一時的にキャプチャ
                import io
                import sys
                old_stderr = sys.stderr
                sys.stderr = io.StringIO()
                
                try:
                    # URLベースのダウンロードを実装
                    import urllib.request
                    import tempfile
                    import shutil
                    
                    # Hugging Face URLを構築
                    base_url = f"https://huggingface.co/{model_info['repo_id']}/resolve/main/{model_info['filename']}"
                    
                    # 一時ファイルにダウンロード
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".gguf") as temp_file:
                        temp_path = temp_file.name
                    
                    def download_with_progress(url, dest_path):
                        """進捗表示付きダウンロード"""
                        nonlocal last_update_time, last_downloaded
                        
                        response = urllib.request.urlopen(url)
                        total_size = int(response.headers.get('Content-Length', 0))
                        
                        # 初期進捗を送信
                        if progress_callback and total_size > 0:
                            progress = DownloadProgress(
                                model_name=model_info["name"],
                                downloaded=0,
                                total=total_size,
                                status="downloading"
                            )
                            progress_callback(progress)
                        
                        block_size = 8192  # 8KB
                        downloaded = 0
                        last_update_time = time.time()
                        last_downloaded = 0
                        
                        with open(dest_path, 'wb') as f:
                            while True:
                                buffer = response.read(block_size)
                                if not buffer:
                                    break
                                
                                f.write(buffer)
                                downloaded += len(buffer)
                                
                                # 進捗を計算して送信
                                current_time = time.time()
                                time_diff = current_time - last_update_time
                                
                                if time_diff >= 0.5 and progress_callback:
                                    speed = (downloaded - last_downloaded) / time_diff if time_diff > 0 else 0
                                    eta = int((total_size - downloaded) / speed) if speed > 0 else 0
                                    
                                    progress = DownloadProgress(
                                        model_name=model_info["name"],
                                        downloaded=downloaded,
                                        total=total_size,
                                        status="downloading",
                                        speed=speed,
                                        eta=eta
                                    )
                                    progress_callback(progress)
                                    
                                    last_update_time = current_time
                                    last_downloaded = downloaded
                    
                    try:
                        # ダウンロード実行
                        download_with_progress(base_url, temp_path)
                        
                        # 成功したら正式な場所に移動
                        shutil.move(temp_path, str(target_path))
                        
                    except urllib.error.HTTPError:
                        # Hugging Face APIが使えない場合は従来の方法にフォールバック
                        if Path(temp_path).exists():
                            Path(temp_path).unlink()
                        
                        # hf_hub_downloadを使用
                        downloaded_path = hf_hub_download(
                            repo_id=model_info["repo_id"],
                            filename=model_info["filename"],
                            local_dir=str(self.models_dir),
                            force_download=False,
                            resume_download=True,
                            local_dir_use_symlinks=False
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