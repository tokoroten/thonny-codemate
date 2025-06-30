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
        
        # EditModeHandlerを初期化
        self.edit_mode_handler = None
    
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
        
        # 各UI要素を作成
        self._create_header_frame()
        self._create_html_frame()
        self._create_streaming_frame()
        self._create_input_frame()
        self._setup_key_bindings()
    
    def _create_header_frame(self):
        """ヘッダーフレームを作成"""
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
    
    def _create_html_frame(self):
        """HTMLフレームを作成"""
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
    
    def _create_streaming_frame(self):
        """ストリーミング表示エリアを作成"""
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
    
    def _create_input_frame(self):
        """入力エリアを作成"""
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
        
        self._create_buttons(button_frame)
        
        # コンテキストマネージャー
        self.context_manager = None
    
    def _create_buttons(self, button_frame):
        """ボタン類を作成"""
        # モード選択フレーム
        mode_frame = ttk.LabelFrame(button_frame, text=tr("Mode"), padding=2)
        mode_frame.pack(side=tk.LEFT, padx=5)
        
        self.mode_var = tk.StringVar(value="chat")
        ttk.Radiobutton(
            mode_frame,
            text=tr("Chat"),
            variable=self.mode_var,
            value="chat",
            command=self._on_mode_change
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Radiobutton(
            mode_frame,
            text=tr("Edit"),
            variable=self.mode_var,
            value="edit",
            command=self._on_mode_change
        ).pack(side=tk.LEFT, padx=2)
        
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
    
    def _setup_key_bindings(self):
        """キーバインディングを設定"""
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
        
        # Edit modeの場合は特別な処理
        if self.mode_var.get() == "edit":
            self._handle_edit_mode(message)
            return
        
        # Chat mode（通常の処理）
        # コンテキスト情報を取得して表示メッセージを作成
        context_info = self._get_context_info()
        display_message = self._format_display_message(message, context_info)
        
        # ユーザーメッセージを追加
        self._add_message("user", display_message)
        
        # ユーザーメッセージ追加後に最下部にスクロール
        self.after(100, self._scroll_to_bottom)
        
        # 生成を開始
        self._start_generation(message)
    
    def _get_context_info(self) -> Optional[str]:
        """コンテキスト情報を取得"""
        if not (self.context_var.get() and self.context_manager):
            return None
        
        workbench = get_workbench()
        editor = workbench.get_editor_notebook().get_current_editor()
        if not editor:
            return None
        
        current_file = editor.get_filename()
        text_widget = editor.get_text_widget()
        
        if text_widget.tag_ranges("sel"):
            # 選択範囲がある場合
            start_line = int(text_widget.index("sel.first").split(".")[0])
            end_line = int(text_widget.index("sel.last").split(".")[0])
            file_name = Path(current_file).name if current_file else "Untitled"
            return f"Context: {file_name} (lines {start_line}-{end_line})"
        else:
            # ファイル全体の場合（未保存ファイルも含む）
            file_name = Path(current_file).name if current_file else "Untitled"
            return f"Context: {file_name} (entire file)"
    
    def _format_display_message(self, message: str, context_info: Optional[str]) -> str:
        """表示用メッセージをフォーマット"""
        if context_info:
            return f"{message}\n\n[{context_info}]"
        return message
    
    def _start_generation(self, message: str):
        """生成処理を開始"""
        # 処理中フラグを設定
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
            
            # プロンプトと会話履歴を準備
            full_prompt = self._prepare_prompt_with_context(message)
            conversation_history = self._prepare_conversation_history()
            
            # ストリーミング生成
            self._stream_generation(llm_client, full_prompt, conversation_history)
            
        except Exception as e:
            self._handle_generation_error(e)
    
    def _prepare_prompt_with_context(self, message: str) -> str:
        """コンテキストを含むプロンプトを準備"""
        if not (self.context_var.get() and self.context_manager):
            return message
        
        context_str = self._build_context_string()
        if context_str:
            return f"""Here is the context from the current project:

{context_str}

Based on this context, {message}"""
        
        return message
    
    def _build_context_string(self) -> Optional[str]:
        """コンテキスト文字列を構築"""
        workbench = get_workbench()
        editor = workbench.get_editor_notebook().get_current_editor()
        if not editor:
            return None
        
        current_file = editor.get_filename()
        text_widget = editor.get_text_widget()
        
        # 選択範囲のテキストを取得
        selected_text = self._get_selected_text(text_widget)
        if selected_text:
            return self._format_selected_context(current_file, text_widget, selected_text)
        
        # 選択範囲がない場合はファイル全体
        # current_fileがなくても（未保存ファイル）エディタから内容を取得
        return self._format_full_file_context(current_file, text_widget)
    
    def _get_selected_text(self, text_widget) -> Optional[str]:
        """選択されたテキストを取得"""
        if text_widget.tag_ranges("sel"):
            return text_widget.get("sel.first", "sel.last")
        return None
    
    def _format_selected_context(self, current_file: str, text_widget, selected_text: str) -> str:
        """選択範囲のコンテキストをフォーマット"""
        start_line = int(text_widget.index("sel.first").split(".")[0])
        end_line = int(text_widget.index("sel.last").split(".")[0])
        selection_info = f"Selected lines: {start_line}-{end_line}"
        
        lang = self._detect_language(current_file)
        file_name = Path(current_file).name if current_file else 'Untitled'
        
        return f"""File: {file_name}
{selection_info}

```{lang}
{selected_text}
```"""
    
    def _format_full_file_context(self, current_file: str, text_widget) -> Optional[str]:
        """ファイル全体のコンテキストをフォーマット"""
        full_text = text_widget.get("1.0", tk.END).strip()
        if not full_text:
            return None
        
        lang = self._detect_language(current_file)
        file_name = Path(current_file).name if current_file else 'Untitled'
        
        return f"""File: {file_name}
Full file content:

```{lang}
{full_text}
```"""
    
    def _detect_language(self, file_path: str) -> str:
        """ファイル拡張子から言語を検出"""
        if not file_path:
            return 'python'
        
        file_ext = Path(file_path).suffix.lower()
        lang_map = {'.py': 'python', '.js': 'javascript', '.java': 'java', '.cpp': 'cpp', '.c': 'c'}
        return lang_map.get(file_ext, 'python')
    
    def _stream_generation(self, llm_client, prompt: str, conversation_history: list):
        """LLMからストリーミング生成"""
        for token in llm_client.generate_stream(prompt, messages=conversation_history):
            if self._stop_generation:
                self.message_queue.put(("complete", None))
                return
            self.message_queue.put(("token", token))
        
        self.message_queue.put(("complete", None))
    
    def _handle_generation_error(self, error: Exception):
        """生成エラーを処理"""
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error generating response: {error}\n{error_details}")
        
        # ユーザーフレンドリーなエラーメッセージ
        from ..utils.error_messages import get_user_friendly_error_message
        user_message = get_user_friendly_error_message(error, "generating response")
        self.message_queue.put(("error", user_message))
    
    def _process_queue(self):
        """メッセージキューを処理"""
        try:
            while True:
                msg_type, content = self.message_queue.get_nowait()
                
                if msg_type == "token":
                    self._handle_token(content)
                elif msg_type == "complete":
                    self._handle_completion()
                elif msg_type == "edit_complete":
                    self._handle_edit_completion(content)
                elif msg_type == "error":
                    self._handle_error(content)
                elif msg_type == "info":
                    self._add_message("system", content)
            
        except queue.Empty:
            pass
        
        # 次のチェックをスケジュール
        self._queue_check_id = self.after(50, self._process_queue)
    
    def _handle_token(self, content: str):
        """トークンを処理"""
        # 最初のトークンを受け取ったら準備完了
        if not self._first_token_received:
            self._first_token_received = True
            # ストリーミングフレームのタイトルを更新
            self.streaming_frame.config(text=tr("Assistant"))
        
        with self._message_lock:
            self._current_message += content
        
        # ストリーミングテキストに追加表示
        self._update_streaming_text(content)
    
    def _update_streaming_text(self, content: str):
        """ストリーミングテキストを更新"""
        self.streaming_text.config(state=tk.NORMAL)
        self.streaming_text.insert(tk.END, content)
        self.streaming_text.see(tk.END)
        self.streaming_text.config(state=tk.DISABLED)
    
    def _handle_completion(self):
        """生成完了を処理"""
        # ストリーミングエリアを非表示にしてHTMLビューに転送
        self._stop_generating_animation()
        
        # 現在のメッセージがある場合、HTMLビューに転送
        with self._message_lock:
            current_msg = self._current_message
        
        if current_msg:
            self._finalize_assistant_message(current_msg)
        elif self._stop_generation:
            # メッセージがない場合でも停止メッセージを追加
            self._add_message("system", tr("[Generation stopped by user]"))
        
        self._reset_generation_state()
    
    def _finalize_assistant_message(self, message: str):
        """アシスタントメッセージを完了"""
        # アシスタントメッセージを追加
        self.messages.append(("assistant", message))
        
        # HTMLビューに完全なメッセージを表示
        self._update_html(full_reload=True)
        
        # HTMLの更新完了後に最下部にスクロール
        self.after(200, self._scroll_to_bottom)
        
        with self._message_lock:
            self._current_message = ""
        
        # 停止された場合のみ停止メッセージを追加
        if self._stop_generation:
            self._add_message("system", tr("[Generation stopped by user]"))
    
    def _handle_edit_completion(self, full_response: str):
        """Edit mode完了時の処理"""
        # 通常の完了処理
        self._handle_completion()
        
        # 中止された場合のチェック
        if self._stop_generation:
            self._add_message("system", tr("⚠️ Edit generation was stopped. Changes were not applied."))
            return
        
        # コードブロックを抽出
        new_code = self.edit_mode_handler.extract_code_block(full_response)
        
        if not new_code:
            self._add_message("system", tr("No code changes were generated. Please try rephrasing your request."))
            return
        
        # エディタを取得
        workbench = get_workbench()
        editor = workbench.get_editor_notebook().get_current_editor()
        if not editor:
            self._add_message("system", tr("Editor was closed. Cannot apply changes."))
            return
        
        # 現在のコードを取得
        text_widget = editor.get_text_widget()
        original_code = text_widget.get("1.0", tk.END).strip()
        
        # "# ...existing code..." マーカーを展開
        try:
            expanded_code = self.edit_mode_handler.expand_existing_code_markers(new_code, original_code)
        except Exception as e:
            logger.error(f"Failed to expand code markers: {e}")
            expanded_code = new_code  # フォールバック
        
        # 差分を作成して表示（オプション）
        diff_lines = self.edit_mode_handler.create_diff(original_code, expanded_code)
        
        # 変更を適用
        if self.edit_mode_handler.apply_edit(editor, expanded_code):
            self._add_message("system", tr("✅ Changes applied successfully!"))
            
            # 差分のサマリーを表示
            added = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
            removed = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))
            if added or removed:
                self._add_message("system", f"📊 {added} lines added, {removed} lines removed")
        else:
            self._add_message("system", tr("❌ Failed to apply changes."))
    
    def _handle_error(self, error_message: str):
        """エラーを処理"""
        # ストリーミングエリアを非表示
        self._stop_generating_animation()
        
        self._add_message("system", f"Error: {error_message}")
        self._reset_generation_state()
    
    def _reset_generation_state(self):
        """生成状態をリセット"""
        self._processing = False
        self._stop_generation = False
        self.send_button.config(text=tr("Send"), state=tk.NORMAL)
        
        # グローバルの生成状態を解除
        from .. import set_llm_busy
        set_llm_busy(False)
    
    def _delayed_update(self):
        """遅延更新を実行（ストリーミング中は使用しない）"""
        # 新しいアプローチでは使用しない
        pass
    
    def explain_code(self, code: str):
        """コードを説明（外部から呼ばれる）"""
        # 既に生成中の場合は何もしない（ハンドラー側でチェック済み）
        if self._processing:
            return
        
        # 言語を検出
        lang = self._detect_current_file_language()
        
        # 説明用のプロンプトを生成
        message = self._build_code_explanation_prompt(code, lang)
        
        # プロンプトを入力して送信
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert("1.0", message)
        self._send_message()
    
    def _detect_current_file_language(self) -> str:
        """現在のファイルから言語を検出"""
        workbench = get_workbench()
        editor = workbench.get_editor_notebook().get_current_editor()
        
        if editor:
            filename = editor.get_filename()
            if filename:
                return self._detect_language(filename)
        
        return 'python'  # デフォルト
    
    def _build_code_explanation_prompt(self, code: str, lang: str) -> str:
        """コード説明用のプロンプトを構築"""
        workbench = get_workbench()
        
        # 言語設定を取得
        language_setting = self._get_language_setting(workbench)
        
        # スキルレベルの指示を取得
        skill_instruction = self._get_code_explanation_instruction(workbench)
        
        # 言語別のプロンプトを構築
        if language_setting == "Japanese":
            return f"{skill_instruction}\n\n以下のコードを説明してください:\n```{lang}\n{code}\n```"
        else:  # English
            return f"{skill_instruction}\n\nPlease explain this code:\n```{lang}\n{code}\n```"
    
    def _get_code_explanation_instruction(self, workbench_settings) -> str:
        """コード説明用のスキルレベル指示を取得"""
        skill_level = workbench_settings.get_option("llm.skill_level", "beginner")
        
        skill_instructions = {
            "beginner": "Explain in simple terms for a beginner. Avoid technical jargon and use plain language.",
            "intermediate": "Explain assuming basic programming knowledge.",
            "advanced": "Provide a detailed explanation including algorithmic efficiency and design considerations."
        }
        
        return skill_instructions.get(skill_level, skill_instructions["beginner"])
    
    def _explain_last_error(self):
        """最後のエラーを説明"""
        try:
            error_message = self._extract_error_from_shell()
            if not error_message:
                messagebox.showinfo("No Error", "No recent error found in shell.")
                return
            
            code = self._get_current_editor_code()
            prompt = self._build_error_explanation_prompt(error_message, code)
            
            self.input_text.delete("1.0", tk.END)
            self.input_text.insert("1.0", prompt)
            self._send_message()
            
        except Exception as e:
            self._handle_explain_error_failure(e)
    
    def _extract_error_from_shell(self) -> Optional[str]:
        """シェルからエラーメッセージを抽出"""
        shell_view = get_workbench().get_view("ShellView")
        if not shell_view:
            return None
        
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
        
        return '\n'.join(error_lines) if error_lines else None
    
    def _get_current_editor_code(self) -> str:
        """現在のエディタのコードを取得"""
        editor = get_workbench().get_editor_notebook().get_current_editor()
        if editor:
            try:
                return editor.get_text_widget().get("1.0", tk.END).strip()
            except:
                pass
        return ""
    
    def _build_error_explanation_prompt(self, error_message: str, code: str) -> str:
        """エラー説明用のプロンプトを構築"""
        workbench_settings = get_workbench()
        
        # 言語設定を取得
        language_setting = self._get_language_setting(workbench_settings)
        
        # スキルレベルの指示を取得
        skill_instruction = self._get_skill_instruction(workbench_settings)
        
        # 言語別のプロンプトを構築
        return self._format_error_prompt(language_setting, skill_instruction, error_message, code)
    
    def _get_language_setting(self, workbench_settings) -> str:
        """言語設定を取得"""
        language_setting = workbench_settings.get_option("llm.output_language", "auto")
        if language_setting == "auto":
            thonny_lang = workbench_settings.get_option("general.language", "en")
            return "Japanese" if thonny_lang.startswith("ja") else "English"
        elif language_setting == "ja":
            return "Japanese"
        elif language_setting == "en":
            return "English"
        return "English"
    
    def _get_skill_instruction(self, workbench_settings) -> str:
        """スキルレベルに応じた指示を取得"""
        skill_level = workbench_settings.get_option("llm.skill_level", "beginner")
        
        skill_instructions = {
            "beginner": "Explain the error in simple terms for a beginner and provide clear solutions.",
            "intermediate": "Explain the error and solutions assuming basic programming knowledge.",
            "advanced": "Provide a technical explanation of the error and efficient solutions."
        }
        
        return skill_instructions.get(skill_level, skill_instructions["beginner"])
    
    def _format_error_prompt(self, language: str, skill_instruction: str, error_message: str, code: str) -> str:
        """エラープロンプトをフォーマット"""
        if language == "Japanese":
            if code:
                return f"{skill_instruction}\n\n以下のエラーが発生しました:\n```\n{error_message}\n```\n\nこのコードで:\n```python\n{code}\n```"
            else:
                return f"{skill_instruction}\n\n以下のエラーが発生しました:\n```\n{error_message}\n```"
        else:  # English
            if code:
                return f"{skill_instruction}\n\nI encountered this error:\n```\n{error_message}\n```\n\nIn this code:\n```python\n{code}\n```"
            else:
                return f"{skill_instruction}\n\nI encountered this error:\n```\n{error_message}\n```"
    
    def _handle_explain_error_failure(self, error: Exception):
        """エラー説明の失敗を処理"""
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error in _explain_last_error: {error}\n{error_details}")
        messagebox.showerror(
            tr("Error"), 
            f"{tr('Failed to get error information')}: {str(error)}"
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
    
    def _handle_edit_mode(self, user_prompt: str):
        """Edit modeでのメッセージ処理"""
        # エディタの情報を取得
        workbench = get_workbench()
        editor = workbench.get_editor_notebook().get_current_editor()
        if not editor:
            self._add_message("system", tr("No active editor. Please open a file to edit."))
            return
        
        # ファイル情報を取得
        filename = editor.get_filename() or "Untitled"
        text_widget = editor.get_text_widget()
        content = text_widget.get("1.0", tk.END).strip()
        
        if not content:
            self._add_message("system", tr("The editor is empty. Please write some code first."))
            return
        
        # 選択範囲を取得（あれば）
        selection_info = self.edit_mode_handler.get_selection_info(editor)
        
        # メッセージを表示
        selection_text = ""
        if selection_info:
            _, start_line, end_line = selection_info
            selection_text = f" (lines {start_line}-{end_line})"
        self._add_message("user", f"{user_prompt}\n\n[Edit Mode: {Path(filename).name}{selection_text}]")
        
        # 生成を開始
        self._start_edit_generation(user_prompt, filename, content, selection_info)
    
    def _start_edit_generation(self, user_prompt: str, filename: str, content: str, selection_info):
        """Edit mode用の生成を開始"""
        if self._processing:
            return
        
        self._processing = True
        self._stop_generation = False
        self.send_button.config(text=tr("Stop"), state=tk.NORMAL)  # Stop ボタンを有効化
        
        # ストリーミングの準備
        self._start_generating_animation()
        
        # バックグラウンドで生成
        def generate():
            try:
                # Edit用のプロンプトを構築
                prompt = self.edit_mode_handler.build_edit_prompt(
                    user_prompt, filename, content, selection_info
                )
                
                # LLMで生成
                from .. import get_llm_client
                llm_client = get_llm_client()
                
                # 応答を収集
                full_response = ""
                for token in llm_client.generate_stream(prompt):
                    if self._stop_generation:
                        # 中止された場合もedit_completeを送信（部分的な応答で処理）
                        self.message_queue.put(("edit_complete", full_response))
                        return
                    full_response += token
                    self.message_queue.put(("token", token))
                
                # コードブロックを抽出
                self.message_queue.put(("edit_complete", full_response))
                
            except Exception as e:
                self.message_queue.put(("error", str(e)))
        
        import threading
        thread = threading.Thread(target=generate, daemon=True)
        thread.start()
    
    def _on_mode_change(self):
        """モード変更時の処理"""
        mode = self.mode_var.get()
        if mode == "edit":
            # Edit modeに切り替え
            self.context_check.config(state=tk.DISABLED)
            self.context_var.set(True)  # Edit modeでは常にコンテキストを含む
            
            # EditModeHandlerを初期化（必要な場合）
            if not self.edit_mode_handler:
                from ..edit_mode_handler import EditModeHandler
                from .. import get_llm_client
                self.edit_mode_handler = EditModeHandler(get_llm_client())
        else:
            # Chat modeに戻る
            self.context_check.config(state=tk.NORMAL)
    
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