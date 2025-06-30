"""
Thonny Local LLM Plugin
GitHub Copilot風のローカルLLM統合を提供するThonnyプラグイン
"""
import logging
import sys
import threading
from typing import Optional
from pathlib import Path
from .i18n import tr

# ログを完全に無効化（Thonny環境での問題を回避）
import logging.config

# ログ設定を完全に無効化
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
})

# プラグイン用のロガー（何も出力しない）
logger = logging.getLogger(__name__)
logger.disabled = True

# プラグインのバージョン
__version__ = "0.1.4"

# グローバル変数でプラグインの状態を管理
_plugin_loaded = False
_llm_client: Optional['LLMClient'] = None
_is_generating = False  # LLMが生成中かどうかのフラグ
_generation_lock = threading.Lock()  # スレッドセーフティのためのロック


def get_safe_logger(name: str) -> logging.Logger:
    """
    Thonny環境で安全に動作するロガーを取得
    
    Args:
        name: ロガー名
        
    Returns:
        設定済みのロガー
    """
    safe_logger = logging.getLogger(name)
    safe_logger.setLevel(logging.INFO)
    
    # 既存のハンドラーがない場合のみ追加
    if not safe_logger.handlers:
        try:
            if sys.stderr is not None and hasattr(sys.stderr, 'write'):
                handler = logging.StreamHandler(sys.stderr)
                handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
                safe_logger.addHandler(handler)
            else:
                safe_logger.addHandler(logging.NullHandler())
        except Exception:
            safe_logger.addHandler(logging.NullHandler())
    
    return safe_logger


def load_plugin():
    """
    Thonnyが呼び出すプラグインエントリポイント
    プラグインの初期化とUIコンポーネントの登録を行う
    """
    global _plugin_loaded, _llm_client
    
    
    if _plugin_loaded:
        try:
            logger.warning("Plugin already loaded, skipping initialization")
        except Exception:
            pass
        return
    
    try:
        from thonny import get_workbench
        workbench = get_workbench()
        
        try:
            logger.info("Loading Thonny Local LLM Plugin...")
        except Exception:
            # ログ出力でエラーが発生しても続行
            pass
        
        # UIコンポーネントを登録（常にHTMLビューを使用）
        try:
            from .ui.chat_view_html import LLMChatViewHTML
            workbench.add_view(
                LLMChatViewHTML,
                "LLM Assistant",
                "e",  # 右側に配置（east）
                visible_by_default=False,
                default_position_key="e"
            )
        except Exception as e:
            logger.error(f"Failed to register chat view: {e}", exc_info=True)
        
        # メニューコマンドを追加
        workbench.add_command(
            command_id="show_llm_assistant",
            menu_name="tools",
            command_label=tr("Show LLM Assistant"),
            handler=lambda: workbench.show_view("LLMChatViewHTML"),  # クラス名を使用
            group=150
        )
        
        # AI機能のグループ（上下にセパレーターで区切る）
        # エディタのコンテキストメニューにコマンドを追加
        workbench.add_command(
            command_id="explain_selection",
            menu_name="edit",
            command_label=tr("AI: Explain Selected Code"),
            handler=explain_selection_handler,
            default_sequence="<Control-Alt-e>",  # Ctrl+Alt+E for Explain
            extra_sequences=["<Control-Shift-e>"],  # 代替ショートカット
            group=150  # グループ番号を調整
        )
        
        # コード生成コマンドを追加
        workbench.add_command(
            command_id="generate_from_comment",
            menu_name="edit",
            command_label=tr("AI: Generate Code from Comment"),
            handler=generate_from_comment_handler,
            default_sequence="<Control-Alt-g>",
            extra_sequences=[],
            group=150  # 同じグループにしてAI機能をまとめる
        )
        
        # 設定を登録
        workbench.set_default("llm.model_path", "")
        workbench.set_default("llm.skill_level", "beginner")
        workbench.set_default("llm.auto_load", False)
        workbench.set_default("llm.use_html_view", True)
        workbench.set_default("llm.repeat_penalty", 1.1)
        
        _plugin_loaded = True
        try:
            logger.info("Thonny Local LLM Plugin loaded successfully!")
        except Exception:
            pass
        
        print("=" * 60)
        print("✓ Thonny Codemate Plugin loaded successfully!")
        print("✓ LLM Assistant is available in Tools menu")
        print("=" * 60)
        
    except Exception as e:
        try:
            logger.error(f"Failed to load Thonny Local LLM Plugin: {e}", exc_info=True)
        except Exception:
            # ログ出力でエラーが発生した場合は、少なくともプリントを試みる
            try:
                print(f"Failed to load Thonny Local LLM Plugin: {e}")
            except Exception:
                pass
        raise


def is_llm_busy() -> bool:
    """
    LLMが現在生成中かどうかを確認
    """
    global _is_generating, _generation_lock
    with _generation_lock:
        return _is_generating


def set_llm_busy(busy: bool):
    """
    LLMの生成状態を設定
    """
    global _is_generating, _generation_lock
    with _generation_lock:
        _is_generating = busy


def explain_selection_handler():
    """
    選択されたコードを説明するハンドラー
    """
    # LLMが生成中の場合は実行しない
    if is_llm_busy():
        from tkinter import messagebox
        messagebox.showwarning(
            tr("LLM Busy"),
            tr("Please wait for the current generation to complete.")
        )
        return
    
    try:
        from thonny import get_workbench
        workbench = get_workbench()
        
        # エディタから選択テキストを取得
        editor = workbench.get_editor_notebook().get_current_editor()
        if not editor:
            logger.warning("No active editor")
            return
        
        text_widget = editor.get_text_widget()
        
        # 選択範囲があるかチェック
        if not text_widget.tag_ranges("sel"):
            from tkinter import messagebox
            messagebox.showinfo(
                "No Selection",
                "Please select some code to explain."
            )
            return
        
        # 選択テキストを取得
        selected_text = text_widget.get("sel.first", "sel.last")
        
        # チャットビューを表示（クラス名を使用）
        view_name = "LLMChatViewHTML"
        workbench.show_view(view_name)
        
        # チャットビューに説明リクエストを送信
        chat_view = workbench.get_view(view_name)
        if chat_view and hasattr(chat_view, 'explain_code'):
            chat_view.explain_code(selected_text)
        else:
            logger.error(f"Chat view not found or doesn't have explain_code method: {type(chat_view)}")
            
    except Exception as e:
        logger.error(f"Error in explain_selection_handler: {e}", exc_info=True)
        from tkinter import messagebox
        messagebox.showerror(
            "Error",
            f"Failed to explain selection: {str(e)}"
        )


def get_llm_client():
    """
    LLMクライアントのシングルトンインスタンスを取得
    遅延初期化を使用
    """
    global _llm_client
    
    # プロバイダーが変更されている可能性があるため、毎回チェック
    from thonny import get_workbench
    workbench = get_workbench()
    current_provider = workbench.get_option("llm.provider", "local")
    
    # クライアントが存在し、プロバイダーが一致している場合は再利用
    if _llm_client is not None:
        # LLMClient内部で管理されているプロバイダーを確認
        if _llm_client._current_provider == current_provider:
            return _llm_client
        else:
            # プロバイダーが変更された場合は再作成
            cleanup_llm_client()
    
    # 新しいクライアントを作成
    from .llm_client import LLMClient
    _llm_client = LLMClient()
    
    return _llm_client


def cleanup_llm_client():
    """LLMクライアントをクリーンアップ"""
    global _llm_client
    if _llm_client is not None:
        try:
            _llm_client.shutdown()
        except Exception:
            pass
        _llm_client = None


def generate_from_comment_handler():
    """
    コメントからコードを生成するハンドラー
    """
    # LLMが生成中の場合は実行しない
    if is_llm_busy():
        from tkinter import messagebox
        messagebox.showwarning(
            tr("LLM Busy"),
            tr("Please wait for the current generation to complete.")
        )
        return
    
    try:
        from thonny import get_workbench
        workbench = get_workbench()
        
        # エディタを取得
        editor = workbench.get_editor_notebook().get_current_editor()
        if not editor:
            logger.warning("No active editor")
            return
        
        text_widget = editor.get_text_widget()
        
        # カーソル位置を取得
        cursor_pos = text_widget.index("insert")
        line_num = int(cursor_pos.split(".")[0])
        
        # 現在の行とその前後の行を取得してコンテキストを把握
        current_line = text_widget.get(f"{line_num}.0", f"{line_num}.end")
        
        # コメント行を探す（現在行から上方向に）
        comment_lines = []
        check_line = line_num
        
        while check_line > 0:
            line_content = text_widget.get(f"{check_line}.0", f"{check_line}.end").strip()
            
            if line_content.startswith("#") or line_content.startswith('"""') or line_content.startswith("'''"):
                comment_lines.insert(0, line_content)
                check_line -= 1
            elif not line_content:  # 空行
                check_line -= 1
            else:
                break
        
        if not comment_lines:
            from tkinter import messagebox
            messagebox.showinfo(
                "No Comment Found",
                "Please write a comment describing what code you want to generate."
            )
            return
        
        # コメントを結合
        comment_text = "\n".join(comment_lines)
        
        # チャットビューを表示
        use_html_view = workbench.get_option("llm.use_html_view", True)
        view_name = "LLMChatViewHTML" if use_html_view else "LLMChatView"
        workbench.show_view(view_name)
        
        # チャットビューに生成リクエストを送信
        chat_view = workbench.get_view(view_name)
        if chat_view and hasattr(chat_view, 'generate_code_from_comment'):
            chat_view.generate_code_from_comment(comment_text, cursor_pos)
        else:
            # 直接メッセージを送信
            if chat_view:
                # ファイルから言語を検出
                filename = editor.get_filename()
                lang = 'Python'  # デフォルト
                if filename:
                    file_ext = Path(filename).suffix.lower()
                    lang_map = {
                        '.py': 'Python', '.js': 'JavaScript', '.java': 'Java',
                        '.cpp': 'C++', '.c': 'C', '.cs': 'C#', '.rb': 'Ruby',
                        '.go': 'Go', '.rs': 'Rust', '.php': 'PHP'
                    }
                    lang = lang_map.get(file_ext, 'Python')
                
                prompt = f"Generate {lang} code based on this comment:\n\n{comment_text}\n\nProvide only the code implementation without explanations."
                chat_view.input_text.delete("1.0", "end")
                chat_view.input_text.insert("1.0", prompt)
                chat_view._send_message()
            
    except Exception as e:
        logger.error(f"Error in generate_from_comment_handler: {e}", exc_info=True)
        from tkinter import messagebox
        messagebox.showerror(
            "Error",
            f"Failed to generate code: {str(e)}"
        )


def unload_plugin():
    """プラグインのアンロード時のクリーンアップ"""
    global _plugin_loaded
    
    # LLMクライアントをクリーンアップ
    cleanup_llm_client()
    
    # プラグインの状態をリセット
    _plugin_loaded = False
    
    try:
        # ワークベンチからビューを削除（必要な場合）
        from thonny import get_workbench
        workbench = get_workbench()
        # ビューの削除は通常Thonnyが自動的に行うため、ここでは特別な処理は不要
    except Exception:
        pass
