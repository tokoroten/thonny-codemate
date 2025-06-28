"""
新しいデザインの設定ダイアログ
重要度順に項目を配置
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Optional
import logging

from thonny import get_workbench
from ..i18n import tr

logger = logging.getLogger(__name__)


class SettingsDialog(tk.Toplevel):
    """新しいデザインの設定ダイアログ"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title(tr("LLM Assistant Settings"))
        self.geometry("700x750")  # ウィンドウサイズを拡大
        
        # モーダルダイアログ
        self.transient(parent)
        
        self.workbench = get_workbench()
        self.settings_changed = False
        
        # メインコンテナ
        main_container = ttk.Frame(self, padding="10")
        main_container.pack(fill="both", expand=True)
        
        # スクロール可能な領域を作成
        canvas = tk.Canvas(main_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # レイアウト
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # セクションを作成
        self._create_basic_section()
        self._create_generation_section()
        self._create_advanced_section()
        
        # ボタンフレーム
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=10, pady=15)  # パディングを増やす
        
        # ボタンのスタイルを設定（フォントサイズを大きく）
        button_style = ttk.Style()
        button_style.configure("Large.TButton", font=("", 11))
        
        # 左側のボタン
        left_buttons = ttk.Frame(button_frame)
        left_buttons.pack(side="left")
        
        ttk.Button(
            left_buttons,
            text=tr("Download Models"),
            command=self._show_model_manager,
            width=20,  # 幅を指定
            style="Large.TButton"
        ).pack(side="left", padx=(0, 8), ipady=5)  # ipadyで高さを増やす
        
        self.test_connection_button = ttk.Button(
            left_buttons,
            text=tr("Test Connection"),
            command=self._test_connection,
            width=20,  # 幅を指定
            style="Large.TButton"
        )
        self.test_connection_button.pack(side="left", ipady=5)  # ipadyで高さを増やす
        
        # 右側のボタン
        right_buttons = ttk.Frame(button_frame)
        right_buttons.pack(side="right")
        
        ttk.Button(
            right_buttons,
            text=tr("Save"),
            command=self._save_settings,
            width=12,  # 幅を指定
            style="Large.TButton"
        ).pack(side="left", padx=(0, 8), ipady=5)  # ipadyで高さを増やす
        
        ttk.Button(
            right_buttons,
            text=tr("Cancel"),
            command=self.destroy,
            width=12,  # 幅を指定
            style="Large.TButton"
        ).pack(side="left", ipady=5)  # ipadyで高さを増やす
        
        # 設定を読み込む
        self._load_settings()
        
        # 初期状態を更新
        self._on_provider_changed()
        
        # 初期化完了フラグを設定
        self._initialization_complete = True
    
    def _create_basic_section(self):
        """基本設定セクション"""
        # 基本設定（常に展開）
        basic_frame = ttk.LabelFrame(
            self.scrollable_frame,
            text=tr("Basic Settings"),
            padding="10"
        )
        basic_frame.pack(fill="x", padx=5, pady=5)
        
        # Provider
        ttk.Label(basic_frame, text=tr("Provider:")).grid(row=0, column=0, sticky="w", pady=5)
        self.provider_var = tk.StringVar(value="local")
        self.provider_combo = ttk.Combobox(
            basic_frame,
            textvariable=self.provider_var,
            values=["local", "chatgpt", "ollama/lmstudio", "openrouter"],
            state="readonly",
            width=20
        )
        self.provider_combo.grid(row=0, column=1, sticky="ew", pady=5)
        self.provider_combo.bind("<<ComboboxSelected>>", self._on_provider_changed)
        
        # Model/API Key（動的に切り替え）
        self.model_frame = ttk.Frame(basic_frame)
        self.model_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)
        
        # ローカルモデル用
        self.local_model_frame = ttk.Frame(self.model_frame)
        
        # 上部のパス入力部分
        path_frame = ttk.Frame(self.local_model_frame)
        path_frame.pack(fill="x")
        
        ttk.Label(path_frame, text=tr("Model:")).pack(side="left", padx=(0, 10))
        self.model_path_var = tk.StringVar()
        self.model_path_entry = ttk.Entry(
            path_frame,
            textvariable=self.model_path_var,
            width=30
        )
        self.model_path_entry.pack(side="left", padx=(0, 5))
        
        # エントリーフィールドのツールチップ設定
        self._create_dynamic_tooltip(self.model_path_entry)
        ttk.Button(
            path_frame,
            text=tr("Browse..."),
            command=self._browse_model,
            width=12  # 幅を指定
        ).pack(side="left")
        
        # 下部のファイル名表示ラベル
        self.model_filename_label = ttk.Label(
            self.local_model_frame,
            text="",
            foreground="gray",
            font=("", 9)
        )
        self.model_filename_label.pack(anchor="w", padx=(60, 0), pady=(2, 0))
        
        # パスが変更されたときにファイル名を更新
        self.model_path_var.trace_add("write", self._update_model_filename_label)
        
        # 外部API用
        self.api_frame = ttk.Frame(self.model_frame)
        
        # API Key
        self.api_key_frame = ttk.Frame(self.api_frame)
        ttk.Label(self.api_key_frame, text=tr("API Key:")).pack(side="left", padx=(0, 10))
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(
            self.api_key_frame,
            textvariable=self.api_key_var,
            show="*",
            width=40
        )
        self.api_key_entry.pack(side="left")
        
        # Ollama/LM Studio Server設定 (Basic Settingsに移動)
        self.ollama_server_frame = ttk.Frame(self.api_frame)
        ttk.Label(self.ollama_server_frame, text=tr("Server:")).pack(side="left", padx=(0, 10))
        
        # IP/Host
        ttk.Label(self.ollama_server_frame, text=tr("Host:")).pack(side="left", padx=(0, 5))
        self.ollama_host_var = tk.StringVar(value="localhost")
        self.ollama_host_entry = ttk.Entry(
            self.ollama_server_frame,
            textvariable=self.ollama_host_var,
            width=15
        )
        self.ollama_host_entry.pack(side="left", padx=(0, 10))
        
        # Port (デフォルトは11434だが、LM Studioの場合は1234)
        ttk.Label(self.ollama_server_frame, text=tr("Port:")).pack(side="left", padx=(0, 5))
        self.ollama_port_var = tk.StringVar(value="11434")
        self.ollama_port_entry = ttk.Entry(
            self.ollama_server_frame,
            textvariable=self.ollama_port_var,
            width=8
        )
        self.ollama_port_entry.pack(side="left")
        
        # クイック設定ボタン
        preset_frame = ttk.Frame(self.ollama_server_frame)
        preset_frame.pack(side="left", padx=(10, 0))
        
        ttk.Label(preset_frame, text=tr("Presets:")).pack(side="left", padx=(0, 5))
        
        # Ollamaプリセットボタン
        ttk.Button(
            preset_frame,
            text="Ollama",
            command=lambda: self._set_ollama_defaults(),
            width=8
        ).pack(side="left", padx=(0, 5))
        
        # LM Studioプリセットボタン
        ttk.Button(
            preset_frame,
            text="LM Studio",
            command=lambda: self._set_lmstudio_defaults(),
            width=8
        ).pack(side="left")
        
        # Host/Port変更時にBase URLを更新
        self.ollama_host_var.trace_add("write", self._update_base_url_from_host_port)
        self.ollama_port_var.trace_add("write", self._update_base_url_from_host_port)
        
        # Model Name（外部API用）
        self.model_name_frame = ttk.Frame(self.api_frame)
        ttk.Label(self.model_name_frame, text=tr("Model Name:")).pack(side="left", padx=(0, 10))
        self.external_model_var = tk.StringVar()
        
        # ChatGPT/OpenRouter用コンボボックス
        self.external_model_combo = ttk.Combobox(
            self.model_name_frame,
            textvariable=self.external_model_var,
            state="readonly",
            width=30
        )
        
        # Ollama用エントリー（削除予定、互換性のために残す）
        self.external_model_entry = ttk.Entry(
            self.model_name_frame,
            textvariable=self.external_model_var,
            width=30
        )
        
        # Ollama用リフレッシュボタン
        self.refresh_ollama_button = ttk.Button(
            self.model_name_frame,
            text=tr("Refresh"),
            command=self._fetch_ollama_models,
            width=10
        )
        
        # Language
        ttk.Label(basic_frame, text=tr("Language:")).grid(row=2, column=0, sticky="w", pady=5)
        self.output_language_var = tk.StringVar(value="auto")
        self.language_combo = ttk.Combobox(
            basic_frame,
            textvariable=self.output_language_var,
            values=["auto", "ja", "en", "zh-CN", "zh-TW"],
            state="readonly",
            width=20
        )
        self.language_combo.grid(row=2, column=1, sticky="ew", pady=5)
        
        # 言語表示名
        self.language_label = ttk.Label(basic_frame, text="", foreground="gray")
        self.language_label.grid(row=2, column=2, padx=(10, 0), pady=5)
        self.language_combo.bind("<<ComboboxSelected>>", self._update_language_label)
        
        # Skill Level
        ttk.Label(basic_frame, text=tr("Skill Level:")).grid(row=3, column=0, sticky="w", pady=5)
        self.skill_level_var = tk.StringVar(value="beginner")
        self.skill_combo = ttk.Combobox(
            basic_frame,
            textvariable=self.skill_level_var,
            values=["beginner", "intermediate", "advanced"],
            state="readonly",
            width=20
        )
        self.skill_combo.grid(row=3, column=1, sticky="ew", pady=5)
        
        # スキルレベル表示名
        self.skill_label = ttk.Label(basic_frame, text="", foreground="gray")
        self.skill_label.grid(row=3, column=2, padx=(10, 0), pady=5)
        self.skill_combo.bind("<<ComboboxSelected>>", self._update_skill_label)
        
        # グリッド設定
        basic_frame.columnconfigure(1, weight=1)
    
    def _create_generation_section(self):
        """生成設定セクション"""
        # 生成設定
        generation_frame = ttk.LabelFrame(
            self.scrollable_frame,
            text=tr("Generation Settings"),
            padding="10"
        )
        generation_frame.pack(fill="x", padx=5, pady=5)
        
        gen_frame = generation_frame
        
        # Temperature
        temp_frame = ttk.Frame(gen_frame)
        temp_frame.pack(fill="x", pady=5)
        
        temp_label = ttk.Label(temp_frame, text=tr("Temperature:"))
        temp_label.pack(side="left", padx=(0, 10))
        
        # Temperatureの説明ツールチップ
        temp_help = ttk.Label(temp_frame, text="(?)", foreground="blue", cursor="hand2")
        temp_help.pack(side="left", padx=(0, 10))
        self._create_tooltip(temp_help, tr("Controls randomness: 0.0 = deterministic, 2.0 = very creative"))
        self.temperature_var = tk.DoubleVar()
        temp_scale = ttk.Scale(
            temp_frame,
            from_=0.0,
            to=2.0,
            orient=tk.HORIZONTAL,
            variable=self.temperature_var,
            length=200
        )
        temp_scale.pack(side="left", padx=(0, 10))
        
        self.temp_label = ttk.Label(temp_frame, text="0.7")
        self.temp_label.pack(side="left")
        
        def update_temp_label(value):
            self.temp_label.config(text=f"{float(value):.1f}")
        temp_scale.config(command=update_temp_label)
        
        # Max Tokens
        tokens_frame = ttk.Frame(gen_frame)
        tokens_frame.pack(fill="x", pady=5)
        
        ttk.Label(tokens_frame, text=tr("Max Tokens:")).pack(side="left", padx=(0, 10))
        self.max_tokens_var = tk.IntVar()
        tokens_spinbox = ttk.Spinbox(
            tokens_frame,
            from_=128,
            to=4096,
            increment=128,
            textvariable=self.max_tokens_var,
            width=10
        )
        tokens_spinbox.pack(side="left")
        
        # Context Size
        context_frame = ttk.Frame(gen_frame)
        context_frame.pack(fill="x", pady=5)
        
        context_label = ttk.Label(context_frame, text=tr("Context Size:"))
        context_label.pack(side="left", padx=(0, 10))
        
        # Context Sizeの説明ツールチップ
        context_help = ttk.Label(context_frame, text="(?)", foreground="blue", cursor="hand2")
        context_help.pack(side="left", padx=(0, 10))
        self._create_tooltip(context_help, tr("Maximum number of tokens the model can process at once"))
        self.context_size_var = tk.IntVar()
        context_spinbox = ttk.Spinbox(
            context_frame,
            from_=512,
            to=32768,
            increment=512,
            textvariable=self.context_size_var,
            width=10
        )
        context_spinbox.pack(side="left")
        
        # Repeat Penalty
        repeat_frame = ttk.Frame(gen_frame)
        repeat_frame.pack(fill="x", pady=5)
        
        repeat_label = ttk.Label(repeat_frame, text=tr("Repeat Penalty:"))
        repeat_label.pack(side="left", padx=(0, 10))
        
        # Repeat Penaltyの説明ツールチップ
        repeat_help = ttk.Label(repeat_frame, text="(?)", foreground="blue", cursor="hand2")
        repeat_help.pack(side="left", padx=(0, 10))
        self._create_tooltip(repeat_help, tr("Penalty for repeating tokens: 1.0 = no penalty, 2.0 = strong penalty"))
        self.repeat_penalty_var = tk.DoubleVar()
        repeat_scale = ttk.Scale(
            repeat_frame,
            from_=1.0,
            to=2.0,
            orient=tk.HORIZONTAL,
            variable=self.repeat_penalty_var,
            length=200
        )
        repeat_scale.pack(side="left", padx=(0, 10))
        
        self.repeat_label = ttk.Label(repeat_frame, text="1.1")
        self.repeat_label.pack(side="left")
        
        def update_repeat_label(value):
            self.repeat_label.config(text=f"{float(value):.2f}")
        repeat_scale.config(command=update_repeat_label)
    
    def _create_advanced_section(self):
        """詳細設定セクション"""
        # 詳細設定
        advanced_frame = ttk.LabelFrame(
            self.scrollable_frame,
            text=tr("Advanced Settings"),
            padding="10"
        )
        advanced_frame.pack(fill="x", padx=5, pady=5)
        
        adv_frame = advanced_frame
        
        # Base URL (内部用、非表示)
        self.base_url_var = tk.StringVar(value="http://localhost:11434")
        
        # Base URLが変更された時にOllamaのモデルを再取得
        self.base_url_var.trace_add("write", self._on_base_url_changed)
        
        # System Prompt Type
        prompt_frame = ttk.Frame(adv_frame)
        prompt_frame.pack(fill="x", pady=5)
        
        ttk.Label(prompt_frame, text=tr("System Prompt:")).pack(side="left", padx=(0, 10))
        self.prompt_type_var = tk.StringVar(value="default")
        
        ttk.Radiobutton(
            prompt_frame,
            text=tr("Default"),
            variable=self.prompt_type_var,
            value="default"
        ).pack(side="left", padx=(0, 10))
        
        ttk.Radiobutton(
            prompt_frame,
            text=tr("Custom"),
            variable=self.prompt_type_var,
            value="custom"
        ).pack(side="left", padx=(0, 10))
        
        ttk.Button(
            prompt_frame,
            text=tr("Edit Custom Prompt"),
            command=self._edit_custom_prompt,
            width=20  # 幅を指定
        ).pack(side="left")
    
    def _on_provider_changed(self, event=None):
        """プロバイダー変更時の処理"""
        provider = self.provider_var.get()
        
        # ollama/lmstudioの場合はollamaとして扱う
        if provider == "ollama/lmstudio":
            provider = "ollama"
        
        # プロバイダー変更時に適切なAPIキーを読み込む
        if provider == "chatgpt":
            self.api_key_var.set(self.workbench.get_option("llm.chatgpt_api_key", ""))
        elif provider == "openrouter":
            self.api_key_var.set(self.workbench.get_option("llm.openrouter_api_key", ""))
        else:
            self.api_key_var.set("")
        
        # フレームを一旦非表示
        self.local_model_frame.pack_forget()
        self.api_frame.pack_forget()
        self.api_key_frame.pack_forget()
        self.model_name_frame.pack_forget()
        self.refresh_ollama_button.pack_forget()
        self.ollama_server_frame.pack_forget()
        
        if provider == "local":
            # ローカルモデル
            self.local_model_frame.pack(fill="x")
        else:
            # 外部API
            self.api_frame.pack(fill="x")
            
            if provider in ["chatgpt", "openrouter"]:
                self.api_key_frame.pack(fill="x", pady=2)
                self.model_name_frame.pack(fill="x", pady=2)
                
                # コンボボックスを表示
                self.external_model_entry.pack_forget()
                self.external_model_combo.pack(side="left")
                
                # モデルリストを更新
                if provider == "chatgpt":
                    models = [
                        "gpt-4o",
                        "gpt-4o-mini",
                        "gpt-4-turbo",
                        "gpt-4",
                        "o1-preview",
                        "o1-mini"
                    ]
                else:  # openrouter
                    models = [
                        "meta-llama/llama-3.2-3b-instruct:free",
                        "meta-llama/llama-3.2-1b-instruct:free",
                        "google/gemini-2.0-flash-exp:free",
                        "anthropic/claude-3.5-sonnet",
                        "openai/gpt-4o"
                    ]
                
                self.external_model_combo['values'] = models
                if self.external_model_var.get() not in models:
                    self.external_model_var.set(models[0])
            
            elif provider == "ollama":
                # サーバー設定を表示
                self.ollama_server_frame.pack(fill="x", pady=2)
                self.model_name_frame.pack(fill="x", pady=2)
                
                # Ollamaの場合もコンボボックスを使用
                self.external_model_entry.pack_forget()
                self.external_model_combo.pack(side="left")
                
                # リフレッシュボタンを表示
                self.refresh_ollama_button.pack(side="left", padx=(5, 0))
                
                # Ollamaからモデルを取得
                self._fetch_ollama_models()
    
    def _update_language_label(self, event=None):
        """言語ラベルを更新"""
        lang_names = {
            "auto": tr("Auto (Follow Thonny)"),
            "ja": "日本語",
            "en": "English",
            "zh-CN": "中文（简体）",
            "zh-TW": "中文（繁體）"
        }
        lang = self.output_language_var.get()
        self.language_label.config(text=lang_names.get(lang, ""))
    
    def _update_skill_label(self, event=None):
        """スキルレベルラベルを更新"""
        skill_names = {
            "beginner": tr("beginner"),
            "intermediate": tr("intermediate"),
            "advanced": tr("advanced")
        }
        skill = self.skill_level_var.get()
        self.skill_label.config(text=skill_names.get(skill, ""))
    
    def _browse_model(self):
        """モデルファイルを選択"""
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
    
    def _show_model_manager(self):
        """モデルマネージャーを表示"""
        from .model_download_dialog import ModelDownloadDialog
        dialog = ModelDownloadDialog(self)
        self.wait_window(dialog)
        
        # モデルが選択された場合
        if hasattr(dialog, 'selected_model_path') and dialog.selected_model_path:
            self.model_path_var.set(dialog.selected_model_path)
            self.provider_var.set("local")
            self._on_provider_changed()
    
    def _test_connection(self):
        """接続テスト"""
        provider = self.provider_var.get()
        
        # ollama/lmstudioの場合はollamaとして扱う
        if provider == "ollama/lmstudio":
            provider = "ollama"
        
        if provider == "local":
            model_path = self.model_path_var.get()
            if not model_path or not Path(model_path).exists():
                messagebox.showerror(tr("Error"), tr("Please select a valid model file!"))
            else:
                messagebox.showinfo(tr("Success"), tr("Model file found!"))
        else:
            # 外部APIのテスト
            if provider in ["chatgpt", "openrouter"] and not self.api_key_var.get():
                messagebox.showerror(tr("Error"), tr("API key is required for {}").format(provider))
                return
            
            # 実際のAPI接続テストを実装
            self.test_connection_button.config(state="disabled", text=tr("Testing..."))
            
            def test_api():
                try:
                    if provider == "ollama":
                        from ..external_providers import OllamaProvider
                        api_provider = OllamaProvider(
                            base_url=self.base_url_var.get(),
                            model=self.external_model_var.get()
                        )
                    elif provider == "chatgpt":
                        from ..external_providers import ChatGPTProvider
                        api_provider = ChatGPTProvider(
                            api_key=self.api_key_var.get(),
                            model=self.external_model_var.get()
                        )
                    elif provider == "openrouter":
                        from ..external_providers import OpenRouterProvider
                        api_provider = OpenRouterProvider(
                            api_key=self.api_key_var.get(),
                            model=self.external_model_var.get()
                        )
                    
                    result = api_provider.test_connection()
                    self.after(0, lambda: self._show_test_result(result))
                    
                except Exception as e:
                    logger.error(f"Test connection error: {e}")
                    self.after(0, lambda: self._show_test_result({
                        "success": False,
                        "provider": provider,
                        "error": str(e)
                    }))
            
            import threading
            thread = threading.Thread(target=test_api, daemon=True)
            thread.start()
    
    def _show_test_result(self, result: dict):
        """接続テスト結果を表示"""
        self.test_connection_button.config(state="normal", text=tr("Test Connection"))
        
        if result["success"]:
            # 表示用のプロバイダー名を取得
            display_provider = result["provider"]
            if display_provider == "Ollama":
                display_provider = "Ollama/LM Studio"
                
            if result["provider"] == "Ollama":
                models = result.get("available_models", [])
                model_info = f"\nModels: {len(models)}" if models else "\nNo models found"
                messagebox.showinfo(
                    tr("Success"), 
                    f"Connected to {display_provider} successfully!{model_info}"
                )
            else:
                messagebox.showinfo(
                    tr("Success"), 
                    f"Connected to {display_provider} successfully!"
                )
        else:
            # 表示用のプロバイダー名を取得
            display_provider = result.get("provider", provider)
            if display_provider == "Ollama":
                display_provider = "Ollama/LM Studio"
                
            messagebox.showerror(
                tr("Error"), 
                f"Failed to connect to {display_provider}: {result.get('error', 'Unknown error')}"
            )
    
    def _edit_custom_prompt(self):
        """カスタムプロンプトを編集"""
        from .custom_prompt_dialog import CustomPromptDialog
        current_prompt = self.workbench.get_option("llm.custom_prompt", "")
        dialog = CustomPromptDialog(self, current_prompt)
        self.wait_window(dialog)
        
        if hasattr(dialog, 'result'):
            self.custom_prompt = dialog.result
            self.prompt_type_var.set("custom")
    
    def _load_settings(self):
        """設定を読み込む"""
        # 基本設定
        provider = self.workbench.get_option("llm.provider", "local")
        # ollamaの場合は表示用にollama/lmstudioに変換
        if provider == "ollama":
            provider = "ollama/lmstudio"
        self.provider_var.set(provider)
        self.model_path_var.set(self.workbench.get_option("llm.model_path", ""))
        self.output_language_var.set(self.workbench.get_option("llm.output_language", "auto"))
        self.skill_level_var.set(self.workbench.get_option("llm.skill_level", "beginner"))
        
        # 生成設定
        self.temperature_var.set(self.workbench.get_option("llm.temperature", 0.3))
        self.max_tokens_var.set(self.workbench.get_option("llm.max_tokens", 2048))
        self.context_size_var.set(self.workbench.get_option("llm.context_size", 4096))
        self.repeat_penalty_var.set(self.workbench.get_option("llm.repeat_penalty", 1.1))
        
        # 詳細設定
        # プロバイダーに応じて適切なAPIキーを読み込む
        provider = self.provider_var.get()
        if provider == "chatgpt":
            self.api_key_var.set(self.workbench.get_option("llm.chatgpt_api_key", ""))
        elif provider == "openrouter":
            self.api_key_var.set(self.workbench.get_option("llm.openrouter_api_key", ""))
        else:
            self.api_key_var.set("")
            
        base_url = self.workbench.get_option("llm.base_url", "http://localhost:11434")
        self.base_url_var.set(base_url)
        
        # Base URLからHost/Portを抽出
        try:
            if base_url.startswith("http://"):
                url_part = base_url[7:]  # "http://"を除去
            elif base_url.startswith("https://"):
                url_part = base_url[8:]  # "https://"を除去
            else:
                url_part = base_url
            
            if ":" in url_part:
                host, port = url_part.split(":", 1)
                # ポート番号の後にパスがある場合は除去
                if "/" in port:
                    port = port.split("/")[0]
                self.ollama_host_var.set(host)
                self.ollama_port_var.set(port)
            else:
                self.ollama_host_var.set(url_part)
                self.ollama_port_var.set("11434")
        except Exception as e:
            logger.error(f"Error parsing base URL: {e}")
            self.ollama_host_var.set("localhost")
            self.ollama_port_var.set("11434")
        
        self.external_model_var.set(self.workbench.get_option("llm.external_model", "gpt-4o-mini"))
        self.prompt_type_var.set(self.workbench.get_option("llm.prompt_type", "default"))
        
        # カスタムプロンプト
        self.custom_prompt = self.workbench.get_option("llm.custom_prompt", "")
        
        # UI更新
        self._update_language_label()
        self._update_skill_label()
        self._update_model_filename_label()
        self.temp_label.config(text=f"{self.temperature_var.get():.1f}")
        self.repeat_label.config(text=f"{self.repeat_penalty_var.get():.2f}")
    
    def _save_settings(self):
        """設定を保存"""
        # 検証
        provider = self.provider_var.get()
        
        # 保存時はollama/lmstudioをollamaとして保存
        save_provider = provider
        if provider == "ollama/lmstudio":
            save_provider = "ollama"
        
        if provider == "local":
            model_path = self.model_path_var.get()
            if model_path and not Path(model_path).exists():
                messagebox.showerror(tr("Error"), tr("Model file does not exist!"))
                return
        else:
            # 外部プロバイダーの検証
            if provider in ["chatgpt", "openrouter"] and not self.api_key_var.get():
                messagebox.showerror(tr("Error"), tr("API key is required for {}").format(provider))
                return
        
        # 保存
        self.workbench.set_option("llm.provider", save_provider)
        self.workbench.set_option("llm.model_path", self.model_path_var.get())
        self.workbench.set_option("llm.output_language", self.output_language_var.get())
        self.workbench.set_option("llm.skill_level", self.skill_level_var.get())
        
        self.workbench.set_option("llm.temperature", self.temperature_var.get())
        self.workbench.set_option("llm.max_tokens", self.max_tokens_var.get())
        self.workbench.set_option("llm.context_size", self.context_size_var.get())
        self.workbench.set_option("llm.repeat_penalty", self.repeat_penalty_var.get())
        
        # プロバイダーに応じて適切なAPIキーを保存
        if provider == "chatgpt":
            self.workbench.set_option("llm.chatgpt_api_key", self.api_key_var.get())
        elif provider == "openrouter":
            self.workbench.set_option("llm.openrouter_api_key", self.api_key_var.get())
            
        self.workbench.set_option("llm.base_url", self.base_url_var.get())
        self.workbench.set_option("llm.external_model", self.external_model_var.get())
        self.workbench.set_option("llm.prompt_type", self.prompt_type_var.get())
        
        if hasattr(self, 'custom_prompt'):
            self.workbench.set_option("llm.custom_prompt", self.custom_prompt)
        
        self.settings_changed = True
        self.destroy()
    
    def _fetch_ollama_models(self):
        """Ollamaからモデルリストを取得"""
        try:
            # 現在の設定を一時的に保存
            current_model = self.external_model_var.get()
            
            # ボタンを無効化
            self.refresh_ollama_button.config(state="disabled", text=tr("Loading..."))
            
            # OllamaProviderを使ってモデルを取得
            from ..external_providers import OllamaProvider
            base_url = self.base_url_var.get()
            
            # バックグラウンドで取得
            def fetch_models():
                try:
                    provider = OllamaProvider(base_url=base_url)
                    models = provider.get_models()
                    
                    # UIスレッドで更新
                    self.after(0, lambda: self._update_ollama_models(models, current_model))
                except Exception as e:
                    logger.error(f"Failed to fetch Ollama models: {e}")
                    self.after(0, lambda: self._update_ollama_models([], current_model, error=str(e)))
            
            import threading
            thread = threading.Thread(target=fetch_models, daemon=True)
            thread.start()
            
        except Exception as e:
            logger.error(f"Error in _fetch_ollama_models: {e}")
            messagebox.showerror(tr("Error"), tr("Failed to fetch models: {}").format(str(e)))
            self.refresh_ollama_button.config(state="normal", text=tr("Refresh"))
    
    def _update_ollama_models(self, models: list, current_model: str, error: Optional[str] = None):
        """Ollamaモデルリストを更新"""
        try:
            # ボタンを有効化
            self.refresh_ollama_button.config(state="normal", text=tr("Refresh"))
            
            if error:
                # 初期化中でなければエラーを表示
                if hasattr(self, '_initialization_complete'):
                    messagebox.showerror(tr("Error"), tr("Failed to connect to Ollama: {}").format(error))
                else:
                    logger.warning(f"Failed to connect to Ollama during initialization: {error}")
                self.external_model_combo['values'] = []
                return
            
            if not models:
                # モデルがない場合
                if hasattr(self, '_initialization_complete'):
                    messagebox.showwarning(
                        tr("No Models"), 
                        tr("No models found in Ollama. Please pull a model first using 'ollama pull <model>'")
                    )
                self.external_model_combo['values'] = []
                return
            
            # モデルリストを更新
            self.external_model_combo['values'] = models
            
            # 現在のモデルがリストにある場合は選択を維持
            if current_model in models:
                self.external_model_var.set(current_model)
            else:
                # ない場合は最初のモデルを選択
                self.external_model_var.set(models[0])
                
        except Exception as e:
            logger.error(f"Error updating Ollama models: {e}")
    
    def _set_ollama_defaults(self):
        """Ollamaのデフォルト設定を適用"""
        self.ollama_host_var.set("localhost")
        self.ollama_port_var.set("11434")
        # モデルリストを再取得
        self._fetch_ollama_models()
    
    def _set_lmstudio_defaults(self):
        """LM Studioのデフォルト設定を適用"""
        self.ollama_host_var.set("localhost")
        self.ollama_port_var.set("1234")
        # モデルリストを再取得
        self._fetch_ollama_models()
    
    def _update_model_filename_label(self, *args):
        """モデルファイル名ラベルを更新"""
        try:
            path = self.model_path_var.get().strip()
            if path:
                # パスからファイル名を抽出
                filename = Path(path).name
                # ファイルサイズも表示（存在する場合）
                if Path(path).exists():
                    size_bytes = Path(path).stat().st_size
                    # サイズを人間が読みやすい形式に変換
                    if size_bytes < 1024:
                        size_str = f"{size_bytes} B"
                    elif size_bytes < 1024 * 1024:
                        size_str = f"{size_bytes / 1024:.1f} KB"
                    elif size_bytes < 1024 * 1024 * 1024:
                        size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
                    else:
                        size_str = f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
                    
                    self.model_filename_label.config(
                        text=f"📄 {filename} ({size_str})",
                        foreground="blue"
                    )
                else:
                    self.model_filename_label.config(
                        text=f"⚠️ {filename} " + tr("(File not found)"),
                        foreground="red"
                    )
            else:
                self.model_filename_label.config(text="", foreground="gray")
        except Exception as e:
            logger.error(f"Error updating filename label: {e}")
            self.model_filename_label.config(text="", foreground="gray")
    
    def _update_base_url_from_host_port(self, *args):
        """Host/PortからBase URLを更新"""
        try:
            host = self.ollama_host_var.get().strip()
            port = self.ollama_port_var.get().strip()
            
            if host and port:
                # Base URLを構築
                self.base_url_var.set(f"http://{host}:{port}")
        except Exception as e:
            logger.error(f"Error updating base URL: {e}")
    
    def _on_base_url_changed(self, *args):
        """Base URLが変更された時の処理"""
        # Ollama/LM Studioが選択されている場合のみ
        if self.provider_var.get() in ["ollama", "ollama/lmstudio"]:
            # タイマーをリセット（連続入力に対応）
            if hasattr(self, '_base_url_timer'):
                self.after_cancel(self._base_url_timer)
            # 500ms後にモデルを取得
            self._base_url_timer = self.after(500, self._fetch_ollama_models)
    
    def _create_tooltip(self, widget, text):
        """ツールチップを作成"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = ttk.Label(tooltip, text=text, relief="solid", borderwidth=1)
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def _create_dynamic_tooltip(self, widget):
        """エントリーフィールドの内容を表示する動的ツールチップを作成"""
        def on_enter(event):
            # エントリーの内容を取得
            if hasattr(widget, 'get'):
                text = widget.get()
                if text:
                    tooltip = tk.Toplevel()
                    tooltip.wm_overrideredirect(True)
                    tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                    label = ttk.Label(tooltip, text=text, relief="solid", borderwidth=1)
                    label.pack()
                    widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)