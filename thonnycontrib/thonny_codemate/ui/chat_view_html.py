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
import traceback
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

# パフォーマンスモニタリングを試す（オプショナル）
try:
    from ..performance_monitor import measure_performance, Timer
except ImportError:
    # パフォーマンスモニタリングが利用できない場合はダミー実装
    def measure_performance(operation=None):
        def decorator(func):
            return func
        return decorator
    
    class Timer:
        def __init__(self, operation):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass


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
        self._stop_generation = False
        self._first_token_received = False  # 最初のトークンを受け取ったか
        self._generating_animation_id = None  # アニメーションのafter ID
        
        # スレッドセーフティのためのロック
        self._message_lock = threading.Lock()
        self._current_message = ""  # ストリーミング中のメッセージ（ロックで保護）
        
        # HTMLが完全に読み込まれたかを追跡
        self._html_ready = False
        
        self._init_ui()
        self._init_llm()
        
        # 定期的にキューをチェック
        self._queue_check_id = self.after(100, self._process_queue)
        
        # ウィンドウ閉じるイベントをバインド
        self.bind("<Destroy>", self._on_destroy)
        
        # 最後の更新時刻（レート制限用）
        self._last_update_time = 0
        self._update_pending = False
        
        # ストリーミングメッセージIDを生成
        self._current_message_id = None
        
        # 一時ファイルのパス
        import tempfile
        self._temp_dir = tempfile.mkdtemp(prefix="thonny_llm_")
        self._current_html_path = None
        
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
            text=tr("tkinterweb is not installed"),
            font=("", 12, "bold")
        ).pack(pady=10)
        
        ttk.Label(
            frame,
            text=tr("To enable Markdown rendering and interactive features,\nplease install tkinterweb:\n\npip install tkinterweb"),
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
        header_frame.grid(row=0, column=0, sticky="ew", padx=3, pady=2)
        
        ttk.Label(header_frame, text=tr("LLM Assistant"), font=("", 10, "bold")).pack(side=tk.LEFT)
        
        # Clearボタン
        self.clear_button = ttk.Button(
            header_frame,
            text=tr("Clear"),
            command=self._clear_chat,
            width=8
        )
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
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
        status_frame.pack(side=tk.RIGHT, padx=3)
        
        self.status_label = ttk.Label(status_frame, text=tr("No model loaded"), foreground="gray")
        self.status_label.pack(side=tk.RIGHT)
        
        # HTMLフレーム（JavaScriptを有効化）
        self.html_frame = HtmlFrame(self, messages_enabled=False, javascript_enabled=True)
        self.html_frame.grid(row=1, column=0, sticky="nsew", padx=3, pady=2)
        
        
        # URL変更のハンドラーを設定（Insert機能用）
        self.html_frame.on_url_change = self._handle_url_change
        
        # JavaScriptインターフェースを設定（HTML読み込み前に登録）
        self._setup_js_interface()
        
        # 初期HTMLを設定
        self._update_html(full_reload=True)
        
        # 初期状態では空のHTMLなのですぐに準備完了とみなす
        if not self.messages:
            self._html_ready = True
        
        # ストリーミング表示エリア（HTMLビューと入力エリアの間）
        self.streaming_frame = ttk.LabelFrame(self, text=tr("Generating..."), padding=5)
        # 初期状態では非表示
        
        # ストリーミング用のテキストウィジェット
        from tkinter import scrolledtext
        self.streaming_text = scrolledtext.ScrolledText(
            self.streaming_frame,
            height=6,
            wrap=tk.WORD,
            font=("Consolas", 10),
            background="#f8f8f8",
            foreground="#333333",
            padx=10,
            pady=5
        )
        self.streaming_text.pack(fill=tk.BOTH, expand=True)
        self.streaming_text.config(state=tk.DISABLED)  # 読み取り専用
        
        # 入力エリア
        input_frame = ttk.Frame(self)
        input_frame.grid(row=3, column=0, sticky="ew", padx=3, pady=2)
        input_frame.columnconfigure(0, weight=1)
        
        # 入力テキスト
        self.input_text = tk.Text(
            input_frame,
            height=3,
            font=("Consolas", 10),
            wrap=tk.WORD
        )
        self.input_text.grid(row=0, column=0, sticky="ew", pady=(0, 2))
        
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
        hint_label.pack(side=tk.RIGHT, padx=3)
        
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
        self.context_check.pack(side=tk.LEFT, padx=5)
        
        # コンテキストマネージャー
        self.context_manager = None
        
        # キーバインディング
        self.input_text.bind("<Control-Return>", lambda e: (self._handle_send_button(), "break")[1])
        self.input_text.bind("<Shift-Return>", lambda e: "break")
        
        # Escapeキーで生成を停止
        self.bind_all("<Escape>", lambda e: self._stop_if_processing())
    
    def _show_notification(self, message, notification_type="success"):
        """一時的な通知を表示"""
        # ステータスラベルに一時的に表示
        original_text = self.status_label.cget("text")
        original_color = self.status_label.cget("foreground")
        
        # タイプに応じて色を設定
        color = "green" if notification_type == "success" else "red"
        self.status_label.config(text=message, foreground=color)
        
        # 2秒後に元に戻す
        self.after(2000, lambda: self.status_label.config(text=original_text, foreground=original_color))
    
    def _setup_js_interface(self):
        """JavaScriptとのインターフェースを設定"""
        try:
            # Python関数をJavaScriptから呼び出せるように登録
            self.html_frame.register_JS_object("pyInsertCode", self._insert_code)
            self.html_frame.register_JS_object("pyCopyCode", self._copy_code)
            logger.info("JavaScript API registered successfully")
        except Exception as e:
            logger.error(f"Failed to setup JavaScript interface: {e}")
    
    def _insert_code(self, code):
        """JavaScriptから呼ばれるコード挿入関数"""
        try:
            workbench = get_workbench()
            editor = workbench.get_editor_notebook().get_current_editor()
            if editor:
                text_widget = editor.get_text_widget()
                text_widget.insert("insert", code)
                text_widget.focus_set()
                self._show_notification("Code inserted into editor!")
                return True
            else:
                self._show_notification("Please open a file in the editor first", "error")
                return False
        except Exception as e:
            logger.error(f"Error inserting code: {e}")
            return False
    
    def _copy_code(self, code):
        """JavaScriptから呼ばれるコードコピー関数"""
        try:
            self.clipboard_clear()
            self.clipboard_append(code)
            self.update()
            return True
        except Exception as e:
            logger.error(f"Error copying code: {e}")
            return False
    
    def _handle_url_change(self, url):
        """URL変更を処理（Insert機能用）"""
        if url.startswith("thonny:insert:"):
            import urllib.parse
            code = urllib.parse.unquote(url[14:])
            
            workbench = get_workbench()
            editor = workbench.get_editor_notebook().get_current_editor()
            if editor:
                text_widget = editor.get_text_widget()
                text_widget.insert("insert", code)
                text_widget.focus_set()
                self._show_notification(tr("Code inserted into editor!"))
            else:
                messagebox.showinfo(tr("No Editor"), tr("Please open a file in the editor first."))
            
            # URLをリセットするため、空のページに戻す
            # HTMLの再読み込みは避ける（ボタンが使えなくなるため）
            try:
                self.html_frame.stop()  # 現在のナビゲーションを停止
            except:
                pass
        
        return True  # すべてのナビゲーションをキャンセル
    
    @measure_performance("chat_view.update_html")
    def _update_html(self, full_reload=True):
        """HTMLコンテンツを更新"""
        if full_reload:
            # 完全な再読み込み（初回やクリア時）
            self._html_ready = False
            html_content = self.markdown_renderer.get_full_html(self.messages)
            
            # HTMLを読み込み（HTML内のJavaScriptで自動的に表示される）
            self.html_frame.load_html(html_content)
            
            # HTMLの読み込み完了を待つためのチェック
            self.after(100, self._check_html_ready)
            
            # スクロール管理システムを初期化（HTMLロード後）
            self.after(200, lambda: self._init_scroll_manager() if not hasattr(self, '_scroll_manager_initialized') else None)
            
            # 完全読み込み後にスクロール（初回のみ）
            if not self.messages or len(self.messages) <= 1:
                self._scroll_to_bottom()
        else:
            # ストリーミング中は何もしない（ストリーミングテキストエリアで表示）
            pass
    
    def _update_last_message_js(self, message_html):
        """JavaScriptで最後のメッセージのみ更新"""
        # 新しいアプローチでは使用しない
        pass
    
    @measure_performance("chat_view.append_message_js")
    def _append_message_js(self, sender: str, text: str):
        """JavaScriptで新しいメッセージを追加"""
        try:
            # HTMLが準備できていない場合は全体更新
            if not self._html_ready:
                self._update_html(full_reload=True)
                return
            
            # HTMLを生成
            message_html = self.markdown_renderer.render(text, sender)
            
            # HTMLをJavaScript文字列としてエスケープ
            escaped_html = (message_html
                .replace('\\', '\\\\')
                .replace('\n', '\\n')
                .replace('\r', '\\r')
                .replace('"', '\\"')
                .replace('</script>', '<\\/script>'))
            
            js_code = f"""
            (function() {{
                var messagesDiv = document.getElementById('messages');
                if (!messagesDiv) {{
                    console.error('Messages container not found');
                    return false;
                }}
                
                // 新しいメッセージを追加
                messagesDiv.insertAdjacentHTML('beforeend', "{escaped_html}");
                return true;
            }})();
            """
            result = self.html_frame.run_javascript(js_code)
            
            # JavaScriptの実行に失敗した場合は全体更新
            if not result:
                self._update_html(full_reload=True)
            
        except Exception as e:
            logger.error(f"Could not append message: {e}")
            # エラーの場合はフォールバックとして完全更新
            self._update_html(full_reload=True)
    
    
    def _check_html_ready(self):
        """HTMLの読み込み完了をチェック"""
        # タイムアウト設定（10秒）
        if not hasattr(self, '_html_ready_check_count'):
            self._html_ready_check_count = 0
        
        self._html_ready_check_count += 1
        if self._html_ready_check_count > 200:  # 50ms * 200 = 10秒
            logger.warning("HTML ready check timeout - proceeding anyway")
            self._html_ready = True
            return
        
        try:
            # JavaScriptでDOMの準備状態をチェック
            js_code = """
            (function() {
                return document.readyState === 'complete' && 
                       document.getElementById('messages') !== null &&
                       typeof pyInsertCode !== 'undefined' &&
                       typeof pyCopyCode !== 'undefined' &&
                       window.pageReady === true;
            })();
            """
            result = self.html_frame.run_javascript(js_code)
            if result:
                self._html_ready = True
                logger.debug("HTML is ready")
                # HTMLが準備完了したらスクロール管理システムを初期化
                if not hasattr(self, '_scroll_manager_initialized'):
                    self._init_scroll_manager()
                    self._scroll_manager_initialized = True
            else:
                # まだ準備ができていない場合は再チェック
                self.after(50, self._check_html_ready)
        except Exception as e:
            logger.debug(f"HTML readiness check error: {e}")
            # エラーの場合も再チェック（タイムアウトまで）
            if self._html_ready_check_count < 200:
                self.after(50, self._check_html_ready)
    
    
    def _init_scroll_manager(self):
        """JavaScriptスクロール管理システムを初期化"""
        # シンプルなスクロール管理
        pass
    
    def _scroll_to_bottom(self):
        """HTMLフレームを最下部にスクロール"""
        try:
            # tkinterwebの標準的なスクロールメソッドを使用
            self.html_frame.yview_moveto(1.0)
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
                # 表示用のプロバイダー名
                display_provider = "Ollama/LM Studio" if provider == "ollama" else provider
                display_text = f"{external_model} ({display_provider})" if external_model else f"Using {display_provider}"
                self.status_label.config(text=display_text, foreground="blue")
                self.llm_client.get_config()
                self.send_button.config(state=tk.NORMAL)
                self._add_message(
                    "system",
                    tr("Connected to {} API. Ready to chat!").format(display_provider.upper())
                )
        
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Failed to initialize LLM client: {e}\n{error_details}")
            self.status_label.config(text="Error loading model", foreground="red")
            # ユーザーフレンドリーなエラーメッセージ
            if "import" in str(e).lower():
                user_message = tr("LLM module not installed. Please install llama-cpp-python.")
            else:
                user_message = f"{tr('Failed to initialize LLM')}: {str(e)}"
            self._add_message("system", user_message)
    
    def _on_model_loaded(self, success: bool, error: Optional[Exception]):
        """モデル読み込み完了時のコールバック"""
        def update_ui():
            if success:
                model_path = get_workbench().get_option("llm.model_path", "")
                model_name = Path(model_path).name if model_path else "Unknown"
                self.status_label.config(text=f"{model_name} | {tr('Ready')}", foreground="green")
                self.send_button.config(state=tk.NORMAL)
                self._add_message("system", tr("LLM model loaded successfully!"))
            else:
                self.status_label.config(text=tr("Load failed"), foreground="red")
                self._add_message("system", f"{tr('Failed to load model:')} {error}")
        
        self.after(0, update_ui)
    
    def _add_message(self, sender: str, text: str):
        """メッセージを追加してHTMLを更新"""
        # メッセージ履歴の上限を設定（メモリ使用量を制限）
        MAX_MESSAGES = 200  # メモリ上の最大メッセージ数
        
        self.messages.append((sender, text))
        
        # 古いメッセージを削除（最新のMAX_MESSAGES件のみ保持）
        if len(self.messages) > MAX_MESSAGES:
            # 最初の10%を削除してパフォーマンスを向上
            remove_count = max(1, MAX_MESSAGES // 10)
            self.messages = self.messages[remove_count:]
            logger.debug(f"Trimmed {remove_count} old messages from memory")
        
        # HTMLが準備できているかチェックしてメッセージを追加
        if self._html_ready:
            # JavaScriptで新しいメッセージを追加（全体再読み込みを避ける）
            self._append_message_js(sender, text)
            # ユーザーメッセージの場合のみ自動スクロール（会話開始時）
            if sender == "user":
                self._scroll_to_bottom()
        else:
            # HTMLが準備できていない場合は、準備完了を待ってから追加
            self._add_message_when_ready(sender, text)
        
        # ユーザーとアシスタントのメッセージのみ保存（システムメッセージは一時的なものが多いため）
        if sender in ["user", "assistant"]:
            self._save_chat_history()
    
    def _add_message_when_ready(self, sender: str, text: str, retry_count=0):
        """HTMLが準備できたらメッセージを追加（既にメッセージリストには追加済み）"""
        if self._html_ready:
            # JavaScriptで新しいメッセージを追加
            self._append_message_js(sender, text)
            # ユーザーメッセージの場合のみスクロール
            if sender == "user":
                self._scroll_to_bottom()
        else:
            # まだ準備ができていない場合は再試行（最大100回）
            if retry_count < 100:
                self.after(50, lambda: self._add_message_when_ready(sender, text, retry_count + 1))
            else:
                # タイムアウト時は全体を再読み込み
                self._update_html(full_reload=True)
    
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
        
        # コンテキスト情報を取得
        context_info = None
        if self.context_var.get() and self.context_manager:
            workbench = get_workbench()
            editor = workbench.get_editor_notebook().get_current_editor()
            if editor:
                current_file = editor.get_filename()
                text_widget = editor.get_text_widget()
                
                if text_widget.tag_ranges("sel"):
                    # 選択範囲がある場合
                    start_line = int(text_widget.index("sel.first").split(".")[0])
                    end_line = int(text_widget.index("sel.last").split(".")[0])
                    file_name = Path(current_file).name if current_file else "Unknown"
                    context_info = f"Context: {file_name} (lines {start_line}-{end_line})"
                elif current_file:
                    # ファイル全体の場合
                    file_name = Path(current_file).name
                    context_info = f"Context: {file_name} (entire file)"
        
        # ユーザーメッセージを追加（コンテキスト情報付き）
        if context_info:
            display_message = f"{message}\n\n[{context_info}]"
        else:
            display_message = message
        
        self._add_message("user", display_message)
        
        # ユーザーメッセージ追加後に最下部にスクロール
        self.after(100, self._scroll_to_bottom)
        
        # 処理中フラグ
        self._processing = True
        with self._message_lock:
            self._current_message = ""
        self._stop_generation = False
        self._first_token_received = False
        self.send_button.config(text="Stop", state=tk.NORMAL)
        
        # 新しいメッセージIDを生成
        import time
        self._current_message_id = f"msg_{int(time.time() * 1000)}"
        
        # グローバルの生成状態を更新
        from .. import set_llm_busy
        set_llm_busy(True)
        
        # "Generating..."アニメーションを開始
        self._start_generating_animation()
        
        # バックグラウンドで処理
        thread = threading.Thread(
            target=self._generate_response,
            args=(message,),  # 元のメッセージを渡す（コンテキスト情報なし）
            daemon=True
        )
        thread.start()
    
    def _get_system_prompt(self) -> str:
        """スキルレベルと言語設定に応じたシステムプロンプトを生成（フォーマット文字列置換付き）"""
        workbench = get_workbench()
        
        # 設定値を取得
        skill_level_setting = workbench.get_option("llm.skill_level", "beginner")
        language_setting = workbench.get_option("llm.language", "auto")
        custom_prompt = workbench.get_option("llm.custom_system_prompt", "")
        
        # カスタムプロンプトが設定されている場合はそれを使用
        if custom_prompt.strip():
            template = custom_prompt
        else:
            # デフォルトテンプレート（共通定数から取得）
            from ..prompts import DEFAULT_SYSTEM_PROMPT_TEMPLATE
            template = DEFAULT_SYSTEM_PROMPT_TEMPLATE
        
        # スキルレベルの詳細説明を生成（共通定数から取得）
        from ..prompts import SKILL_LEVEL_DESCRIPTIONS
        
        skill_level_detailed = SKILL_LEVEL_DESCRIPTIONS.get(skill_level_setting, skill_level_setting)
        
        # フォーマット文字列を置換
        try:
            formatted_prompt = template.format(
                skill_level=skill_level_detailed,
                language=language_setting
            )
            return formatted_prompt
        except KeyError as e:
            # フォーマット文字列にエラーがある場合はそのまま返す
            return template
    
    def _prepare_conversation_history(self) -> list:
        """会話履歴をLLM用の形式に変換（システムプロンプト付き）"""
        history = []
        
        # システムプロンプトを最初に追加
        system_prompt = self._get_system_prompt()
        history.append({"role": "system", "content": system_prompt})
        
        # 最新の会話履歴から適切な数だけ取得（メモリ制限のため）
        workbench = get_workbench()
        max_history = workbench.get_option("llm.max_conversation_history", 10)  # デフォルト10ターン
        
        # 現在生成中の場合、最新のユーザーメッセージは除外する
        messages_to_process = self.messages[:-1] if self._processing else self.messages
        
        for sender, text in messages_to_process[-max_history:]:
            if sender == "user":
                # コンテキスト情報を除去（[Context: ...]の部分）
                clean_text = text
                if "\n\n[Context:" in text:
                    clean_text = text.split("\n\n[Context:")[0]
                history.append({"role": "user", "content": clean_text})
            elif sender == "assistant":
                history.append({"role": "assistant", "content": text})
            # システムメッセージ（UI上の）は除外（システムプロンプトとは別）
        
        return history
    
    def _generate_response(self, message: str):
        """バックグラウンドで応答を生成"""
        try:
            # 最新のLLMクライアントを取得（プロバイダー変更に対応）
            from .. import get_llm_client
            llm_client = get_llm_client()
            
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
                    # ファイル拡張子から言語を判定
                    file_ext = Path(current_file).suffix.lower() if current_file else '.py'
                    lang_map = {'.py': 'python', '.js': 'javascript', '.java': 'java', '.cpp': 'cpp', '.c': 'c'}
                    lang = lang_map.get(file_ext, 'python')
                    
                    context_str = f"""File: {Path(current_file).name if current_file else 'Unknown'}
{selection_info}

```{lang}
{selected_text}
```"""
                    # コンテキスト使用メッセージは不要
                elif editor and current_file:
                    # 選択範囲がない場合は、ファイル全体を取得
                    full_text = text_widget.get("1.0", tk.END).strip()
                    if full_text:
                        # ファイル拡張子から言語を判定
                        file_ext = Path(current_file).suffix.lower()
                        lang_map = {'.py': 'python', '.js': 'javascript', '.java': 'java', '.cpp': 'cpp', '.c': 'c'}
                        lang = lang_map.get(file_ext, 'python')
                        
                        context_str = f"""File: {Path(current_file).name}
Full file content:

```{lang}
{full_text}
```"""
                        # コンテキスト使用メッセージは不要
                    else:
                        context_str = None
                else:
                    context_str = None
                
                if context_str:
                    full_prompt = f"""Here is the context from the current project:

{context_str}

Based on this context, {message}"""
                    
                    # 会話履歴を準備
                    conversation_history = self._prepare_conversation_history()
                    
                    for token in llm_client.generate_stream(
                        full_prompt,
                        messages=conversation_history
                    ):
                        if self._stop_generation:
                            self.message_queue.put(("complete", None))
                            return
                        self.message_queue.put(("token", token))
                else:
                    # 会話履歴を準備
                    conversation_history = self._prepare_conversation_history()
                    
                    for token in llm_client.generate_stream(
                        message,
                        messages=conversation_history
                    ):
                        if self._stop_generation:
                            self.message_queue.put(("complete", None))
                            return
                        self.message_queue.put(("token", token))
            else:
                # 会話履歴を準備
                conversation_history = self._prepare_conversation_history()
                
                for token in llm_client.generate_stream(
                    message,
                    messages=conversation_history
                ):
                    if self._stop_generation:
                        self.message_queue.put(("complete", None))
                        return
                    self.message_queue.put(("token", token))
            
            self.message_queue.put(("complete", None))
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error generating response: {e}\n{error_details}")
            # ユーザーフレンドリーなエラーメッセージ
            if "connection" in str(e).lower():
                user_message = tr("Connection error. Please check your network and API settings.")
            elif "api key" in str(e).lower():
                user_message = tr("API key error. Please check your API key in settings.")
            elif "model" in str(e).lower():
                user_message = tr("Model error. The selected model may not be available.")
            else:
                user_message = f"{tr('Error generating response')}: {str(e)}"
            self.message_queue.put(("error", user_message))
    
    def _process_queue(self):
        """メッセージキューを処理"""
        try:
            update_needed = False
            
            while True:
                msg_type, content = self.message_queue.get_nowait()
                
                if msg_type == "token":
                    # 最初のトークンを受け取ったら準備完了
                    if not self._first_token_received:
                        self._first_token_received = True
                        # ストリーミングフレームのタイトルを更新
                        self.streaming_frame.config(text=tr("Assistant"))
                    
                    with self._message_lock:
                        self._current_message += content
                    
                    # ストリーミングテキストに追加表示
                    self.streaming_text.config(state=tk.NORMAL)
                    self.streaming_text.insert(tk.END, content)
                    self.streaming_text.see(tk.END)
                    self.streaming_text.config(state=tk.DISABLED)
                    
                    update_needed = True
                
                elif msg_type == "complete":
                    # ストリーミングエリアを非表示にしてHTMLビューに転送
                    self._stop_generating_animation()
                    
                    # 現在のメッセージがある場合、HTMLビューに転送
                    with self._message_lock:
                        current_msg = self._current_message
                    
                    if current_msg:
                        # アシスタントメッセージを追加
                        self.messages.append(("assistant", current_msg))
                        
                        # HTMLビューに完全なメッセージを表示
                        self._update_html(full_reload=True)
                        
                        # HTMLの更新完了後に最下部にスクロール
                        self.after(200, self._scroll_to_bottom)
                        
                        with self._message_lock:
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
                    
                    # グローバルの生成状態を解除
                    from .. import set_llm_busy
                    set_llm_busy(False)
                
                elif msg_type == "error":
                    # ストリーミングエリアを非表示
                    self._stop_generating_animation()
                    
                    self._add_message("system", f"Error: {content}")
                    self._processing = False
                    self._stop_generation = False
                    self.send_button.config(text=tr("Send"), state=tk.NORMAL)
                    
                    # グローバルの生成状態を解除
                    from .. import set_llm_busy
                    set_llm_busy(False)
                
                elif msg_type == "info":
                    self._add_message("system", content)
            
        except queue.Empty:
            pass
        
        # ストリーミング中はHTMLビューを更新しない（ストリーミングテキストエリアで表示中）
        # HTMLビューの更新は完了時に一度だけ実行
        
        # 次のチェックをスケジュール
        self._queue_check_id = self.after(50, self._process_queue)
    
    def _delayed_update(self):
        """遅延更新を実行（ストリーミング中は使用しない）"""
        # 新しいアプローチでは使用しない
        pass
    
    def explain_code(self, code: str):
        """コードを説明（外部から呼ばれる）"""
        # 既に生成中の場合は何もしない（ハンドラー側でチェック済み）
        if self._processing:
            return
        
        # 現在のファイルから言語を検出
        workbench = get_workbench()
        editor = workbench.get_editor_notebook().get_current_editor()
        lang = 'python'  # デフォルト
        if editor:
            filename = editor.get_filename()
            if filename:
                file_ext = Path(filename).suffix.lower()
                lang_map = {'.py': 'python', '.js': 'javascript', '.java': 'java', '.cpp': 'cpp', '.c': 'c'}
                lang = lang_map.get(file_ext, 'python')
        
        # 言語設定を取得
        language_setting = workbench.get_option("llm.output_language", "auto")
        if language_setting == "auto":
            # Thonnyの言語設定から取得
            thonny_lang = workbench.get_option("general.language", "en")
            language_setting = "Japanese" if thonny_lang.startswith("ja") else "English"
        elif language_setting == "ja":
            language_setting = "Japanese"
        elif language_setting == "en":
            language_setting = "English"
        
        # スキルレベルを考慮したプロンプトを生成
        skill_level = workbench.get_option("llm.skill_level", "beginner")
        
        # スキルレベルの指示（英語で統一）
        if skill_level == "beginner":
            skill_instruction = "Explain in simple terms for a beginner. Avoid technical jargon and use plain language."
        elif skill_level == "intermediate":
            skill_instruction = "Explain assuming basic programming knowledge."
        else:  # advanced
            skill_instruction = "Provide a detailed explanation including algorithmic efficiency and design considerations."
        
        # 言語別のプロンプト
        if language_setting == "Japanese":
            message = f"{skill_instruction}\n\n以下のコードを説明してください:\n```{lang}\n{code}\n```"
        else:  # English
            message = f"{skill_instruction}\n\nPlease explain this code:\n```{lang}\n{code}\n```"
        
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
            
            # 言語設定とスキルレベルを取得
            workbench_settings = get_workbench()
            language_setting = workbench_settings.get_option("llm.output_language", "auto")
            if language_setting == "auto":
                thonny_lang = workbench_settings.get_option("general.language", "en")
                language_setting = "Japanese" if thonny_lang.startswith("ja") else "English"
            elif language_setting == "ja":
                language_setting = "Japanese"
            elif language_setting == "en":
                language_setting = "English"
            
            skill_level = workbench_settings.get_option("llm.skill_level", "beginner")
            
            # スキルレベルの指示（英語で統一）
            if skill_level == "beginner":
                skill_instruction = "Explain the error in simple terms for a beginner and provide clear solutions."
            elif skill_level == "intermediate":
                skill_instruction = "Explain the error and solutions assuming basic programming knowledge."
            else:  # advanced
                skill_instruction = "Provide a technical explanation of the error and efficient solutions."
            
            # 言語別のプロンプト
            if language_setting == "Japanese":
                if code:
                    prompt = f"{skill_instruction}\n\n以下のエラーが発生しました:\n```\n{error_message}\n```\n\nこのコードで:\n```python\n{code}\n```"
                else:
                    prompt = f"{skill_instruction}\n\n以下のエラーが発生しました:\n```\n{error_message}\n```"
            else:  # English
                if code:
                    prompt = f"{skill_instruction}\n\nI encountered this error:\n```\n{error_message}\n```\n\nIn this code:\n```python\n{code}\n```"
                else:
                    prompt = f"{skill_instruction}\n\nI encountered this error:\n```\n{error_message}\n```"
            
            self.input_text.delete("1.0", tk.END)
            self.input_text.insert("1.0", prompt)
            self._send_message()
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error in _explain_last_error: {e}\n{error_details}")
            messagebox.showerror(
                tr("Error"), 
                f"{tr('Failed to get error information')}: {str(e)}"
            )
    
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
        with self._message_lock:
            self._current_message = ""
        self._update_html(full_reload=True)  # クリア時は全体再読み込み
        # 履歴もクリア
        self._save_chat_history()
    
    def _toggle_context(self):
        """コンテキストの有効/無効を切り替え"""
        if self.context_var.get():
            if not self.context_manager:
                from ..context_manager import ContextManager
                self.context_manager = ContextManager()
    
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
                    # 履歴がある場合は、HTMLの準備後にシステムメッセージを追加
                    self._update_html(full_reload=True)  # 履歴読み込み時は全体更新が必要
                    self.after(300, lambda: self._add_message("system", tr("Previous conversation restored")))
                    
        except Exception as e:
            logger.error(f"Failed to load chat history: {e}")
    
    def _start_generating_animation(self):
        """生成中のアニメーションを開始（ストリーミングエリアを表示）"""
        try:
            # 既存のアニメーションがあれば停止
            if self._generating_animation_id:
                self.after_cancel(self._generating_animation_id)
                self._generating_animation_id = None
            
            # ストリーミングフレームを表示（HTMLビューと入力エリアの間に配置）
            self.streaming_frame.grid(row=2, column=0, sticky="ew", padx=3, pady=2)
            # ストリーミングテキストをクリアして準備
            self.streaming_text.config(state=tk.NORMAL)
            self.streaming_text.delete("1.0", tk.END)
            self.streaming_text.config(state=tk.DISABLED)
            
        except Exception as e:
            logger.error(f"Error starting animation: {e}")
    
    def _stop_generating_animation(self):
        """生成中のアニメーションを停止（ストリーミングエリアを非表示）"""
        try:
            # アニメーションIDをキャンセル
            if self._generating_animation_id:
                self.after_cancel(self._generating_animation_id)
                self._generating_animation_id = None
            
            # ストリーミングフレームを非表示
            self.streaming_frame.grid_remove()
            
        except Exception as e:
            logger.error(f"Error stopping animation: {e}")
    
    def _on_destroy(self, event):
        """ウィンドウが破棄される時のクリーンアップ"""
        # チャット履歴を保存
        self._save_chat_history()
        
        if hasattr(self, '_queue_check_id'):
            self.after_cancel(self._queue_check_id)
        
        self._stop_generation = True
        
        if self.llm_client:
            self.llm_client.shutdown()