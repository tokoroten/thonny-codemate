"""
LLMチャットビュー
GitHub Copilot風の右側パネルUIを提供
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import logging
from pathlib import Path
from typing import Optional

from thonny import get_workbench

logger = logging.getLogger(__name__)


class LLMChatView(ttk.Frame):
    """
    LLMとのチャットインターフェースを提供するビュー
    Thonnyの右側に表示される
    """
    
    def __init__(self, master):
        super().__init__(master)
        
        self.llm_client = None
        self._init_ui()
        self._init_llm()
        
        # メッセージキュー（スレッド間通信用）
        self.message_queue = queue.Queue()
        self._processing = False
        
        # 定期的にキューをチェック
        self.after(100, self._process_queue)
    
    def _init_ui(self):
        """UIコンポーネントを初期化"""
        # メインコンテナ
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        # ヘッダー
        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        ttk.Label(header_frame, text="LLM Assistant", font=("", 12, "bold")).pack(side=tk.LEFT)
        
        # 設定ボタン
        self.settings_button = ttk.Button(
            header_frame,
            text="⚙",
            width=3,
            command=self._show_settings
        )
        self.settings_button.pack(side=tk.RIGHT, padx=2)
        
        # ステータスラベル
        self.status_label = ttk.Label(header_frame, text="Not loaded", foreground="gray")
        self.status_label.pack(side=tk.RIGHT, padx=5)
        
        # チャット表示エリア
        chat_frame = ttk.Frame(self)
        chat_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        chat_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)
        
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            width=40,
            height=20,
            font=("Consolas", 10),
            state=tk.DISABLED,
            background="#f8f8f8"
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew")
        
        # タグの設定
        self.chat_display.tag_config("user", foreground="#0066cc", font=("Consolas", 10, "bold"))
        self.chat_display.tag_config("assistant", foreground="#006600")
        self.chat_display.tag_config("error", foreground="#cc0000")
        self.chat_display.tag_config("code", background="#e8e8e8", font=("Consolas", 9))
        
        # 入力エリア
        input_frame = ttk.Frame(self)
        input_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        input_frame.columnconfigure(0, weight=1)
        
        # 入力テキスト
        self.input_text = tk.Text(
            input_frame,
            height=3,
            font=("Consolas", 10),
            wrap=tk.WORD
        )
        self.input_text.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        # ボタンフレーム
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=1, column=0, sticky="ew")
        
        self.send_button = ttk.Button(
            button_frame,
            text="Send",
            command=self._send_message,
            state=tk.DISABLED
        )
        self.send_button.pack(side=tk.RIGHT, padx=2)
        
        self.clear_button = ttk.Button(
            button_frame,
            text="Clear",
            command=self._clear_chat
        )
        self.clear_button.pack(side=tk.RIGHT, padx=2)
        
        # プリセットボタン
        ttk.Button(
            button_frame,
            text="Explain Error",
            command=self._explain_last_error
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame,
            text="Generate Code",
            command=self._show_code_generator
        ).pack(side=tk.LEFT, padx=2)
        
        # コンテキストボタン
        self.context_var = tk.BooleanVar(value=False)
        self.context_check = ttk.Checkbutton(
            button_frame,
            text="Include Context",
            variable=self.context_var,
            command=self._toggle_context
        )
        self.context_check.pack(side=tk.LEFT, padx=10)
        
        # コンテキストマネージャー
        self.context_manager = None
        
        # キーバインディング
        self.input_text.bind("<Control-Return>", lambda e: self._send_message())
        self.input_text.bind("<Shift-Return>", lambda e: "break")  # 改行を許可
    
    def _init_llm(self):
        """LLMクライアントを初期化"""
        try:
            from .. import get_llm_client
            from ..model_manager import ModelManager
            
            self.llm_client = get_llm_client()
            
            workbench = get_workbench()
            provider = workbench.get_option("llm.provider", "local")
            
            if provider == "local":
                # ローカルモデルの場合
                model_path = workbench.get_option("llm.model_path", "")
                
                if not model_path or not Path(model_path).exists():
                    # モデルがない場合、利用可能なモデルをチェック
                    manager = ModelManager()
                    available_model = manager.get_model_path("explanation") or manager.get_model_path("coding")
                    
                    if available_model:
                        # 利用可能なモデルがある場合は自動設定
                        workbench.set_option("llm.model_path", available_model)
                        model_path = available_model
                    else:
                        # モデルがない場合はダウンロードを促す
                        self.status_label.config(text="No model", foreground="red")
                        self._append_message(
                            "System",
                            "No model found. Please download a model from Settings → Download Models.",
                            "error"
                        )
                        
                        # 設定ダイアログを開くボタンを表示
                        # 親ウィンドウを指定してダイアログを表示
                        if messagebox.askyesno(
                            "No Model Found",
                            "No LLM model found. Would you like to download recommended models?",
                            parent=self
                        ):
                            self._show_settings()
                        return
                
                # 非同期でモデルをロード
                self.status_label.config(text="Loading model...", foreground="orange")
                self.llm_client.load_model_async(callback=self._on_model_loaded)
            else:
                # 外部プロバイダーの場合
                self.status_label.config(text=f"Using {provider}", foreground="blue")
                # config取得で外部プロバイダーが設定される
                self.llm_client.get_config()
                self.send_button.config(state=tk.NORMAL)
                self._append_message(
                    "System", 
                    f"Connected to {provider.upper()} API. Ready to chat!",
                    "assistant"
                )
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            self.status_label.config(text="Error", foreground="red")
            self._append_message("System", f"Failed to initialize LLM: {str(e)}", "error")
    
    def _on_model_loaded(self, success: bool, error: Optional[Exception]):
        """モデル読み込み完了時のコールバック"""
        def update_ui():
            if success:
                self.status_label.config(text="Ready", foreground="green")
                self.send_button.config(state=tk.NORMAL)
                self._append_message("System", "LLM model loaded successfully!", "assistant")
            else:
                self.status_label.config(text="Load failed", foreground="red")
                self._append_message("System", f"Failed to load model: {error}", "error")
        
        # UIスレッドで更新
        self.after(0, update_ui)
    
    def _append_message(self, sender: str, message: str, tag: str = None):
        """チャット表示にメッセージを追加"""
        self.chat_display.config(state=tk.NORMAL)
        
        # 送信者を表示
        self.chat_display.insert(tk.END, f"\n{sender}: ", tag or "user")
        
        # メッセージを表示
        if tag == "code" or "```" in message:
            # コードブロックを検出して整形
            parts = message.split("```")
            for i, part in enumerate(parts):
                if i % 2 == 0:
                    self.chat_display.insert(tk.END, part, tag or "assistant")
                else:
                    # コードブロック
                    lines = part.split('\n')
                    if lines[0]:  # 言語指定がある場合
                        self.chat_display.insert(tk.END, f"\n[{lines[0]}]\n", "assistant")
                        code = '\n'.join(lines[1:])
                    else:
                        code = part
                    self.chat_display.insert(tk.END, code, "code")
        else:
            self.chat_display.insert(tk.END, message, tag or "assistant")
        
        self.chat_display.insert(tk.END, "\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def _send_message(self):
        """メッセージを送信"""
        message = self.input_text.get("1.0", tk.END).strip()
        if not message or self._processing:
            return
        
        # UIをクリア
        self.input_text.delete("1.0", tk.END)
        self._append_message("You", message, "user")
        
        # 処理中フラグ
        self._processing = True
        self.send_button.config(state=tk.DISABLED)
        
        # バックグラウンドで処理
        thread = threading.Thread(
            target=self._generate_response,
            args=(message,),
            daemon=True
        )
        thread.start()
    
    def _generate_response(self, message: str):
        """バックグラウンドで応答を生成"""
        try:
            # コンテキストを含める場合
            if self.context_var.get() and self.context_manager:
                contexts = self.context_manager.get_project_context()
                if contexts:
                    context_str = self.context_manager.format_context_for_llm(contexts)
                    # コンテキストサマリーをUIに表示
                    summary = self.context_manager.get_context_summary()
                    self.message_queue.put(("info", f"Using context from {summary['total_files']} files"))
                    
                    # コンテキスト付きで生成
                    full_prompt = f"""Here is the context from the current project:

{context_str}

Based on this context, {message}"""
                    
                    for token in self.llm_client.generate_stream(full_prompt):
                        self.message_queue.put(("token", token))
                else:
                    # 通常の生成
                    for token in self.llm_client.generate_stream(message):
                        self.message_queue.put(("token", token))
            else:
                # 通常の生成
                for token in self.llm_client.generate_stream(message):
                    self.message_queue.put(("token", token))
            
            # 完了
            self.message_queue.put(("complete", None))
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            self.message_queue.put(("error", str(e)))
    
    def _process_queue(self):
        """メッセージキューを処理"""
        try:
            # キューから全てのメッセージを処理
            first_token = True
            while True:
                msg_type, content = self.message_queue.get_nowait()
                
                if msg_type == "token":
                    if first_token:
                        self._append_message("Assistant", "", "assistant")
                        first_token = False
                    
                    # トークンを追加
                    self.chat_display.config(state=tk.NORMAL)
                    self.chat_display.insert(tk.END, content, "assistant")
                    self.chat_display.see(tk.END)
                    self.chat_display.config(state=tk.DISABLED)
                
                elif msg_type == "complete":
                    self._processing = False
                    self.send_button.config(state=tk.NORMAL)
                    first_token = True
                
                elif msg_type == "error":
                    self._append_message("System", f"Error: {content}", "error")
                    self._processing = False
                    self.send_button.config(state=tk.NORMAL)
                    first_token = True
                
                elif msg_type == "info":
                    self._append_message("System", content, "assistant")
                    first_token = True
        
        except queue.Empty:
            pass
        
        # 次のチェックをスケジュール
        self.after(50, self._process_queue)
    
    def explain_code(self, code: str):
        """コードを説明（外部から呼ばれる）"""
        # 現在のスキルレベルを取得
        workbench = get_workbench()
        skill_level = workbench.get_option("llm.skill_level", "beginner")
        
        # メッセージを作成
        message = f"Please explain this code:\n```python\n{code}\n```"
        
        # 入力欄に設定して送信
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert("1.0", message)
        self._send_message()
    
    def _explain_last_error(self):
        """最後のエラーを説明"""
        try:
            # シェルビューを取得
            shell_view = get_workbench().get_view("ShellView")
            if not shell_view:
                messagebox.showinfo("No Shell", "Shell view not found.")
                return
            
            # シェルのテキストウィジェットを取得
            shell_text = shell_view.text
            
            # シェルの内容を取得（最後の部分）
            shell_content = shell_text.get("1.0", tk.END)
            lines = shell_content.strip().split('\n')
            
            # エラーを探す（後ろから検索）
            error_lines = []
            error_found = False
            
            for i in range(len(lines) - 1, -1, -1):
                line = lines[i]
                
                # エラーの終わりを検出
                if error_found and (line.startswith(">>>") or line.startswith("===") or not line.strip()):
                    break
                
                # エラーパターンを検出
                if any(error_type in line for error_type in ["Error", "Exception", "Traceback"]):
                    error_found = True
                
                if error_found:
                    error_lines.insert(0, line)
            
            if not error_lines:
                messagebox.showinfo("No Error", "No recent error found in shell.")
                return
            
            # エラーメッセージを結合
            error_message = '\n'.join(error_lines)
            
            # 関連するコードも取得（エディタから）
            code = ""
            editor = get_workbench().get_editor_notebook().get_current_editor()
            if editor:
                try:
                    code = editor.get_text_widget().get("1.0", tk.END).strip()
                except:
                    pass
            
            # プロンプトを作成
            if code:
                prompt = f"I encountered this error:\n```\n{error_message}\n```\n\nIn this code:\n```python\n{code}\n```\n\nPlease explain what causes this error and how to fix it."
            else:
                prompt = f"I encountered this error:\n```\n{error_message}\n```\n\nPlease explain what causes this error and provide a solution."
            
            # 入力欄に設定して送信
            self.input_text.delete("1.0", tk.END)
            self.input_text.insert("1.0", prompt)
            self._send_message()
            
        except Exception as e:
            logger.error(f"Error in _explain_last_error: {e}")
            messagebox.showerror("Error", f"Failed to get error information: {str(e)}")
    
    def _show_code_generator(self):
        """コード生成ダイアログを表示"""
        # 簡単なプロンプト入力ダイアログ
        dialog = tk.Toplevel(self)
        dialog.title("Generate Code")
        dialog.geometry("400x200")
        
        ttk.Label(dialog, text="What code do you want to generate?").pack(pady=5)
        
        prompt_text = tk.Text(dialog, height=5, width=50)
        prompt_text.pack(padx=10, pady=5)
        prompt_text.insert("1.0", "# Write a function that ")
        
        def generate():
            prompt = prompt_text.get("1.0", tk.END).strip()
            if prompt:
                self.input_text.delete("1.0", tk.END)
                self.input_text.insert("1.0", f"Generate Python code for: {prompt}")
                self._send_message()
            dialog.destroy()
        
        ttk.Button(dialog, text="Generate", command=generate).pack(pady=5)
    
    def _show_settings(self):
        """設定ダイアログを表示"""
        from .settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.grab_set()
        self.wait_window(dialog)
        
        # 設定が変更された可能性があるので再初期化
        if hasattr(dialog, 'settings_changed') and dialog.settings_changed:
            self._init_llm()
    
    def _clear_chat(self):
        """チャットをクリア"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def _toggle_context(self):
        """コンテキストの有効/無効を切り替え"""
        if self.context_var.get():
            # コンテキストマネージャーを初期化
            if not self.context_manager:
                from ..context_manager import ContextManager
                self.context_manager = ContextManager()
            
            # コンテキストサマリーを表示
            summary = self.context_manager.get_context_summary()
            if summary['current_file']:
                self._append_message(
                    "System",
                    f"Context enabled: {summary['total_files']} files, "
                    f"{summary['total_classes']} classes, {summary['total_functions']} functions",
                    "assistant"
                )
        else:
            self._append_message("System", "Context disabled", "assistant")