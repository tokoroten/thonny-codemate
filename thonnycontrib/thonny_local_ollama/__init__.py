"""
Thonny Local LLM Plugin
GitHub Copilot風のローカルLLM統合を提供するThonnyプラグイン
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# プラグインのバージョン
__version__ = "0.1.0"

# グローバル変数でプラグインの状態を管理
_plugin_loaded = False
_llm_client: Optional['LLMClient'] = None


def load_plugin():
    """
    Thonnyが呼び出すプラグインエントリポイント
    プラグインの初期化とUIコンポーネントの登録を行う
    """
    global _plugin_loaded, _llm_client
    
    if _plugin_loaded:
        logger.warning("Plugin already loaded, skipping initialization")
        return
    
    try:
        from thonny import get_workbench
        workbench = get_workbench()
        
        logger.info("Loading Thonny Local LLM Plugin...")
        
        # UIコンポーネントを登録（エラーハンドリングを追加）
        try:
            from .ui.chat_view import LLMChatView
            workbench.add_view(
                LLMChatView,
                "LLM Assistant",
                "e",  # 右側に配置（east）
                visible_by_default=False,
                default_position_key="e"
            )
        except ImportError as e:
            logger.warning(f"Could not import chat view: {e}")
        
        # メニューコマンドを追加
        workbench.add_command(
            command_id="show_llm_assistant",
            menu_name="tools",
            command_label="Show LLM Assistant",
            handler=lambda: workbench.show_view("LLMChatView"),
            group=150
        )
        
        # エディタのコンテキストメニューにコマンドを追加
        workbench.add_command(
            command_id="explain_selection",
            menu_name="edit",
            command_label="Explain with LLM",
            handler=explain_selection_handler,
            default_sequence=None,
            extra_sequences=[],
            group=99
        )
        
        # コード生成コマンドを追加
        workbench.add_command(
            command_id="generate_from_comment",
            menu_name="edit",
            command_label="Generate Code from Comment",
            handler=generate_from_comment_handler,
            default_sequence="<Control-Alt-g>",
            extra_sequences=[],
            group=99
        )
        
        # 設定を登録
        workbench.set_default("llm.model_path", "")
        workbench.set_default("llm.skill_level", "beginner")
        workbench.set_default("llm.auto_load", False)
        
        _plugin_loaded = True
        logger.info("Thonny Local LLM Plugin loaded successfully!")
        
    except Exception as e:
        logger.error(f"Failed to load Thonny Local LLM Plugin: {e}", exc_info=True)
        raise


def explain_selection_handler():
    """
    選択されたコードを説明するハンドラー
    """
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
        
        # チャットビューを表示
        workbench.show_view("LLMChatView")
        
        # チャットビューに説明リクエストを送信
        chat_view = workbench.get_view("LLMChatView")
        if chat_view and hasattr(chat_view, 'explain_code'):
            chat_view.explain_code(selected_text)
        else:
            logger.error("Chat view not found or doesn't have explain_code method")
            
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
    
    if _llm_client is None:
        from .llm_client import LLMClient
        _llm_client = LLMClient()
    
    return _llm_client


def generate_from_comment_handler():
    """
    コメントからコードを生成するハンドラー
    """
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
        workbench.show_view("LLMChatView")
        
        # チャットビューに生成リクエストを送信
        chat_view = workbench.get_view("LLMChatView")
        if chat_view and hasattr(chat_view, 'generate_code_from_comment'):
            chat_view.generate_code_from_comment(comment_text, cursor_pos)
        else:
            # 直接メッセージを送信
            if chat_view:
                prompt = f"Generate Python code based on this comment:\n\n{comment_text}\n\nProvide only the code implementation without explanations."
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
