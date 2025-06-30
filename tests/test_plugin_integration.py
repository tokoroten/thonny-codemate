"""
プラグイン統合テスト
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from thonnycontrib.thonny_codemate import load_plugin, explain_selection_handler, generate_from_comment_handler


class TestPluginIntegration:
    """プラグイン統合のテスト"""
    
    @patch('thonnycontrib.thonny_codemate.get_workbench')
    def test_load_plugin_success(self, mock_get_workbench):
        """プラグイン読み込み成功のテスト"""
        # Workbenchのモック
        mock_workbench = Mock()
        mock_get_workbench.return_value = mock_workbench
        
        # add_viewが失敗してもプラグインは読み込まれる
        mock_workbench.add_view.side_effect = ImportError("Test error")
        
        # プラグインを読み込む
        load_plugin()
        
        # 基本的なコマンドが登録されていることを確認
        assert mock_workbench.add_command.call_count >= 3  # 最低3つのコマンド
        assert mock_workbench.set_default.called  # デフォルト設定が登録される
    
    @patch('thonnycontrib.thonny_codemate.get_workbench')
    def test_load_plugin_already_loaded(self, mock_get_workbench):
        """プラグインが既に読み込まれている場合のテスト"""
        # 既に読み込まれている状態を設定
        import thonnycontrib.thonny_codemate as plugin_module
        plugin_module._plugin_loaded = True
        
        try:
            # 再度読み込みを試みる
            load_plugin()
            
            # workbenchが呼ばれないことを確認
            mock_get_workbench.assert_not_called()
        finally:
            # 状態をリセット
            plugin_module._plugin_loaded = False
    
    @patch('thonnycontrib.thonny_codemate.get_workbench')
    @patch('tkinter.messagebox.showinfo')
    def test_explain_selection_handler_no_selection(self, mock_msgbox, mock_get_workbench):
        """選択なしでexplain_selection_handlerを呼ぶテスト"""
        # エディタのモック
        mock_editor = Mock()
        mock_text_widget = Mock()
        mock_text_widget.tag_ranges.return_value = []  # 選択なし
        mock_editor.get_text_widget.return_value = mock_text_widget
        
        # Workbenchのモック
        mock_workbench = Mock()
        mock_workbench.get_editor_notebook.return_value.get_current_editor.return_value = mock_editor
        mock_get_workbench.return_value = mock_workbench
        
        # ハンドラーを実行
        explain_selection_handler()
        
        # メッセージボックスが表示されることを確認
        mock_msgbox.assert_called_once()
        assert "No Selection" in mock_msgbox.call_args[0][0]
    
    @patch('thonnycontrib.thonny_codemate.get_workbench')
    def test_explain_selection_handler_with_selection(self, mock_get_workbench):
        """選択ありでexplain_selection_handlerを呼ぶテスト"""
        # エディタのモック
        mock_editor = Mock()
        mock_text_widget = Mock()
        mock_text_widget.tag_ranges.return_value = ["1.0", "2.0"]  # 選択あり
        mock_text_widget.get.return_value = "selected code"
        mock_editor.get_text_widget.return_value = mock_text_widget
        
        # チャットビューのモック
        mock_chat_view = Mock()
        
        # Workbenchのモック
        mock_workbench = Mock()
        mock_workbench.get_editor_notebook.return_value.get_current_editor.return_value = mock_editor
        mock_workbench.get_view.return_value = mock_chat_view
        mock_get_workbench.return_value = mock_workbench
        
        # ハンドラーを実行
        explain_selection_handler()
        
        # チャットビューが表示されることを確認
        mock_workbench.show_view.assert_called_with("LLMChatView")
        
        # explain_codeが呼ばれることを確認
        if hasattr(mock_chat_view, 'explain_code'):
            mock_chat_view.explain_code.assert_called_with("selected code")
    
    @patch('thonnycontrib.thonny_codemate.get_workbench')
    @patch('tkinter.messagebox.showinfo')
    def test_generate_from_comment_no_comment(self, mock_msgbox, mock_get_workbench):
        """コメントなしでgenerate_from_commentを呼ぶテスト"""
        # エディタのモック
        mock_editor = Mock()
        mock_text_widget = Mock()
        mock_text_widget.index.return_value = "5.0"
        mock_text_widget.get.return_value = "regular code"  # コメントではない
        mock_editor.get_text_widget.return_value = mock_text_widget
        
        # Workbenchのモック
        mock_workbench = Mock()
        mock_workbench.get_editor_notebook.return_value.get_current_editor.return_value = mock_editor
        mock_get_workbench.return_value = mock_workbench
        
        # ハンドラーを実行
        generate_from_comment_handler()
        
        # メッセージボックスが表示されることを確認
        mock_msgbox.assert_called_once()
        assert "No Comment Found" in mock_msgbox.call_args[0][0]
    
    @patch('thonnycontrib.thonny_codemate.get_workbench')
    def test_generate_from_comment_with_comment(self, mock_get_workbench):
        """コメントありでgenerate_from_commentを呼ぶテスト"""
        # エディタのモック
        mock_editor = Mock()
        mock_text_widget = Mock()
        mock_text_widget.index.return_value = "5.0"
        
        # getメソッドが呼ばれるたびに異なる値を返す
        mock_text_widget.get.side_effect = [
            "# This is a comment",  # 現在行
            "# This is a comment",  # 最初のチェック
            "# Another comment",    # 2回目のチェック
            "",                     # 空行でストップ
        ]
        mock_editor.get_text_widget.return_value = mock_text_widget
        
        # チャットビューのモック
        mock_chat_view = Mock()
        mock_chat_view.input_text = Mock()
        mock_chat_view._send_message = Mock()
        
        # Workbenchのモック
        mock_workbench = Mock()
        mock_workbench.get_editor_notebook.return_value.get_current_editor.return_value = mock_editor
        mock_workbench.get_view.return_value = mock_chat_view
        mock_get_workbench.return_value = mock_workbench
        
        # ハンドラーを実行
        generate_from_comment_handler()
        
        # チャットビューが表示されることを確認
        mock_workbench.show_view.assert_called_with("LLMChatView")
        
        # メッセージが送信されることを確認
        mock_chat_view._send_message.assert_called_once()