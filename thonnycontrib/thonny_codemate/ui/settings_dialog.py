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
        self.geometry("700x750")  # 固定サイズ
        self.resizable(False, False)  # リサイズ無効化
        
        # モーダルダイアログ
        self.transient(parent)
        
        self.workbench = get_workbench()
        self.settings_changed = False
        
        # メインコンテナ
        main_container = ttk.Frame(self, padding="10")
        main_container.pack(fill="both", expand=True)
        
        # スクロール可能な領域を作成
        canvas = tk.Canvas(main_container, highlightthickness=0, width=680)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # ウィンドウを作成時に幅を指定
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=680)
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
            padding="10",
            width=650
        )
        basic_frame.pack(fill="x", padx=5, pady=5)
        
        # グリッドの重み設定（第1列を拡張可能に）
        basic_frame.grid_columnconfigure(1, weight=1)
        
        # Provider
        ttk.Label(basic_frame, text=tr("Provider:")).grid(row=0, column=0, sticky="w", pady=5)
        self.provider_var = tk.StringVar(value="local")
        self.provider_combo = ttk.Combobox(
            basic_frame,
            textvariable=self.provider_var,
            values=["local", "chatgpt", "ollama/lmstudio", "openrouter"],
            state="readonly"
        )
        self.provider_combo.grid(row=0, column=1, sticky="ew", pady=5)
        self.provider_combo.bind("<<ComboboxSelected>>", self._on_provider_changed)
        
        # Model/API Key（動的に切り替え）
        # 固定サイズのコンテナフレームを作成
        self.model_container = ttk.Frame(basic_frame)
        self.model_container.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)
        
        # 実際のコンテンツフレーム
        self.model_frame = ttk.Frame(self.model_container)
        self.model_frame.pack(fill="both", expand=True)
        
        # ローカルモデル用
        self.local_model_frame = ttk.Frame(self.model_frame)
        
        # 上部のパス入力部分
        path_frame = ttk.Frame(self.local_model_frame)
        path_frame.pack(fill="x")
        
        ttk.Label(path_frame, text=tr("Model:")).pack(side="left", padx=(0, 10))
        self.model_path_var = tk.StringVar()
        self.model_path_entry = ttk.Entry(
            path_frame,
            textvariable=self.model_path_var
        )
        self.model_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # エントリーフィールドのツールチップ設定
        self._create_tooltip(self.model_path_entry, dynamic=True)
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
        
        # モデルダウンロードボタン（ローカルモデル用）
        download_frame = ttk.Frame(self.local_model_frame)
        download_frame.pack(fill="x", pady=(5, 0))
        
        self.download_models_button = ttk.Button(
            download_frame,
            text=tr("Download Models"),
            command=self._show_model_manager,
            width=15
        )
        self.download_models_button.pack(side="left", padx=(60, 0))
        
        # 外部API用
        self.api_frame = ttk.Frame(self.model_frame)
        
        # API Key
        self.api_key_frame = ttk.Frame(self.api_frame)
        ttk.Label(self.api_key_frame, text=tr("API Key:")).pack(side="left", padx=(0, 10))
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(
            self.api_key_frame,
            textvariable=self.api_key_var,
            show="*"
        )
        self.api_key_entry.pack(side="left", fill="x", expand=True)
        
        # Ollama/LM Studio Server設定 (Basic Settingsに移動)
        self.ollama_server_frame = ttk.Frame(self.api_frame)
        ttk.Label(self.ollama_server_frame, text=tr("Server:")).pack(side="left", padx=(0, 10))
        
        # IP/Host
        ttk.Label(self.ollama_server_frame, text=tr("Host:")).pack(side="left", padx=(0, 5))
        self.ollama_host_var = tk.StringVar(value="localhost")
        self.ollama_host_entry = ttk.Entry(
            self.ollama_server_frame,
            textvariable=self.ollama_host_var
        )
        self.ollama_host_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
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
            width=10
        ).pack(side="left", padx=(0, 5))
        
        # LM Studioプリセットボタン
        ttk.Button(
            preset_frame,
            text="LM Studio",
            command=lambda: self._set_lmstudio_defaults(),
            width=10
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
            state="readonly"
        )
        
        # Ollama用エントリー（削除予定、互換性のために残す）
        self.external_model_entry = ttk.Entry(
            self.model_name_frame,
            textvariable=self.external_model_var
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
            state="readonly"
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
            state="readonly"
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
            padding="10",
            width=650
        )
        generation_frame.pack(fill="x", padx=5, pady=5)
        
        gen_frame = generation_frame
        
        # Temperature
        temp_frame = ttk.Frame(gen_frame)
        temp_frame.pack(fill="x", pady=5)
        
        # Temperature行の要素が均等に配置されるようにスペーサーを追加
        temp_spacer_frame = ttk.Frame(temp_frame)
        temp_spacer_frame.pack(side="right", padx=(10, 0))
        
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
            variable=self.temperature_var
        )
        temp_scale.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.temp_label = ttk.Label(temp_frame, text="0.7")
        self.temp_label.pack(side="left")
        
        def update_temp_label(value):
            self.temp_label.config(text=f"{float(value):.1f}")
        temp_scale.config(command=update_temp_label)
        
        # Max Tokens
        tokens_frame = ttk.Frame(gen_frame)
        tokens_frame.pack(fill="x", pady=5)
        
        ttk.Label(tokens_frame, text=tr("Max Tokens:")).pack(side="left", padx=(0, 10))
        
        # Max Tokensの説明ツールチップ
        tokens_help = ttk.Label(tokens_frame, text="(?)", foreground="blue", cursor="hand2")
        tokens_help.pack(side="left", padx=(0, 10))
        self._create_tooltip(tokens_help, tr("Maximum number of tokens the model will generate in one response"))
        
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
        
        # 自動設定ボタンを追加
        auto_context_button = ttk.Button(
            context_frame,
            text=tr("Auto"),
            command=self._auto_set_context_size,
            width=8
        )
        auto_context_button.pack(side="left", padx=(10, 0))
        
        # Repeat Penalty
        repeat_frame = ttk.Frame(gen_frame)
        repeat_frame.pack(fill="x", pady=5)
        
        # Repeat Penalty行の要素が均等に配置されるようにスペーサーを追加
        repeat_spacer_frame = ttk.Frame(repeat_frame)
        repeat_spacer_frame.pack(side="right", padx=(10, 0))
        
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
            variable=self.repeat_penalty_var
        )
        repeat_scale.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
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
            padding="10",
            width=650
        )
        advanced_frame.pack(fill="x", padx=5, pady=5)
        
        adv_frame = advanced_frame
        
        # Base URL (内部用、非表示)
        self.base_url_var = tk.StringVar(value="http://localhost:11434")
        
        # Base URLが変更された時の処理は削除（手動でRefreshボタンを押してもらう）
        
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
                self.external_model_combo.pack(side="left", fill="x", expand=True)
                
                # モデルリストを更新
                from ..utils.constants import ProviderConstants
                models = ProviderConstants.PROVIDER_MODELS.get(provider, [])
                
                self.external_model_combo['values'] = models
                if self.external_model_var.get() not in models:
                    self.external_model_var.set(models[0])
            
            elif provider == "ollama":
                # サーバー設定を表示
                self.ollama_server_frame.pack(fill="both", expand=True, pady=2)
                self.model_name_frame.pack(fill="x", pady=2)
                
                # Ollamaの場合もコンボボックスを使用
                self.external_model_entry.pack_forget()
                self.external_model_combo.pack(side="left", fill="x", expand=True)
                
                # リフレッシュボタンを表示
                self.refresh_ollama_button.pack(side="left", padx=(5, 0))
                
                # 初回は手動でRefreshボタンを押してもらう
                self.external_model_combo['values'] = []
                self.external_model_var.set("")
    
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
                    import traceback
                    error_details = traceback.format_exc()
                    logger.error(f"Test connection error: {e}\n{error_details}")
                    
                    # ユーザーフレンドリーなエラーメッセージ
                    from ..utils.error_messages import format_api_error
                    user_error = format_api_error(provider, e)
                    
                    self.after(0, lambda: self._show_test_result({
                        "success": False,
                        "provider": provider,
                        "error": user_error
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
            display_provider = result.get("provider", "Unknown")
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
        from ..utils.constants import ProviderConstants
        api_key_option = ProviderConstants.API_KEY_OPTIONS.get(provider)
        if api_key_option:
            self.api_key_var.set(self.workbench.get_option(api_key_option, ""))
        else:
            self.api_key_var.set("")
            
        base_url = self.workbench.get_option("llm.base_url", "http://localhost:11434")
        self.base_url_var.set(base_url)
        
        # Base URLからHost/Portを抽出（urllib.parseを使用して安全に解析）
        try:
            from urllib.parse import urlparse
            
            parsed = urlparse(base_url)
            
            # ホスト名の取得
            host = parsed.hostname or "localhost"
            self.ollama_host_var.set(host)
            
            # ポート番号の取得
            if parsed.port:
                self.ollama_port_var.set(str(parsed.port))
            else:
                # デフォルトポート
                if base_url.endswith(":1234") or ":1234/" in base_url:
                    self.ollama_port_var.set("1234")
                else:
                    self.ollama_port_var.set("11434")
                    
        except Exception as e:
            import traceback
            logger.error(f"Error parsing base URL: {e}\n{traceback.format_exc()}")
            logger.error(f"Failed to parse URL: {base_url}")
            # フォールバック値
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
        from ..utils.constants import ProviderConstants
        
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
        api_key_option = ProviderConstants.API_KEY_OPTIONS.get(provider)
        if api_key_option:
            self.workbench.set_option(api_key_option, self.api_key_var.get())
            
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
                except urllib.error.URLError as e:
                    import traceback
                    logger.error(f"Failed to connect to Ollama: {e}\n{traceback.format_exc()}")
                    error_msg = tr("Cannot connect to server. Please check if Ollama/LM Studio is running.")
                    self.after(0, lambda: self._update_ollama_models([], current_model, error=error_msg))
                except Exception as e:
                    import traceback
                    logger.error(f"Failed to fetch Ollama models: {e}\n{traceback.format_exc()}")
                    self.after(0, lambda: self._update_ollama_models([], current_model, error=str(e)))
            
            import threading
            thread = threading.Thread(target=fetch_models, daemon=True)
            thread.start()
            
        except Exception as e:
            import traceback
            logger.error(f"Error in _fetch_ollama_models: {e}\n{traceback.format_exc()}")
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
            import traceback
            logger.error(f"Error updating filename label: {e}\n{traceback.format_exc()}")
            logger.error(f"Path that caused error: {self.model_path_var.get()}")
            self.model_filename_label.config(text="", foreground="gray")
    
    def _update_base_url_from_host_port(self, *args):
        """Host/PortからBase URLを更新"""
        # 既に更新中の場合はスキップ（競合状態を防ぐ）
        if hasattr(self, '_updating_base_url') and self._updating_base_url:
            return
        
        self._updating_base_url = True
        try:
            host = self.ollama_host_var.get().strip()
            port = self.ollama_port_var.get().strip()
            
            if host and port:
                # Base URLを構築
                new_url = f"http://{host}:{port}"
                # 現在の値と異なる場合のみ更新
                if self.base_url_var.get() != new_url:
                    self.base_url_var.set(new_url)
        except Exception as e:
            import traceback
            logger.error(f"Error updating base URL: {e}\n{traceback.format_exc()}")
            logger.error(f"Host: {self.ollama_host_var.get()}, Port: {self.ollama_port_var.get()}")
        finally:
            self._updating_base_url = False
    
    def _on_base_url_changed(self, *args):
        """Base URLが変更された時の処理"""
        # Ollama/LM Studioが選択されている場合のみ
        if self.provider_var.get() in ["ollama", "ollama/lmstudio"]:
            # URLが変更されたらモデルリストをクリア
            self.external_model_combo['values'] = []
            self.external_model_var.set("")
    
    def _create_tooltip(self, widget, text=None, dynamic=False):
        """静的または動的なツールチップを作成
        
        Args:
            widget: ツールチップを追加するウィジェット
            text: 静的ツールチップのテキスト（dynamicがFalseの場合に使用）
            dynamic: Trueの場合、ウィジェットのget()メソッドから動的にテキストを取得
        """
        def on_enter(event):
            # ツールチップテキストを決定
            tooltip_text = None
            if dynamic and hasattr(widget, 'get'):
                tooltip_text = widget.get()
            else:
                tooltip_text = text
            
            # テキストがある場合のみツールチップを表示
            if tooltip_text:
                tooltip = tk.Toplevel()
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                label = ttk.Label(tooltip, text=tooltip_text, relief="solid", borderwidth=1)
                label.pack()
                widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    
    # _create_dynamic_tooltipは_create_tooltipに統合されたため削除
    
    def _get_model_max_context_size(self, provider: str, model_name: str = "") -> int:
        """モデルの最大コンテキストサイズを取得"""
        # ローカルモデルの場合
        if provider == "local":
            model_path = self.model_path_var.get()
            if not model_path:
                return 4096  # デフォルト値
            
            # GGUFファイルから直接メタデータを読み取る
            try:
                from llama_cpp import Llama, llama_model_n_ctx_train
                
                # モデルを最小限の設定で読み込む（n_ctx=0でGGUFのデフォルト値を使用）
                llm = Llama(model_path=model_path, n_ctx=0, verbose=False)
                
                # トレーニング時のコンテキスト長を取得
                n_ctx_train = llama_model_n_ctx_train(llm.model)
                logger.info(f"Found training context length in GGUF: {n_ctx_train}")
                return int(n_ctx_train)
                
            except ImportError:
                raise ImportError("llama_cpp not available. Please install or upgrade llama-cpp-python>=0.3.9: pip install 'llama-cpp-python>=0.3.9'")
            except Exception as e:
                raise Exception(f"Error reading GGUF metadata from {Path(model_path).name}: {str(e)}")
        
        # OpenAI API の場合
        elif provider == "openai":
            if not model_name:
                model_name = self.external_model_var.get()
            
            # ChatGPTプロバイダーからモデル情報を取得
            try:
                from ..external_providers import ChatGPTProvider
                chatgpt_provider = ChatGPTProvider(
                    api_key=self.api_key_var.get(),
                    model=model_name,
                    base_url=self.base_url_var.get() if hasattr(self, 'base_url_var') else None
                )
                
                model_info = chatgpt_provider.get_model_info(model_name)
                context_size = model_info.get("context_size")
                
                if context_size:
                    logger.info(f"Found context size from ChatGPT provider: {context_size}")
                    return int(context_size)
                else:
                    logger.warning(f"Could not get context size from ChatGPT provider: {model_info.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.warning(f"Error getting context size from ChatGPT provider: {e}")
            
            return 4096  # デフォルト
        
        # LM Studio / Ollama の場合
        elif provider in ["ollama", "ollama/lmstudio"]:
            if not model_name:
                model_name = self.external_model_var.get()
            
            # Ollama/LM Studio APIからモデル情報を取得
            try:
                from ..external_providers import OllamaProvider
                ollama_provider = OllamaProvider(
                    base_url=self.base_url_var.get(),
                    model=model_name
                )
                
                model_info = ollama_provider.get_model_info(model_name)
                context_size = model_info.get("context_size")
                
                # サーバータイプを判定してログメッセージを調整
                server_type = "LM Studio" if ":1234" in self.base_url_var.get() else "Ollama"
                
                if context_size:
                    logger.info(f"Found context size from {server_type} API: {context_size}")
                    return int(context_size)
                else:
                    logger.warning(f"Could not get context size from {server_type} API: {model_info.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.warning(f"Error getting context size from Ollama/LM Studio API: {e}")
            
            # フォールバック: モデル名からコンテキストサイズを推定
            model_lower = model_name.lower()
            
            if "llama" in model_lower:
                if "3.2" in model_lower or "3.1" in model_lower:
                    return 128000
                elif "3" in model_lower:
                    return 8192
                else:
                    return 4096
            elif "qwen" in model_lower:
                if "2.5" in model_lower:
                    return 32768
                else:
                    return 8192
            elif "gemma" in model_lower:
                return 8192
            elif "phi" in model_lower:
                return 4096
            elif "codellama" in model_lower:
                return 16384
            elif "mistral" in model_lower:
                return 32768
            elif "mixtral" in model_lower:
                return 32768
            else:
                return 4096  # デフォルト
        
        # OpenRouter の場合
        elif provider == "openrouter":
            if not model_name:
                model_name = self.external_model_var.get()
            
            # OpenRouter APIからモデル情報を取得
            try:
                from ..external_providers import OpenRouterProvider
                openrouter_provider = OpenRouterProvider(
                    api_key=self.api_key_var.get(),
                    model=model_name
                )
                
                model_info = openrouter_provider.get_model_info(model_name)
                context_size = model_info.get("context_size")
                
                if context_size:
                    logger.info(f"Found context size from OpenRouter API: {context_size}")
                    return int(context_size)
                else:
                    logger.warning(f"Could not get context size from OpenRouter API: {model_info.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.warning(f"Error getting context size from OpenRouter API: {e}")
            
            # フォールバック: デフォルト値
            return 4096
        
        return 4096  # デフォルト値
    
    def _auto_set_context_size(self):
        """現在の設定に基づいてコンテキストサイズを自動設定"""
        try:
            provider = self.provider_var.get()
            
            if provider == "local":
                model_path = self.model_path_var.get()
                if not model_path:
                    messagebox.showwarning(
                        tr("No Model Selected"),
                        tr("Please select a local model first.")
                    )
                    return
            elif provider in ["openai", "ollama", "ollama/lmstudio"]:
                model_name = self.external_model_var.get()
                if not model_name:
                    messagebox.showwarning(
                        tr("No Model Selected"),
                        tr("Please select a model first.")
                    )
                    return
            
            # 最大コンテキストサイズを取得
            max_context = self._get_model_max_context_size(provider)
            
            # 設定を更新
            self.context_size_var.set(max_context)
            
            # ユーザーに通知
            model_info = ""
            if provider == "local":
                model_info = Path(self.model_path_var.get()).name
            else:
                model_info = self.external_model_var.get()
            
            messagebox.showinfo(
                tr("Context Size Updated"),
                tr(f"Context size automatically set to {max_context:,} tokens for {model_info}")
            )
            
        except Exception as e:
            logger.error(f"Error in auto context size setting: {e}")
            messagebox.showerror(
                tr("Error"),
                tr(f"Failed to auto-set context size: {str(e)}")
            )