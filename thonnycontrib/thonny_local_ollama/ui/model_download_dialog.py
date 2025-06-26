"""
モデルダウンロードダイアログ
推奨モデルのダウンロードと管理UI
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Dict, List

from ..model_manager import ModelManager, DownloadProgress


class ModelDownloadDialog(tk.Toplevel):
    """モデルダウンロード管理ダイアログ"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("Model Manager")
        self.geometry("800x600")
        
        self.model_manager = ModelManager()
        self.model_widgets = {}
        self._download_progress = {}  # ダウンロード進捗を追跡
        
        self._init_ui()
        self._refresh_model_list()
    
    def _init_ui(self):
        """UIを初期化"""
        # メインフレーム
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # ヘッダー
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        ttk.Label(header_frame, text="Recommended Models", font=("", 12, "bold")).pack(side=tk.LEFT)
        
        ttk.Button(
            header_frame,
            text="Refresh",
            command=self._refresh_model_list,
            width=12
        ).pack(side=tk.RIGHT, padx=5)
        
        # モデルリストフレーム（スクロール可能）
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # スクロールバー付きキャンバス
        canvas = tk.Canvas(list_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # マウスホイールのバインディング
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _on_enter(event):
            # Windows
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            # Linux/macOS
            canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
            canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        
        def _on_leave(event):
            # バインディングを解除
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
        
        # キャンバスにマウスが入った時/出た時のイベント
        canvas.bind("<Enter>", _on_enter)
        canvas.bind("<Leave>", _on_leave)
        
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
    
    def _refresh_model_list(self):
        """モデルリストを更新"""
        # 既存のウィジェットをクリア
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.model_widgets.clear()
        
        # モデルリストを取得
        models = self.model_manager.list_available_models()
        
        # 各モデルのUIを作成
        for i, model in enumerate(models):
            self._create_model_widget(model, i)
    
    def _create_model_widget(self, model: Dict, row: int):
        """個別のモデルウィジェットを作成"""
        # モデルフレーム
        model_frame = ttk.LabelFrame(
            self.scrollable_frame,
            text=model["name"],
            padding="10"
        )
        model_frame.grid(row=row, column=0, sticky="ew", pady=5, padx=5)
        self.scrollable_frame.columnconfigure(0, weight=1)
        
        # 説明
        desc_label = ttk.Label(
            model_frame,
            text=model["description"],
            wraplength=400
        )
        desc_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        
        # サイズと用途と言語
        languages = model.get('languages', ['en'])
        lang_text = ', '.join([
            {'en': 'English', 'zh': 'Chinese', 'ja': 'Japanese', 'multi': 'Multilingual'}.get(lang, lang) 
            for lang in languages
        ])
        info_text = f"Size: {model['size']} | Purpose: {model['purpose']} | Languages: {lang_text}"
        ttk.Label(model_frame, text=info_text, foreground="gray").grid(
            row=1, column=0, sticky="w"
        )
        
        # ステータスとボタン
        status_frame = ttk.Frame(model_frame)
        status_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        
        if model["installed"]:
            # インストール済み
            status_label = ttk.Label(status_frame, text="✓ Installed", foreground="green")
            status_label.pack(side=tk.LEFT)
            
            # 使用ボタン
            use_button = ttk.Button(
                status_frame,
                text="Use This Model",
                command=lambda: self._use_model(model),
                width=18
            )
            use_button.pack(side=tk.LEFT, padx=5)
            
            # 削除ボタン
            delete_button = ttk.Button(
                status_frame,
                text="Delete",
                command=lambda: self._delete_model(model),
                width=12
            )
            delete_button.pack(side=tk.RIGHT)
            
        elif model["downloading"]:
            # ダウンロード中
            status_label = ttk.Label(status_frame, text="Downloading...", foreground="orange")
            status_label.pack(side=tk.LEFT)
            
            # プログレスバー
            progress_bar = ttk.Progressbar(
                status_frame,
                mode='indeterminate',
                length=200
            )
            progress_bar.pack(side=tk.LEFT, padx=5)
            progress_bar.start()
            
            self.model_widgets[model["key"]] = {
                "frame": model_frame,
                "status_label": status_label,
                "progress_bar": progress_bar
            }
            
        else:
            # 未インストール
            status_label = ttk.Label(status_frame, text="Not installed", foreground="gray")
            status_label.pack(side=tk.LEFT)
            
            # ダウンロードボタン
            download_button = ttk.Button(
                status_frame,
                text="Download",
                command=lambda: self._download_model(model),
                width=15
            )
            download_button.pack(side=tk.LEFT, padx=5)
    
    def _download_model(self, model: Dict):
        """モデルをダウンロード"""
        model_key = model["key"]
        
        # カスタムモデルはダウンロードできない
        if model_key.startswith("custom_"):
            messagebox.showinfo("Info", "This is a custom model.", parent=self)
            return
        
        # 確認ダイアログ
        if not messagebox.askyesno(
            "Download Model",
            f"Download {model['name']}?\nSize: {model['size']}",
            parent=self
        ):
            return
        
        # ダウンロード開始
        # プログレスキューを使用してスレッドセーフに更新
        import queue
        progress_queue = queue.Queue()
        
        def progress_callback(progress: DownloadProgress):
            # キューに追加（スレッドセーフ）
            progress_queue.put((model_key, progress))
        
        # ダウンロード開始を記録
        self._download_progress[model_key] = True
        
        # キューをチェックする関数
        def check_progress_queue():
            has_items = False
            try:
                while True:
                    key, progress = progress_queue.get_nowait()
                    self._update_download_progress(key, progress)
                    has_items = True
            except queue.Empty:
                pass
            
            # 次のチェックをスケジュール（ダウンロード中の場合）
            if has_items or model_key in self._download_progress:
                self.after(100, check_progress_queue)
        
        # キューチェックを開始
        self.after(100, check_progress_queue)
        
        # バックグラウンドでダウンロード
        import threading
        download_thread = threading.Thread(
            target=lambda: self.model_manager.download_model(model_key, progress_callback),
            daemon=True
        )
        download_thread.start()
        
        # UIを更新
        self._refresh_model_list()
    
    def _update_download_progress(self, model_key: str, progress: DownloadProgress):
        """ダウンロード進捗を更新"""
        if progress.status == "completed":
            # ダウンロード完了時に追跡を削除
            if model_key in self._download_progress:
                del self._download_progress[model_key]
            messagebox.showinfo("Success", f"{progress.model_name} downloaded successfully!", parent=self)
            self._refresh_model_list()
        elif progress.status == "error":
            # エラー時も追跡を削除
            if model_key in self._download_progress:
                del self._download_progress[model_key]
            messagebox.showerror("Error", f"Failed to download: {progress.error_message}", parent=self)
            self._refresh_model_list()
        else:
            # 進捗更新（現在は未実装）
            pass
    
    def _use_model(self, model: Dict):
        """モデルを使用"""
        from thonny import get_workbench
        workbench = get_workbench()
        
        # 設定を更新
        workbench.set_option("llm.model_path", model["path"])
        
        # 用途に応じた設定
        if model["purpose"] == "explanation":
            workbench.set_option("llm.temperature", 0.3)  # より一貫性のある説明
        elif model["purpose"] == "coding":
            workbench.set_option("llm.temperature", 0.7)  # より創造的なコード生成
        
        messagebox.showinfo(
            "Model Selected",
            f"{model['name']} is now the active model.\n\nRestart the LLM Assistant to use this model.",
            parent=self
        )
        
        # 親ダイアログの設定変更フラグを立てる
        if hasattr(self.master, 'settings_changed'):
            self.master.settings_changed = True
    
    def _delete_model(self, model: Dict):
        """モデルを削除"""
        if not messagebox.askyesno(
            "Delete Model",
            f"Delete {model['name']}?\nThis action cannot be undone.",
            parent=self
        ):
            return
        
        if self.model_manager.delete_model(model["path"]):
            messagebox.showinfo("Success", "Model deleted successfully.", parent=self)
            self._refresh_model_list()
        else:
            messagebox.showerror("Error", "Failed to delete model.", parent=self)