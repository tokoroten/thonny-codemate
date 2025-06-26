"""
LLMチャットビュー（HTML版）
tkinterwebを使用してMarkdown表示と対話機能を提供
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import logging
import time
import json
from pathlib import Path
from typing import Optional, List, Tuple

try:
    from tkinterweb import HtmlFrame
except ImportError:
    HtmlFrame = None

from thonny import get_workbench

# 安全なロガーを使用
try:
    from .. import get_safe_logger
    logger = get_safe_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.NullHandler())

from .markdown_renderer import MarkdownRenderer
from ..i18n import tr


class LLMChatViewHTML(ttk.Frame):
    """
    HTMLベースのLLMチャットインターフェース
    Markdownレンダリングと対話機能を提供
    """
    
    def __init__(self, master):
        super().__init__(master)
        
        # tkinterwebが利用可能かチェック
        if HtmlFrame is None:
            self._show_fallback_ui()
            return
        
        self.llm_client = None
        self.markdown_renderer = MarkdownRenderer()
        self.messages: List[Tuple[str, str]] = []  # [(sender, text), ...]
        
        # メッセージキュー（スレッド間通信用）
        self.message_queue = queue.Queue()
        self._processing = False
        self._current_message = ""  # ストリーミング中のメッセージ
        self._stop_generation = False
        
        self._init_ui()
        self._init_llm()
        
        # 定期的にキューをチェック
        self._queue_check_id = self.after(100, self._process_queue)
        
        # ウィンドウ閉じるイベントをバインド
        self.bind("<Destroy>", self._on_destroy)
        
        # 最後の更新時刻（レート制限用）
        self._last_update_time = 0
        self._update_pending = False
        
        # 会話履歴を読み込む
        self._load_chat_history()
    
    def _show_fallback_ui(self):
        """tkinterwebが利用できない場合のフォールバックUI"""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, padx=20, pady=20)
        
        ttk.Label(
            frame,
            text="tkinterweb is not installed",
            font=("", 12, "bold")
        ).pack(pady=10)
        
        ttk.Label(
            frame,
            text="To enable Markdown rendering and interactive features,\n"
                 "please install tkinterweb:\n\n"
                 "pip install tkinterweb",
            justify=tk.CENTER
        ).pack(pady=10)
        
        ttk.Button(
            frame,
            text="Use Text-Only Version",
            command=self._switch_to_text_view
        ).pack(pady=10)
    
    def _switch_to_text_view(self):
        """テキスト版のチャットビューに切り替え"""
        # 親ウィジェットを取得してビューを切り替え
        workbench = get_workbench()
        # 現在のビューを閉じて、テキスト版を開く
        workbench.show_view("LLMChatView")
    
    def _init_ui(self):
        """UIコンポーネントを初期化"""
        # メインコンテナ
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        # ヘッダー
        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        ttk.Label(header_frame, text=tr("LLM Assistant"), font=("", 12, "bold")).pack(side=tk.LEFT)
        
        # Clearボタン
        self.clear_button = ttk.Button(
            header_frame,
            text=tr("Clear"),
            command=self._clear_chat,
            width=8
        )
        self.clear_button.pack(side=tk.LEFT, padx=10)
        
        # 設定ボタン
        self.settings_button = ttk.Button(
            header_frame,
            text="⚙",
            width=3,
            command=self._show_settings
        )
        self.settings_button.pack(side=tk.RIGHT, padx=2)
        
        # ステータスフレーム
        status_frame = ttk.Frame(header_frame)
        status_frame.pack(side=tk.RIGHT, padx=5)
        
        self.status_label = ttk.Label(status_frame, text=tr("No model loaded"), foreground="gray")
        self.status_label.pack(side=tk.RIGHT)
        
        # HTMLフレーム
        self.html_frame = HtmlFrame(self, messages_enabled=False)
        self.html_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # JavaScriptインターフェースを設定
        self._setup_js_interface()
        
        # URL変更のハンドラーを設定（Insert機能用）
        self.html_frame.on_url_change = self._handle_url_change
        
        # 初期HTMLを設定
        self._update_html()
        
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
        
        # Sendボタン
        self.send_button = ttk.Button(
            button_frame,
            text=tr("Send"),
            command=self._handle_send_button,
            state=tk.DISABLED
        )
        self.send_button.pack(side=tk.RIGHT, padx=2)
        
        # Ctrl+Enterのヒント
        hint_label = ttk.Label(
            button_frame,
            text=tr("Ctrl+Enter to send"),
            foreground="gray",
            font=("", 9)
        )
        hint_label.pack(side=tk.RIGHT, padx=5)
        
        # プリセットボタン
        ttk.Button(
            button_frame,
            text=tr("Explain Error"),
            command=self._explain_last_error,
            width=15
        ).pack(side=tk.LEFT, padx=2)
        
        # コンテキストボタン
        self.context_var = tk.BooleanVar(value=False)
        self.context_check = ttk.Checkbutton(
            button_frame,
            text=tr("Include Context"),
            variable=self.context_var,
            command=self._toggle_context
        )
        self.context_check.pack(side=tk.LEFT, padx=10)
        
        # コンテキストマネージャー
        self.context_manager = None
        
        # キーバインディング
        self.input_text.bind("<Control-Return>", lambda e: self._handle_send_button())
        self.input_text.bind("<Shift-Return>", lambda e: "break")
        
        # Escapeキーで生成を停止
        self.bind_all("<Escape>", lambda e: self._stop_if_processing())
    
    def _setup_js_interface(self):
        """JavaScriptとのインターフェースを設定"""
        # 現時点では、tkinterwebのJS連携機能が限定的なため、
        # コードの挿入機能は一時的に無効化します。
        # 将来的にはtkinterwebのアップデートに合わせて実装予定。
        pass
    
    def _handle_url_change(self, url):
        """URL変更を処理（Insert機能用）"""
        if url.startswith("thonny:insert:"):
            # コードを抽出
            encoded_code = url[14:]  # "thonny:insert:"の長さ
            import urllib.parse
            code = urllib.parse.unquote(encoded_code)
            
            # エディタに挿入
            workbench = get_workbench()
            editor = workbench.get_editor_notebook().get_current_editor()
            if editor:
                text_widget = editor.get_text_widget()
                text_widget.insert("insert", code)
                # フォーカスをエディタに戻す
                text_widget.focus_set()
            else:
                messagebox.showinfo("No Editor", "Please open a file in the editor first.")
            
            # URLを元に戻す（無限ループを防ぐ）
            return False  # ナビゲーションをキャンセル
    
    def _update_html(self):
        """HTMLコンテンツを更新"""
        # 前回のHTMLと比較して変更がある場合のみ更新
        html_content = self.markdown_renderer.get_full_html(self.messages)
        
        # HTMLを設定
        self.html_frame.load_html(html_content)
        
        # スクロールを最下部に（少し遅延を入れて確実に）
        self.after(100, self._scroll_to_bottom)
        self.after(300, self._scroll_to_bottom)  # 念のため2回目
    
    def _scroll_to_bottom(self):
        """HTMLフレームを最下部にスクロール"""
        try:
            # JavaScriptを実行してスクロール
            js_code = """
            window.scrollTo(0, document.body.scrollHeight);
            """
            self.html_frame.run_javascript(js_code)
            
        except Exception as e:
            logger.debug(f"Could not scroll to bottom: {e}")
    
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
                    # モデルがない場合
                    manager = ModelManager()
                    available_model = manager.get_model_path("llama3.2-1b") or manager.get_model_path("llama3.2-3b")
                    
                    if available_model:
                        workbench.set_option("llm.model_path", available_model)
                        model_path = available_model
                    else:
                        self.status_label.config(text=tr("No model loaded"), foreground="red")
                        self._add_message(
                            "system",
                            tr("No model found. Please download a model from Settings → Download Models.")
                        )
                        
                        if messagebox.askyesno(
                            "No Model Found",
                            "No LLM model found. Would you like to download recommended models?",
                            parent=self
                        ):
                            self._show_settings()
                        return
                
                # 非同期でモデルをロード
                model_name = Path(model_path).name if model_path else "model"
                self.status_label.config(text=f"{tr('Loading')} {model_name}...", foreground="orange")
                self.llm_client.load_model_async(callback=self._on_model_loaded)
            else:
                # 外部プロバイダーの場合
                external_model = workbench.get_option("llm.external_model", "")
                display_text = f"{external_model} ({provider})" if external_model else f"Using {provider}"
                self.status_label.config(text=display_text, foreground="blue")
                self.llm_client.get_config()
                self.send_button.config(state=tk.NORMAL)
                self._add_message(
                    "system",
                    f"Connected to {provider.upper()} API. Ready to chat!"
                )
        
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            self.status_label.config(text="Error loading model", foreground="red")
            self._add_message("system", f"Failed to initialize LLM: {str(e)}")
    
    def _on_model_loaded(self, success: bool, error: Optional[Exception]):
        """モデル読み込み完了時のコールバック"""
        def update_ui():
            if success:
                model_path = get_workbench().get_option("llm.model_path", "")
                model_name = Path(model_path).name if model_path else "Unknown"
                self.status_label.config(text=f"{model_name} | {tr('Ready')}", foreground="green")
                self.send_button.config(state=tk.NORMAL)
                self._add_message("system", "LLM model loaded successfully!")
            else:
                self.status_label.config(text=tr("Load failed"), foreground="red")
                self._add_message("system", f"{tr('Failed to load model:')} {error}")
        
        self.after(0, update_ui)
    
    def _add_message(self, sender: str, text: str):
        """メッセージを追加してHTMLを更新"""
        self.messages.append((sender, text))
        self._update_html()
        
        # ユーザーとアシスタントのメッセージのみ保存（システムメッセージは一時的なものが多いため）
        if sender in ["user", "assistant"]:
            self._save_chat_history()
    
    def _handle_send_button(self):
        """送信/停止ボタンのハンドラー"""
        if self._processing:
            self._stop_generation = True
            self.send_button.config(text=tr("Stopping..."))
            # 停止メッセージは完了時に追加するので、ここでは追加しない
        else:
            self._send_message()
    
    def _stop_if_processing(self):
        """処理中の場合は生成を停止"""
        if self._processing:
            self._stop_generation = True
            self.send_button.config(text=tr("Stopping..."))
            # 停止メッセージは完了時に追加するので、ここでは追加しない
    
    def _send_message(self):
        """メッセージを送信"""
        message = self.input_text.get("1.0", tk.END).strip()
        if not message:
            return
        
        # UIをクリア
        self.input_text.delete("1.0", tk.END)
        self._add_message("user", message)
        
        # 処理中フラグ
        self._processing = True
        self._current_message = ""
        self._stop_generation = False
        self.send_button.config(text="Stop", state=tk.NORMAL)
        
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
                # 現在のエディタ情報を取得
                workbench = get_workbench()
                editor = workbench.get_editor_notebook().get_current_editor()
                current_file = None
                selected_text = None
                
                if editor:
                    current_file = editor.get_filename()
                    text_widget = editor.get_text_widget()
                    
                    if text_widget.tag_ranges("sel"):
                        selected_text = text_widget.get("sel.first", "sel.last")
                        start_line = int(text_widget.index("sel.first").split(".")[0])
                        end_line = int(text_widget.index("sel.last").split(".")[0])
                        selection_info = f"Selected lines: {start_line}-{end_line}"
                
                if selected_text:
                    context_str = f"""File: {Path(current_file).name if current_file else 'Unknown'}
{selection_info}

```python
{selected_text}
```"""
                    self.message_queue.put(("info", "Using selected text as context"))
                elif editor and current_file:
                    # 選択範囲がない場合は、ファイル全体を取得
                    full_text = text_widget.get("1.0", tk.END).strip()
                    if full_text:
                        context_str = f"""File: {Path(current_file).name}
Full file content:

```python
{full_text}
```"""
                        self.message_queue.put(("info", "Using entire file as context"))
                    else:
                        context_str = None
                else:
                    context_str = None
                
                if context_str:
                    full_prompt = f"""Here is the context from the current project:

{context_str}

Based on this context, {message}"""
                    
                    for token in self.llm_client.generate_stream(full_prompt):
                        if self._stop_generation:
                            self.message_queue.put(("complete", None))
                            return
                        self.message_queue.put(("token", token))
                else:
                    for token in self.llm_client.generate_stream(message):
                        if self._stop_generation:
                            self.message_queue.put(("complete", None))
                            return
                        self.message_queue.put(("token", token))
            else:
                for token in self.llm_client.generate_stream(message):
                    if self._stop_generation:
                        self.message_queue.put(("complete", None))
                        return
                    self.message_queue.put(("token", token))
            
            self.message_queue.put(("complete", None))
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            self.message_queue.put(("error", str(e)))
    
    def _process_queue(self):
        """メッセージキューを処理"""
        try:
            update_needed = False
            
            while True:
                msg_type, content = self.message_queue.get_nowait()
                
                if msg_type == "token":
                    self._current_message += content
                    update_needed = True
                
                elif msg_type == "complete":
                    # 現在のメッセージがある場合、最終的に確定
                    if self._current_message:
                        # ストリーミング中に既に追加されている場合は更新のみ
                        if self.messages and self.messages[-1][0] == "assistant":
                            # 最後のメッセージを現在のメッセージで確定
                            self.messages[-1] = ("assistant", self._current_message)
                        else:
                            # アシスタントメッセージがない場合は新規追加
                            self._add_message("assistant", self._current_message)
                        self._current_message = ""
                        
                        # 停止された場合のみ停止メッセージを追加
                        if self._stop_generation:
                            self._add_message("system", tr("[Generation stopped by user]"))
                    elif self._stop_generation:
                        # メッセージがない場合でも停止メッセージを追加
                        self._add_message("system", tr("[Generation stopped by user]"))
                    
                    self._processing = False
                    self._stop_generation = False
                    self.send_button.config(text=tr("Send"), state=tk.NORMAL)
                
                elif msg_type == "error":
                    self._add_message("system", f"Error: {content}")
                    self._processing = False
                    self._stop_generation = False
                    self.send_button.config(text=tr("Send"), state=tk.NORMAL)
                
                elif msg_type == "info":
                    self._add_message("system", content)
            
        except queue.Empty:
            pass
        
        # ストリーミング中のメッセージを定期的に更新
        if update_needed and self._current_message:
            # 最後のメッセージがアシスタントなら更新、そうでなければ追加
            if self.messages and self.messages[-1][0] == "assistant":
                self.messages[-1] = ("assistant", self._current_message)
            else:
                self.messages.append(("assistant", self._current_message))
            
            # レート制限付きで更新（100ms間隔）
            current_time = time.time() * 1000  # ミリ秒
            if not self._update_pending and (current_time - self._last_update_time) > 100:
                self._update_html()
                self._last_update_time = current_time
                # ストリーミング中も頻繁にスクロール
                self.after(10, self._scroll_to_bottom)
            else:
                # 更新を予約
                if not self._update_pending:
                    self._update_pending = True
                    self.after(100, self._delayed_update)
        
        # 次のチェックをスケジュール
        self._queue_check_id = self.after(50, self._process_queue)
    
    def _delayed_update(self):
        """遅延更新を実行"""
        self._update_pending = False
        self._update_html()
        self._last_update_time = time.time() * 1000
    
    def explain_code(self, code: str):
        """コードを説明（外部から呼ばれる）"""
        message = f"Please explain this code:\n```python\n{code}\n```"
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert("1.0", message)
        self._send_message()
    
    def _explain_last_error(self):
        """最後のエラーを説明"""
        try:
            shell_view = get_workbench().get_view("ShellView")
            if not shell_view:
                messagebox.showinfo("No Shell", "Shell view not found.")
                return
            
            shell_text = shell_view.text
            shell_content = shell_text.get("1.0", tk.END)
            lines = shell_content.strip().split('\n')
            
            error_lines = []
            error_found = False
            
            for i in range(len(lines) - 1, -1, -1):
                line = lines[i]
                
                if error_found and (line.startswith(">>>") or line.startswith("===") or not line.strip()):
                    break
                
                if any(error_type in line for error_type in ["Error", "Exception", "Traceback"]):
                    error_found = True
                
                if error_found:
                    error_lines.insert(0, line)
            
            if not error_lines:
                messagebox.showinfo("No Error", "No recent error found in shell.")
                return
            
            error_message = '\n'.join(error_lines)
            
            code = ""
            editor = get_workbench().get_editor_notebook().get_current_editor()
            if editor:
                try:
                    code = editor.get_text_widget().get("1.0", tk.END).strip()
                except:
                    pass
            
            if code:
                prompt = f"I encountered this error:\n```\n{error_message}\n```\n\nIn this code:\n```python\n{code}\n```\n\nPlease explain what causes this error and how to fix it."
            else:
                prompt = f"I encountered this error:\n```\n{error_message}\n```\n\nPlease explain what causes this error and provide a solution."
            
            self.input_text.delete("1.0", tk.END)
            self.input_text.insert("1.0", prompt)
            self._send_message()
            
        except Exception as e:
            logger.error(f"Error in _explain_last_error: {e}")
            messagebox.showerror("Error", f"Failed to get error information: {str(e)}")
    
    def _show_settings(self):
        """設定ダイアログを表示"""
        from .settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.grab_set()
        self.wait_window(dialog)
        
        if hasattr(dialog, 'settings_changed') and dialog.settings_changed:
            self._init_llm()
    
    def _clear_chat(self):
        """チャットをクリア"""
        self.messages.clear()
        self._current_message = ""
        self._update_html()
        # 履歴もクリア
        self._save_chat_history()
    
    def _toggle_context(self):
        """コンテキストの有効/無効を切り替え"""
        if self.context_var.get():
            if not self.context_manager:
                from ..context_manager import ContextManager
                self.context_manager = ContextManager()
            
            workbench = get_workbench()
            editor = workbench.get_editor_notebook().get_current_editor()
            current_file = None
            
            if editor:
                current_file = editor.get_filename()
                text_widget = editor.get_text_widget()
                
                if text_widget.tag_ranges("sel"):
                    start_line = int(text_widget.index("sel.first").split(".")[0])
                    end_line = int(text_widget.index("sel.last").split(".")[0])
                    selected_range = f"lines {start_line}-{end_line}"
            
            try:
                if current_file:
                    file_info = f"Current file: {Path(current_file).name}"
                    
                    if 'selected_range' in locals():
                        self._add_message(
                            "system",
                            f"{tr('Context enabled for selected text')}\n{file_info} - {selected_range}"
                        )
                    else:
                        contexts = self.context_manager.get_project_context(current_file)
                        summary = self.context_manager.get_context_summary()
                        self._add_message(
                            "system",
                            f"{tr('Context enabled for current file')}\n{file_info} - {summary['total_classes']} classes, {summary['total_functions']} functions"
                        )
                else:
                    self._add_message("system", tr("Context enabled but no file is currently open"))
                    
            except Exception as e:
                logger.error(f"Error analyzing context: {e}")
                self._add_message("system", f"Error analyzing context: {str(e)}")
        else:
            self._add_message("system", tr("Context disabled"))
    
    def _get_chat_history_path(self) -> Path:
        """チャット履歴ファイルのパスを取得"""
        workbench = get_workbench()
        data_dir = Path(workbench.get_configuration_directory())
        llm_dir = data_dir / "llm_assistant"
        llm_dir.mkdir(exist_ok=True)
        return llm_dir / "chat_history.json"
    
    def _save_chat_history(self):
        """チャット履歴を保存"""
        try:
            # システムメッセージを除外して保存
            messages_to_save = [
                {"sender": sender, "text": text}
                for sender, text in self.messages
                if sender != "system" or not text.startswith("[")  # システムの状態メッセージを除外
            ]
            
            # 最新の100メッセージのみ保存（メモリ節約）
            messages_to_save = messages_to_save[-100:]
            
            history_path = self._get_chat_history_path()
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(messages_to_save, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save chat history: {e}")
    
    def _load_chat_history(self):
        """チャット履歴を読み込む"""
        try:
            history_path = self._get_chat_history_path()
            if history_path.exists():
                with open(history_path, 'r', encoding='utf-8') as f:
                    saved_messages = json.load(f)
                
                # 保存されたメッセージを復元
                for msg in saved_messages:
                    self.messages.append((msg["sender"], msg["text"]))
                
                if self.messages:
                    self._update_html()
                    self._add_message("system", tr("Previous conversation restored"))
                    
        except Exception as e:
            logger.error(f"Failed to load chat history: {e}")
    
    def _on_destroy(self, event):
        """ウィンドウが破棄される時のクリーンアップ"""
        # チャット履歴を保存
        self._save_chat_history()
        
        if hasattr(self, '_queue_check_id'):
            self.after_cancel(self._queue_check_id)
        
        self._stop_generation = True
        
        if self.llm_client:
            self.llm_client.shutdown()