"""
設定ダイアログ
モデルパスやその他の設定を管理
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from thonny import get_workbench


class SettingsDialog(tk.Toplevel):
    """LLMプラグインの設定ダイアログ"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("LLM Assistant Settings")
        
        self.workbench = get_workbench()
        self.settings_changed = False
        
        self._init_ui()
        self._load_settings()
        
        # コンテンツのサイズに基づいてウィンドウサイズを調整
        self.update_idletasks()
        self._adjust_window_size()
    
    def _init_ui(self):
        """UIを初期化"""
        # スクロール可能なキャンバスを作成
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
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
        
        # Canvasにフォーカスがある時のみスクロール
        def _on_enter(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            # Linux/macOS
            canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
            canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        
        def _on_leave(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
        
        canvas.bind("<Enter>", _on_enter)
        canvas.bind("<Leave>", _on_leave)
        
        # ウィンドウを閉じる時にバインディングを解除
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # レイアウト
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # メインフレーム（スクロール可能フレーム内）
        main_frame = ttk.Frame(self.scrollable_frame, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.scrollable_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # モデル設定
        ttk.Label(main_frame, text="Model Settings", font=("", 10, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 10)
        )
        
        # モデルパス
        ttk.Label(main_frame, text="Model Path:").grid(row=1, column=0, sticky="w", pady=5)
        self.model_path_var = tk.StringVar()
        self.model_path_entry = ttk.Entry(main_frame, textvariable=self.model_path_var)
        self.model_path_entry.grid(row=1, column=1, sticky="ew", pady=5)
        
        ttk.Button(
            main_frame,
            text="Browse...",
            command=self._browse_model,
            width=15
        ).grid(row=1, column=2, padx=(5, 0), pady=5)
        
        # コンテキストサイズ
        ttk.Label(main_frame, text="Context Size:").grid(row=2, column=0, sticky="w", pady=5)
        self.context_size_var = tk.IntVar(value=4096)
        context_spinbox = ttk.Spinbox(
            main_frame,
            from_=512,
            to=32768,
            increment=512,
            textvariable=self.context_size_var,
            width=10
        )
        context_spinbox.grid(row=2, column=1, sticky="w", pady=5)
        
        # 生成設定
        ttk.Label(main_frame, text="Generation Settings", font=("", 10, "bold")).grid(
            row=3, column=0, columnspan=3, sticky="w", pady=(20, 10)
        )
        
        # Temperature
        ttk.Label(main_frame, text="Temperature:").grid(row=4, column=0, sticky="w", pady=5)
        self.temperature_var = tk.DoubleVar(value=0.7)
        temperature_scale = ttk.Scale(
            main_frame,
            from_=0.0,
            to=2.0,
            orient=tk.HORIZONTAL,
            variable=self.temperature_var
        )
        temperature_scale.grid(row=4, column=1, sticky="ew", pady=5)
        
        self.temperature_label = ttk.Label(main_frame, text="0.7")
        self.temperature_label.grid(row=4, column=2, pady=5)
        
        # Temperature値の更新
        def update_temp_label(value):
            self.temperature_label.config(text=f"{float(value):.1f}")
        temperature_scale.config(command=update_temp_label)
        
        # Max Tokens
        ttk.Label(main_frame, text="Max Tokens:").grid(row=5, column=0, sticky="w", pady=5)
        self.max_tokens_var = tk.IntVar(value=2048)
        tokens_spinbox = ttk.Spinbox(
            main_frame,
            from_=128,
            to=4096,
            increment=128,
            textvariable=self.max_tokens_var,
            width=10
        )
        tokens_spinbox.grid(row=5, column=1, sticky="w", pady=5)
        
        # Repeat Penalty
        ttk.Label(main_frame, text="Repeat Penalty:").grid(row=6, column=0, sticky="w", pady=5)
        self.repeat_penalty_var = tk.DoubleVar(value=1.1)
        repeat_penalty_scale = ttk.Scale(
            main_frame,
            from_=1.0,
            to=2.0,
            orient=tk.HORIZONTAL,
            variable=self.repeat_penalty_var
        )
        repeat_penalty_scale.grid(row=6, column=1, sticky="ew", pady=5)
        
        self.repeat_penalty_label = ttk.Label(main_frame, text="1.1")
        self.repeat_penalty_label.grid(row=6, column=2, pady=5)
        
        # Repeat Penalty値の更新
        def update_repeat_penalty_label(value):
            self.repeat_penalty_label.config(text=f"{float(value):.2f}")
        repeat_penalty_scale.config(command=update_repeat_penalty_label)
        
        # Repeat Penaltyのヒント
        repeat_hint = ttk.Label(
            main_frame,
            text="Higher values reduce repetition (1.3+ recommended for small models)",
            font=("", 8),
            foreground="gray"
        )
        repeat_hint.grid(row=7, column=1, columnspan=2, sticky="w", pady=(0, 10))
        
        # ユーザー設定
        ttk.Label(main_frame, text="User Settings", font=("", 10, "bold")).grid(
            row=8, column=0, columnspan=3, sticky="w", pady=(20, 10)
        )
        
        # スキルレベル
        ttk.Label(main_frame, text="Skill Level:").grid(row=9, column=0, sticky="w", pady=5)
        self.skill_level_var = tk.StringVar(value="beginner")
        skill_combo = ttk.Combobox(
            main_frame,
            textvariable=self.skill_level_var,
            values=["beginner", "intermediate", "advanced"],
            state="readonly",
            width=15
        )
        skill_combo.grid(row=9, column=1, sticky="w", pady=5)
        
        # Markdownレンダリング
        ttk.Label(main_frame, text="Use Markdown View:").grid(row=10, column=0, sticky="w", pady=5)
        self.use_html_view_var = tk.BooleanVar(value=True)
        html_check = ttk.Checkbutton(
            main_frame,
            text="Enable Markdown rendering (requires tkinterweb)",
            variable=self.use_html_view_var
        )
        html_check.grid(row=10, column=1, sticky="w", pady=5)
        
        # 出力言語
        ttk.Label(main_frame, text="Output Language:").grid(row=11, column=0, sticky="w", pady=5)
        self.output_language_var = tk.StringVar(value="auto")
        
        # 言語オプション
        language_options = [
            ("auto", "Auto (Follow Thonny)"),
            ("ja", "日本語"),
            ("en", "English"),
            ("zh-CN", "中文（简体）"),
            ("zh-TW", "中文（繁體）"),
            ("other", "Other...")
        ]
        
        language_frame = ttk.Frame(main_frame)
        language_frame.grid(row=11, column=1, columnspan=2, sticky="w", pady=5)
        
        self.language_combo = ttk.Combobox(
            language_frame,
            textvariable=self.output_language_var,
            values=[code for code, _ in language_options],
            state="readonly",
            width=15
        )
        self.language_combo.grid(row=0, column=0, sticky="w")
        self.language_combo.bind("<<ComboboxSelected>>", self._on_language_changed)
        
        # 言語表示ラベル
        self.language_label = ttk.Label(language_frame, text="", foreground="gray")
        self.language_label.grid(row=0, column=1, padx=(10, 0))
        
        # カスタム言語入力（Other...選択時のみ表示）
        self.custom_language_frame = ttk.Frame(main_frame)
        self.custom_language_entry = ttk.Entry(self.custom_language_frame, width=30)
        ttk.Label(self.custom_language_frame, text="Language code:").pack(side=tk.LEFT, padx=(0, 5))
        self.custom_language_entry.pack(side=tk.LEFT)
        # 初期状態では非表示
        
        # 外部プロバイダー設定
        ttk.Label(main_frame, text="Provider Settings", font=("", 10, "bold")).grid(
            row=13, column=0, columnspan=3, sticky="w", pady=(20, 10)
        )
        
        # プロバイダー選択
        ttk.Label(main_frame, text="Provider:").grid(row=14, column=0, sticky="w", pady=5)
        self.provider_var = tk.StringVar(value="local")
        provider_combo = ttk.Combobox(
            main_frame,
            textvariable=self.provider_var,
            values=["local", "chatgpt", "ollama", "openrouter"],
            state="readonly",
            width=15
        )
        provider_combo.grid(row=14, column=1, sticky="w", pady=5)
        provider_combo.bind("<<ComboboxSelected>>", self._on_provider_changed)
        
        # APIキー（外部プロバイダー用）
        self.api_key_label = ttk.Label(main_frame, text="API Key:")
        self.api_key_label.grid(row=15, column=0, sticky="w", pady=5)
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(main_frame, textvariable=self.api_key_var, show="*")
        self.api_key_entry.grid(row=15, column=1, sticky="ew", pady=5)
        
        # ベースURL（Ollama用）
        self.base_url_label = ttk.Label(main_frame, text="Base URL:")
        self.base_url_label.grid(row=16, column=0, sticky="w", pady=5)
        self.base_url_var = tk.StringVar(value="http://localhost:11434")
        self.base_url_entry = ttk.Entry(main_frame, textvariable=self.base_url_var)
        self.base_url_entry.grid(row=16, column=1, sticky="ew", pady=5)
        
        # 外部モデル名
        self.external_model_label = ttk.Label(main_frame, text="Model Name:")
        self.external_model_label.grid(row=17, column=0, sticky="w", pady=5)
        self.external_model_var = tk.StringVar(value="gpt-3.5-turbo")
        self.external_model_entry = ttk.Entry(main_frame, textvariable=self.external_model_var)
        self.external_model_entry.grid(row=17, column=1, sticky="ew", pady=5)
        
        # システムプロンプト設定
        ttk.Label(main_frame, text="System Prompt", font=("", 10, "bold")).grid(
            row=18, column=0, columnspan=3, sticky="w", pady=(20, 10)
        )
        
        # プロンプトタイプ選択
        ttk.Label(main_frame, text="Prompt Type:").grid(row=19, column=0, sticky="w", pady=5)
        self.prompt_type_var = tk.StringVar(value="default")
        prompt_frame = ttk.Frame(main_frame)
        prompt_frame.grid(row=19, column=1, columnspan=2, sticky="w", pady=5)
        
        ttk.Radiobutton(
            prompt_frame,
            text="Default",
            variable=self.prompt_type_var,
            value="default",
            command=self._update_prompt_preview
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            prompt_frame,
            text="Custom",
            variable=self.prompt_type_var,
            value="custom",
            command=self._update_prompt_preview
        ).pack(side=tk.LEFT, padx=5)
        
        # カスタムプロンプト編集ボタン
        ttk.Button(
            main_frame,
            text="Edit Custom Prompt",
            command=self._edit_custom_prompt,
            width=22
        ).grid(row=20, column=0, columnspan=2, sticky="w", pady=5)
        
        # ボタンフレーム
        button_frame = ttk.Frame(self)
        button_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        ttk.Button(
            button_frame,
            text="Save",
            command=self._save_settings,
            width=12
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.destroy,
            width=12
        ).pack(side=tk.RIGHT)
        
        ttk.Button(
            button_frame,
            text="Test Model",
            command=self._test_model,
            width=18
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Download Models",
            command=self._show_model_manager,
            width=18
        ).pack(side=tk.LEFT, padx=5)
    
    def _browse_model(self):
        """モデルファイルを選択"""
        # 現在のパスからベースディレクトリを取得
        current_path = self.model_path_var.get()
        if current_path and Path(current_path).exists():
            # ファイルの親ディレクトリを初期ディレクトリとする
            initial_dir = str(Path(current_path).parent)
        elif current_path and Path(current_path).parent.exists():
            # パスが存在しなくても親ディレクトリが存在すれば使用
            initial_dir = str(Path(current_path).parent)
        else:
            # デフォルトはモデルディレクトリまたはホーム
            from ..model_manager import ModelManager
            model_manager = ModelManager()
            models_dir = model_manager.get_models_dir()
            initial_dir = str(models_dir) if models_dir.exists() else str(Path.home())
        
        filename = filedialog.askopenfilename(
            title="Select GGUF Model File",
            filetypes=[("GGUF files", "*.gguf"), ("All files", "*.*")],
            initialdir=initial_dir
        )
        if filename:
            self.model_path_var.set(filename)
    
    def _load_settings(self):
        """設定を読み込む"""
        self.model_path_var.set(self.workbench.get_option("llm.model_path", ""))
        self.context_size_var.set(self.workbench.get_option("llm.context_size", 4096))
        self.temperature_var.set(self.workbench.get_option("llm.temperature", 0.7))
        self.max_tokens_var.set(self.workbench.get_option("llm.max_tokens", 2048))
        self.repeat_penalty_var.set(self.workbench.get_option("llm.repeat_penalty", 1.1))
        self.skill_level_var.set(self.workbench.get_option("llm.skill_level", "beginner"))
        self.prompt_type_var.set(self.workbench.get_option("llm.prompt_type", "default"))
        self.use_html_view_var.set(self.workbench.get_option("llm.use_html_view", True))
        
        # 言語設定を読み込む（デフォルトはThonnyの言語設定に従う）
        default_language = "auto"
        thonny_language = self.workbench.get_option("general.language", None)
        if thonny_language and thonny_language.startswith("ja"):
            default_language = "ja"
        elif thonny_language and thonny_language.startswith("zh"):
            if "TW" in thonny_language or "HK" in thonny_language:
                default_language = "zh-TW"
            else:
                default_language = "zh-CN"
        
        saved_language = self.workbench.get_option("llm.output_language", default_language)
        if saved_language == "other":
            # カスタム言語コードも読み込む
            self.custom_language_entry.delete(0, tk.END)
            self.custom_language_entry.insert(0, self.workbench.get_option("llm.custom_language_code", ""))
        self.output_language_var.set(saved_language)
        self._on_language_changed()  # UIを更新
        
        # プロバイダー設定を読み込む
        self.provider_var.set(self.workbench.get_option("llm.provider", "local"))
        self.api_key_var.set(self.workbench.get_option("llm.api_key", ""))
        self.base_url_var.set(self.workbench.get_option("llm.base_url", "http://localhost:11434"))
        self.external_model_var.set(self.workbench.get_option("llm.external_model", "gpt-3.5-turbo"))
        
        # カスタムプロンプトを読み込む
        self.custom_prompt = self.workbench.get_option("llm.custom_prompt", "")
        
        # 初期表示状態を更新
        self._on_provider_changed()
    
    def _save_settings(self):
        """設定を保存"""
        # 検証
        provider = self.provider_var.get()
        
        if provider == "local":
            model_path = self.model_path_var.get()
            if model_path and not Path(model_path).exists():
                messagebox.showerror("Error", "Model file does not exist!")
                return
        else:
            # 外部プロバイダーの検証
            if provider in ["chatgpt", "openrouter"] and not self.api_key_var.get():
                messagebox.showerror("Error", f"API key is required for {provider}!")
                return
        
        # HTMLビュー設定の変更をチェック（保存前に）
        old_use_html = self.workbench.get_option("llm.use_html_view", True)
        new_use_html = self.use_html_view_var.get()
        html_view_changed = old_use_html != new_use_html
        
        # 保存
        self.workbench.set_option("llm.provider", provider)
        self.workbench.set_option("llm.model_path", self.model_path_var.get())
        self.workbench.set_option("llm.context_size", self.context_size_var.get())
        self.workbench.set_option("llm.temperature", self.temperature_var.get())
        self.workbench.set_option("llm.max_tokens", self.max_tokens_var.get())
        self.workbench.set_option("llm.repeat_penalty", self.repeat_penalty_var.get())
        self.workbench.set_option("llm.skill_level", self.skill_level_var.get())
        self.workbench.set_option("llm.prompt_type", self.prompt_type_var.get())
        self.workbench.set_option("llm.use_html_view", self.use_html_view_var.get())
        
        # 言語設定を保存
        output_language = self.output_language_var.get()
        self.workbench.set_option("llm.output_language", output_language)
        if output_language == "other":
            self.workbench.set_option("llm.custom_language_code", self.custom_language_entry.get())
        
        # プロバイダー設定を保存
        self.workbench.set_option("llm.api_key", self.api_key_var.get())
        self.workbench.set_option("llm.base_url", self.base_url_var.get())
        self.workbench.set_option("llm.external_model", self.external_model_var.get())
        
        if hasattr(self, 'custom_prompt'):
            self.workbench.set_option("llm.custom_prompt", self.custom_prompt)
        
        self.settings_changed = True
        
        # HTMLビュー設定が変更された場合は再起動を促す
        if html_view_changed:
            messagebox.showinfo(
                "Restart Required", 
                "The Markdown view setting change will take effect after restarting the LLM Assistant view.\n\n"
                "Close and reopen the LLM Assistant from Tools menu."
            )
        else:
            messagebox.showinfo("Success", "Settings saved successfully!")
        
        self.destroy()
    
    def _test_model(self):
        """モデルをテスト"""
        provider = self.provider_var.get()
        
        if provider == "local":
            model_path = self.model_path_var.get()
            if not model_path:
                messagebox.showerror("Error", "Please select a model file first!")
                return
            
            if not Path(model_path).exists():
                messagebox.showerror("Error", "Model file does not exist!")
                return
        else:
            # 外部プロバイダーの検証
            if provider in ["chatgpt", "openrouter"] and not self.api_key_var.get():
                messagebox.showerror("Error", f"API key is required for {provider}!")
                return
        
        # プログレスダイアログ
        progress = tk.Toplevel(self)
        progress.title("Testing Connection")
        progress.geometry("300x100")
        ttk.Label(progress, text="Testing connection...").pack(pady=20)
        progress_bar = ttk.Progressbar(progress, mode='indeterminate')
        progress_bar.pack(padx=20, pady=10)
        progress_bar.start()
        
        def test():
            try:
                if provider == "local":
                    from .. import get_llm_client
                    from ..llm_client import ModelConfig
                    
                    # テスト用の設定でクライアントを作成
                    client = get_llm_client()
                    config = ModelConfig(
                        model_path=self.model_path_var.get(),
                        n_ctx=self.context_size_var.get(),
                        temperature=self.temperature_var.get(),
                        max_tokens=self.max_tokens_var.get()
                    )
                    client.set_config(config)
                    
                    # テスト実行
                    result = client.test_connection()
                else:
                    # 外部プロバイダーのテスト
                    from ..external_providers import ChatGPTProvider, OllamaProvider, OpenRouterProvider
                    
                    if provider == "chatgpt":
                        provider_obj = ChatGPTProvider(
                            api_key=self.api_key_var.get(),
                            model=self.external_model_var.get()
                        )
                    elif provider == "ollama":
                        provider_obj = OllamaProvider(
                            base_url=self.base_url_var.get(),
                            model=self.external_model_var.get()
                        )
                    elif provider == "openrouter":
                        provider_obj = OpenRouterProvider(
                            api_key=self.api_key_var.get(),
                            model=self.external_model_var.get()
                        )
                    
                    result = provider_obj.test_connection()
                
                # 結果を表示
                progress.destroy()
                
                if result.get("error") or not result.get("success"):
                    messagebox.showerror("Test Failed", f"Error: {result.get('error', 'Unknown error')}")
                else:
                    info = f"Provider: {result.get('provider', provider)}\n"
                    info += f"Model: {result.get('model', 'N/A')}\n"
                    if result.get('response'):
                        info += f"Test response: {result.get('response')}"
                    elif result.get('available_models'):
                        info += f"Available models: {', '.join(result['available_models'][:5])}"
                    
                    messagebox.showinfo("Test Successful", info)
                    
            except Exception as e:
                progress.destroy()
                messagebox.showerror("Test Failed", f"Error: {str(e)}")
        
        # バックグラウンドでテスト
        import threading
        thread = threading.Thread(target=test, daemon=True)
        thread.start()
    
    def _show_model_manager(self):
        """モデルマネージャーダイアログを表示"""
        from .model_download_dialog import ModelDownloadDialog
        dialog = ModelDownloadDialog(self)
        dialog.grab_set()
        self.wait_window(dialog)
        
        # モデルが変更された可能性があるので、パスを更新
        from ..model_manager import ModelManager
        manager = ModelManager()
        
        # 現在のパスが無効な場合、利用可能なモデルを設定
        current_path = self.model_path_var.get()
        if not current_path or not Path(current_path).exists():
            # 軽量モデルを優先
            new_path = manager.get_model_path("llama3.2-1b")
            if new_path:
                self.model_path_var.set(new_path)
                self.settings_changed = True
    
    def _update_prompt_preview(self):
        """プロンプトタイプ変更時の処理"""
        # 特に処理なし（将来的にプレビュー機能を追加可能）
        pass
    
    def _edit_custom_prompt(self):
        """カスタムプロンプトを編集"""
        dialog = tk.Toplevel(self)
        dialog.title("Edit Custom System Prompt")
        dialog.geometry("600x400")
        
        # 説明ラベル
        ttk.Label(
            dialog,
            text="Enter your custom system prompt for the LLM:",
            font=("", 10)
        ).pack(pady=10)
        
        # テキストエディタ
        text_frame = ttk.Frame(dialog)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        text_editor = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 10))
        text_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame, command=text_editor.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_editor.config(yscrollcommand=scrollbar.set)
        
        # 現在のカスタムプロンプトを表示
        if hasattr(self, 'custom_prompt') and self.custom_prompt:
            text_editor.insert("1.0", self.custom_prompt)
        else:
            # デフォルトのテンプレートを提供
            text_editor.insert("1.0", """You are a helpful AI assistant integrated into Thonny IDE.

[Customize this prompt to define how the AI should behave]

Example customizations:
- Focus on specific programming paradigms (functional, OOP, etc.)
- Emphasize certain coding standards or practices
- Adapt communication style for your needs
- Add domain-specific knowledge requirements
""")
        
        # ボタンフレーム
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, pady=10)
        
        def save_prompt():
            self.custom_prompt = text_editor.get("1.0", tk.END).strip()
            self.prompt_type_var.set("custom")
            dialog.destroy()
        
        def load_default_template():
            from ..llm_client import LLMClient
            client = LLMClient()
            text_editor.delete("1.0", tk.END)
            text_editor.insert("1.0", client.default_system_prompt)
        
        # テンプレートボタン
        ttk.Button(
            button_frame,
            text="Load Default Template",
            command=load_default_template
        ).pack(side=tk.LEFT, padx=5)
        
        # 保存・キャンセルボタン
        ttk.Button(
            button_frame,
            text="Save",
            command=save_prompt
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT)
    
    def _on_language_changed(self, event=None):
        """言語変更時の処理"""
        language = self.output_language_var.get()
        
        # 言語名を表示
        language_names = {
            "auto": "Auto (Follow Thonny)",
            "ja": "日本語",
            "en": "English",
            "zh-CN": "中文（简体）",
            "zh-TW": "中文（繁體）",
            "other": "Other..."
        }
        
        self.language_label.config(text=language_names.get(language, ""))
        
        # Other...を選択した場合はカスタム入力欄を表示
        if language == "other":
            self.custom_language_frame.grid(row=10, column=1, columnspan=2, sticky="w", pady=5)
        else:
            self.custom_language_frame.grid_remove()
    
    def _on_provider_changed(self, event=None):
        """プロバイダー変更時の処理"""
        provider = self.provider_var.get()
        
        if provider == "local":
            # ローカルモデルの設定を表示
            self.model_path_entry.config(state=tk.NORMAL)
            self.api_key_label.grid_remove()
            self.api_key_entry.grid_remove()
            self.base_url_label.grid_remove()
            self.base_url_entry.grid_remove()
            self.external_model_label.grid_remove()
            self.external_model_entry.grid_remove()
        else:
            # 外部プロバイダーの設定を表示
            self.model_path_entry.config(state=tk.DISABLED)
            
            if provider == "chatgpt":
                self.api_key_label.grid()
                self.api_key_entry.grid()
                self.base_url_label.grid_remove()
                self.base_url_entry.grid_remove()
                self.external_model_label.grid()
                self.external_model_entry.grid()
                self.external_model_var.set("gpt-3.5-turbo")
            elif provider == "ollama":
                self.api_key_label.grid_remove()
                self.api_key_entry.grid_remove()
                self.base_url_label.grid()
                self.base_url_entry.grid()
                self.external_model_label.grid()
                self.external_model_entry.grid()
                self.external_model_var.set("llama3")
            elif provider == "openrouter":
                self.api_key_label.grid()
                self.api_key_entry.grid()
                self.base_url_label.grid_remove()
                self.base_url_entry.grid_remove()
                self.external_model_label.grid()
                self.external_model_entry.grid()
                self.external_model_var.set("meta-llama/llama-3.2-3b-instruct:free")
    
    def _adjust_window_size(self):
        """ウィンドウサイズをコンテンツに合わせて調整"""
        # コンテンツのサイズを取得
        self.update_idletasks()
        
        # スクロール可能フレームの実際のサイズを取得
        content_width = self.scrollable_frame.winfo_reqwidth() + 20  # スクロールバー分を追加
        content_height = self.scrollable_frame.winfo_reqheight() + 80  # ボタンエリア分を追加
        
        # 画面サイズを取得
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # 最大サイズを画面の80%に制限
        max_width = int(screen_width * 0.8)
        max_height = int(screen_height * 0.8)
        
        # 最小サイズを設定
        min_width = 600
        min_height = 400
        
        # 実際のウィンドウサイズを決定
        window_width = max(min_width, min(content_width, max_width))
        window_height = max(min_height, min(content_height, max_height))
        
        # ウィンドウを中央に配置
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def _on_close(self):
        """ウィンドウを閉じる時の処理"""
        # マウスホイールのバインディングを解除
        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")
        self.destroy()