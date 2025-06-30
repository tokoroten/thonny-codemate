"""
定数定義モジュール
マジックナンバーやハードコードされた値を集約
"""

# UI関連の定数
class UIConstants:
    # ウィンドウサイズ
    SETTINGS_WINDOW_SIZE = (700, 750)
    
    # ボタン幅
    BUTTON_WIDTH_LARGE = 20
    BUTTON_WIDTH_SMALL = 12
    BUTTON_WIDTH_MEDIUM = 15
    
    # タイミング
    QUEUE_CHECK_INTERVAL_MS = 50
    HTML_READY_TIMEOUT_MS = 200
    NOTIFICATION_DURATION_MS = 2000
    
    # メッセージ制限
    MAX_MESSAGES_IN_MEMORY = 200


# LLM関連の定数
class LLMConstants:
    # モデルのデフォルト値
    DEFAULT_CONTEXT_SIZE = 4096
    DEFAULT_MAX_TOKENS = 2048
    DEFAULT_TEMPERATURE = 0.3
    DEFAULT_REPEAT_PENALTY = 1.1
    DEFAULT_TOP_P = 0.95
    DEFAULT_TOP_K = 40
    
    # メモリ制限
    MAX_CONVERSATION_HISTORY = 10
    
    # ストップトークン
    STOP_TOKENS = ["</s>", "\n\n\n"]
    CHAT_STOP_TOKENS = ["</s>"]


# プロバイダー固有の設定
class ProviderConstants:
    # APIキーオプション名のマッピング
    API_KEY_OPTIONS = {
        "chatgpt": "llm.chatgpt_api_key",
        "openrouter": "llm.openrouter_api_key"
    }
    
    # プロバイダー別モデルリスト
    PROVIDER_MODELS = {
        "chatgpt": [
            "gpt-4o",
            "gpt-4o-mini", 
            "gpt-4-turbo",
            "gpt-4",
            "o1-preview",
            "o1-mini"
        ],
        "openrouter": [
            "meta-llama/llama-3.2-3b-instruct:free",
            "meta-llama/llama-3.2-1b-instruct:free",
            "google/gemini-2.0-flash-exp:free",
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4o"
        ]
    }
    
    # デフォルトポート
    DEFAULT_PORTS = {
        "ollama": 11434,
        "lmstudio": 1234
    }
    
    # デフォルトベースURL
    DEFAULT_BASE_URLS = {
        "ollama": "http://localhost:11434",
        "lmstudio": "http://localhost:1234"
    }


# ファイル拡張子と言語のマッピング
LANGUAGE_EXTENSIONS = {
    '.py': 'Python',
    '.pyw': 'Python',
    '.js': 'JavaScript',
    '.mjs': 'JavaScript',
    '.cjs': 'JavaScript',
    '.ts': 'TypeScript',
    '.tsx': 'TypeScript',
    '.jsx': 'JavaScript',
    '.java': 'Java',
    '.cpp': 'C++',
    '.cxx': 'C++',
    '.cc': 'C++',
    '.c': 'C',
    '.h': 'C/C++',
    '.hpp': 'C++',
    '.cs': 'C#',
    '.go': 'Go',
    '.rs': 'Rust',
    '.php': 'PHP',
    '.rb': 'Ruby',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.scala': 'Scala',
    '.r': 'R',
    '.R': 'R',
    '.lua': 'Lua',
    '.pl': 'Perl',
    '.m': 'MATLAB/Objective-C',
    '.vb': 'Visual Basic',
    '.dart': 'Dart',
    '.jl': 'Julia',
    '.sh': 'Shell',
    '.bash': 'Bash',
    '.zsh': 'Zsh',
    '.ps1': 'PowerShell',
    '.html': 'HTML',
    '.htm': 'HTML',
    '.xml': 'XML',
    '.css': 'CSS',
    '.scss': 'SCSS',
    '.sass': 'Sass',
    '.less': 'Less',
    '.json': 'JSON',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.toml': 'TOML',
    '.ini': 'INI',
    '.cfg': 'Config',
    '.conf': 'Config',
    '.sql': 'SQL',
    '.md': 'Markdown',
    '.rst': 'reStructuredText',
    '.tex': 'LaTeX'
}