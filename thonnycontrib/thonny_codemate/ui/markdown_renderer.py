"""
Markdown renderer for chat messages
Converts markdown to HTML and provides interactive features
"""
import re
from typing import Optional
import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name, PythonLexer
from pygments.formatters import HtmlFormatter


class MarkdownRenderer:
    """Markdownテキストを対話機能付きのHTMLに変換"""
    
    def __init__(self):
        # Markdownパーサーの設定
        # fenced_codeとcodehiliteを除外して、独自のコードブロック処理を使用
        self.md = markdown.Markdown(
            extensions=[
                'markdown.extensions.tables',
                'markdown.extensions.nl2br',
                'markdown.extensions.sane_lists',
            ]
        )
        
        # Pygmentsのスタイルを設定
        self.formatter = HtmlFormatter(style='friendly', nowrap=False)
        self.css_style = self.formatter.get_style_defs('.highlight')
        
        # コードブロックのIDカウンター
        self.code_block_id = 0
    
    def render(self, text: str, sender: str = "assistant") -> str:
        """
        MarkdownテキストをHTMLに変換
        
        Args:
            text: Markdownテキスト
            sender: 送信者（"user", "assistant", "system"）
            
        Returns:
            HTML文字列
        """
        # コードブロックを一時的に置換（後で処理）
        code_blocks = []
        # より柔軟な正規表現パターン（改行の有無に対応）
        code_pattern = re.compile(r'```(\w*)\n?(.*?)```', re.DOTALL)
        
        def replace_code_block(match):
            lang = match.group(1) or 'python'
            code = match.group(2).strip()
            code_blocks.append((lang, code))
            # 一意のプレースホルダーを生成
            placeholder_id = f'CODEBLOCK{len(code_blocks)-1}CODEBLOCK'
            return f'\n\n{placeholder_id}\n\n'
        
        # コードブロックを一時的なプレースホルダーに置換
        text_with_placeholders = code_pattern.sub(replace_code_block, text)
        
        # Markdownを変換
        html_content = self.md.convert(text_with_placeholders)
        
        # コードブロックを処理して戻す
        for i, (lang, code) in enumerate(code_blocks):
            code_html = self._render_code_block(lang, code)
            placeholder = f'CODEBLOCK{i}CODEBLOCK'
            # <p>タグで囲まれている場合も考慮
            html_content = html_content.replace(f'<p>{placeholder}</p>', code_html)
            html_content = html_content.replace(placeholder, code_html)
        
        # メッセージ全体をラップ
        sender_class = f"message-{sender}"
        full_html = f'''
        <div class="message {sender_class}">
            <div class="message-header">{sender.title()}</div>
            <div class="message-content">
                {html_content}
            </div>
        </div>
        '''
        
        return full_html
    
    def _render_code_block(self, language: str, code: str) -> str:
        """
        コードブロックをシンタックスハイライト付きでレンダリング
        Copy/Insertボタンも追加
        """
        self.code_block_id += 1
        block_id = f"code-block-{self.code_block_id}"
        
        # シンタックスハイライト
        try:
            if language:
                lexer = get_lexer_by_name(language, stripall=True)
            else:
                lexer = PythonLexer(stripall=True)
            highlighted_code = highlight(code, lexer, self.formatter)
        except Exception:
            # フォールバック
            highlighted_code = f'<pre><code>{self._escape_html(code)}</code></pre>'
        
        # エスケープされたコードを保存（JavaScript用）
        escaped_code = self._escape_js_string(code)
        
        # HTMLを生成
        return f'''
        <div class="code-block" id="{block_id}">
            <div class="code-header">
                <div class="code-language-wrapper">
                    <span class="code-language">{language or 'text'}</span>
                </div>
                <div class="code-buttons-wrapper">
                    <button class="code-button copy-button" onclick="copyCode('{block_id}')">
                        Copy
                    </button>
                    <button class="code-button insert-button" onclick="insertCode('{block_id}')">
                        Insert
                    </button>
                </div>
            </div>
            <div class="code-content">
                {highlighted_code}
            </div>
            <textarea class="code-source" style="display: none;" id="{block_id}-source">{self._escape_html(code)}</textarea>
        </div>
        '''
    
    def _escape_html(self, text: str) -> str:
        """HTMLエスケープ"""
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    def _escape_js_string(self, text: str) -> str:
        """JavaScript文字列用のエスケープ"""
        # シングルクォート、ダブルクォート、改行、バックスラッシュをエスケープ
        return (text
            .replace('\\', '\\\\')
            .replace("'", "\\'")
            .replace('"', '\\"')
            .replace('\n', '\\n')
            .replace('\r', '\\r')
            .replace('\t', '\\t'))
    
    def get_full_html(self, messages: list) -> str:
        """
        メッセージリストから完全なHTMLを生成
        
        Args:
            messages: [(sender, text), ...] のリスト
            
        Returns:
            完全なHTML文書
        """
        # コードブロックIDをリセット（完全再生成時）
        self.code_block_id = 0
        
        # メッセージをレンダリング
        messages_html = []
        for sender, text in messages:
            messages_html.append(self.render(text, sender))
        
        
        # 完全なHTML文書を生成
        return f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        /* 基本スタイル */
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 5px;
            background-color: #f8f8f8;
            font-size: 13px;
            line-height: 1.4;
            /* スムーズスクロールを無効化（プログラム制御のため） */
            scroll-behavior: auto !important;
        }}
        
        /* メッセージスタイル */
        .message {{
            margin-bottom: 10px;
            background: white;
            border-radius: 6px;
            padding: 8px 10px;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
            /* 更新時のちらつき防止 */
            transform: translateZ(0);
            will-change: contents;
        }}
        
        .message-header {{
            font-weight: bold;
            margin-bottom: 4px;
            color: #333;
            font-size: 12px;
        }}
        
        .message-user .message-header {{
            color: #0066cc;
        }}
        
        .message-assistant .message-header {{
            color: #006600;
        }}
        
        .message-system .message-header {{
            color: #666666;
        }}
        
        .message-content {{
            color: #333;
        }}
        
        /* コードブロックスタイル */
        .code-block {{
            margin: 6px 0;
            border: 1px solid #e1e4e8;
            border-radius: 4px;
            overflow: hidden;
            background: #f6f8fa;
        }}
        
        .code-header {{
            padding: 4px 10px;
            background: #f1f3f5;
            border-bottom: 1px solid #e1e4e8;
            min-height: 26px;
            overflow: hidden;
        }}
        
        .code-header:after {{
            content: "";
            display: table;
            clear: both;
        }}
        
        .code-language-wrapper {{
            float: left;
            line-height: 22px;
        }}
        
        .code-buttons-wrapper {{
            float: right;
            line-height: 22px;
        }}
        
        .code-language {{
            font-size: 11px;
            color: #586069;
            font-weight: 500;
            line-height: 18px;
        }}
        
        .code-button {{
            display: inline-block;
        }}
        
        .code-button + .code-button {{
            margin-left: 6px;
        }}
        
        .code-button {{
            padding: 2px 8px;
            font-size: 10px;
            border: 1px solid #d1d5da;
            background: white;
            border-radius: 3px;
            cursor: pointer;
            color: #333;
            font-weight: 500;
            transition: background-color 0.2s;
        }}
        
        .code-button:hover {{
            background: #f3f4f6;
            border-color: #c2c7cd;
        }}
        
        .code-button.copy-button {{
            background-color: #0066cc;
            color: white;
            border-color: #0066cc;
        }}
        
        .code-button.copy-button:hover {{
            background-color: #0052a3;
        }}
        
        .code-button.insert-button {{
            background-color: #28a745;
            color: white;
            border-color: #28a745;
        }}
        
        .code-button.insert-button:hover {{
            background-color: #218838;
        }}
        
        .code-content {{
            padding: 8px;
            overflow-x: auto;
        }}
        
        .code-content pre {{
            margin: 0;
            font-family: "Consolas", "Monaco", "Courier New", monospace;
            font-size: 12px;
            line-height: 1.3;
        }}
        
        /* Pygmentsスタイル */
        {self.css_style}
        
        /* その他のMarkdown要素 */
        p {{
            margin: 0 0 6px 0;
        }}
        
        ul, ol {{
            margin: 0 0 6px 0;
            padding-left: 18px;
        }}
        
        blockquote {{
            margin: 0 0 6px 0;
            padding: 0 0 0 12px;
            border-left: 3px solid #dfe2e5;
            color: #6a737d;
        }}
        
        table {{
            border-collapse: collapse;
            margin-bottom: 6px;
        }}
        
        th, td {{
            border: 1px solid #dfe2e5;
            padding: 4px 8px;
        }}
        
        th {{
            background-color: #f1f3f5;
            font-weight: 600;
        }}
        
        /* コピー成功の通知 */
        .copy-success {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 10px 20px;
            border-radius: 4px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
            animation: slideIn 0.3s ease-out;
        }}
        
        @keyframes slideIn {{
            from {{
                transform: translateY(100%);
                opacity: 0;
            }}
            to {{
                transform: translateY(0);
                opacity: 1;
            }}
        }}
    </style>
    <script>
        // コードをコピー
        function copyCode(blockId) {{
            var sourceElement = document.getElementById(blockId + '-source');
            if (!sourceElement) {{
                showNotification('Code source not found', 'error');
                return;
            }}
            var code = sourceElement.value;
            
            // Python関数を使用（PythonMonkey経由）
            if (typeof pyCopyCode !== 'undefined') {{
                try {{
                    var result = pyCopyCode(code);
                    if (result) {{
                        showCopySuccess();
                    }} else {{
                        showNotification('Failed to copy', 'error');
                    }}
                }} catch (error) {{
                    console.error('Copy error:', error);
                    // フォールバック: Clipboard API
                    navigator.clipboard.writeText(code).then(function() {{
                        showCopySuccess();
                    }}).catch(function(error) {{
                        showNotification('Failed to copy', 'error');
                    }});
                }}
            }} else {{
                // フォールバック: Clipboard API
                navigator.clipboard.writeText(code).then(function() {{
                    showCopySuccess();
                }}).catch(function(error) {{
                    showNotification('Failed to copy', 'error');
                }});
            }}
        }}
        
        // コードを挿入（Thonnyのエディタに）
        function insertCode(blockId) {{
            var sourceElement = document.getElementById(blockId + '-source');
            if (!sourceElement) {{
                showNotification('Code source not found', 'error');
                return;
            }}
            var code = sourceElement.value;
            
            // Python関数を使用（PythonMonkey経由）
            if (typeof pyInsertCode !== 'undefined') {{
                try {{
                    var result = pyInsertCode(code);
                    if (!result) {{
                        showNotification('Please open a file in the editor first', 'error');
                    }}
                    // 成功時はナビゲーションを防ぐため何もしない
                    return false;
                }} catch (error) {{
                    console.error('Insert error:', error);
                    // フォールバック: URL経由
                    window.location.href = 'thonny:insert:' + encodeURIComponent(code);
                }}
            }} else {{
                // フォールバック: URL経由でPythonに送信
                window.location.href = 'thonny:insert:' + encodeURIComponent(code);
            }}
        }}
        
        
        // コピー成功通知
        function showCopySuccess() {{
            showNotification('Code copied!', 'success');
        }}
        
        // 汎用的な通知関数
        function showNotification(message, type) {{
            var notification = document.createElement('div');
            notification.className = 'copy-success';
            notification.textContent = message;
            
            // タイプに応じて色を変更
            if (type === 'error') {{
                notification.style.backgroundColor = '#dc3545';
            }} else if (type === 'info') {{
                notification.style.backgroundColor = '#17a2b8';
            }}
            
            document.body.appendChild(notification);
            
            setTimeout(function() {{
                notification.remove();
            }}, 2000);
        }}
    </script>
</head>
<body>
    <div id="messages">
        {''.join(messages_html)}
    </div>
    <script>
        // ページの準備完了を示すフラグ
        window.pageReady = false;
        
        // ページ読み込み時に最下部にスクロール
        window.addEventListener('load', function() {{
            window.scrollTo(0, document.body.scrollHeight);
            window.pageReady = true;
        }});
    </script>
</body>
</html>
        '''