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
        self.geometry("500x400")
        
        self.workbench = get_workbench()
        self.settings_changed = False
        
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self):
        """UIを初期化"""
        # メインフレーム
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
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
        
        # ユーザー設定
        ttk.Label(main_frame, text="User Settings", font=("", 10, "bold")).grid(
            row=6, column=0, columnspan=3, sticky="w", pady=(20, 10)
        )
        
        # スキルレベル
        ttk.Label(main_frame, text="Skill Level:").grid(row=7, column=0, sticky="w", pady=5)
        self.skill_level_var = tk.StringVar(value="beginner")
        skill_combo = ttk.Combobox(
            main_frame,
            textvariable=self.skill_level_var,
            values=["beginner", "intermediate", "advanced"],
            state="readonly",
            width=15
        )
        skill_combo.grid(row=7, column=1, sticky="w", pady=5)
        
        # 外部プロバイダー設定
        ttk.Label(main_frame, text="Provider Settings", font=("", 10, "bold")).grid(
            row=8, column=0, columnspan=3, sticky="w", pady=(20, 10)
        )
        
        # プロバイダー選択
        ttk.Label(main_frame, text="Provider:").grid(row=9, column=0, sticky="w", pady=5)
        self.provider_var = tk.StringVar(value="local")
        provider_combo = ttk.Combobox(
            main_frame,
            textvariable=self.provider_var,
            values=["local", "chatgpt", "ollama", "openrouter"],
            state="readonly",
            width=15
        )
        provider_combo.grid(row=9, column=1, sticky="w", pady=5)
        provider_combo.bind("<<ComboboxSelected>>", self._on_provider_changed)
        
        # APIキー（外部プロバイダー用）
        self.api_key_label = ttk.Label(main_frame, text="API Key:")
        self.api_key_label.grid(row=10, column=0, sticky="w", pady=5)
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(main_frame, textvariable=self.api_key_var, show="*")
        self.api_key_entry.grid(row=10, column=1, sticky="ew", pady=5)
        
        # ベースURL（Ollama用）
        self.base_url_label = ttk.Label(main_frame, text="Base URL:")
        self.base_url_label.grid(row=11, column=0, sticky="w", pady=5)
        self.base_url_var = tk.StringVar(value="http://localhost:11434")
        self.base_url_entry = ttk.Entry(main_frame, textvariable=self.base_url_var)
        self.base_url_entry.grid(row=11, column=1, sticky="ew", pady=5)
        
        # 外部モデル名
        self.external_model_label = ttk.Label(main_frame, text="Model Name:")
        self.external_model_label.grid(row=12, column=0, sticky="w", pady=5)
        self.external_model_var = tk.StringVar(value="gpt-3.5-turbo")
        self.external_model_entry = ttk.Entry(main_frame, textvariable=self.external_model_var)
        self.external_model_entry.grid(row=12, column=1, sticky="ew", pady=5)
        
        # システムプロンプト設定
        ttk.Label(main_frame, text="System Prompt", font=("", 10, "bold")).grid(
            row=13, column=0, columnspan=3, sticky="w", pady=(20, 10)
        )
        
        # プロンプトタイプ選択
        ttk.Label(main_frame, text="Prompt Type:").grid(row=14, column=0, sticky="w", pady=5)
        self.prompt_type_var = tk.StringVar(value="coding")
        prompt_frame = ttk.Frame(main_frame)
        prompt_frame.grid(row=14, column=1, columnspan=2, sticky="w", pady=5)
        
        ttk.Radiobutton(
            prompt_frame,
            text="Coding",
            variable=self.prompt_type_var,
            value="coding",
            command=self._update_prompt_preview
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            prompt_frame,
            text="Explanation",
            variable=self.prompt_type_var,
            value="explanation",
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
        ).grid(row=15, column=0, columnspan=2, sticky="w", pady=5)
        
        # ボタンフレーム
        button_frame = ttk.Frame(self)
        button_frame.grid(row=1, column=0, sticky="ew", pady=10)
        
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
        self.skill_level_var.set(self.workbench.get_option("llm.skill_level", "beginner"))
        self.prompt_type_var.set(self.workbench.get_option("llm.prompt_type", "coding"))
        
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
        
        # 保存
        self.workbench.set_option("llm.provider", provider)
        self.workbench.set_option("llm.model_path", self.model_path_var.get())
        self.workbench.set_option("llm.context_size", self.context_size_var.get())
        self.workbench.set_option("llm.temperature", self.temperature_var.get())
        self.workbench.set_option("llm.max_tokens", self.max_tokens_var.get())
        self.workbench.set_option("llm.skill_level", self.skill_level_var.get())
        self.workbench.set_option("llm.prompt_type", self.prompt_type_var.get())
        
        # プロバイダー設定を保存
        self.workbench.set_option("llm.api_key", self.api_key_var.get())
        self.workbench.set_option("llm.base_url", self.base_url_var.get())
        self.workbench.set_option("llm.external_model", self.external_model_var.get())
        
        if hasattr(self, 'custom_prompt'):
            self.workbench.set_option("llm.custom_prompt", self.custom_prompt)
        
        self.settings_changed = True
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
            # 解説用モデルを優先
            new_path = manager.get_model_path("explanation")
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
        
        def load_template(template_type):
            if template_type == "coding":
                from ..llm_client import LLMClient
                client = LLMClient()
                text_editor.delete("1.0", tk.END)
                text_editor.insert("1.0", client.coding_system_prompt)
            elif template_type == "explanation":
                from ..llm_client import LLMClient
                client = LLMClient()
                text_editor.delete("1.0", tk.END)
                text_editor.insert("1.0", client.explanation_system_prompt)
        
        # テンプレートボタン
        ttk.Button(
            button_frame,
            text="Load Coding Template",
            command=lambda: load_template("coding")
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Load Explanation Template",
            command=lambda: load_template("explanation")
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