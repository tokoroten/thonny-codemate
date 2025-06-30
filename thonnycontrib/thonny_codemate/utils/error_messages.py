"""
エラーメッセージ処理のユーティリティ
重複したエラーメッセージ処理ロジックを統一
"""
from typing import Optional
from ..tr import tr


def get_user_friendly_error_message(error: Exception, context: str = "") -> str:
    """
    技術的なエラーをユーザーフレンドリーなメッセージに変換
    
    Args:
        error: 発生したException
        context: エラーの文脈（例: "generating response", "loading model"）
        
    Returns:
        ユーザー向けのエラーメッセージ
    """
    error_str = str(error).lower()
    
    # エラーメッセージのマッピング
    ERROR_MAPPINGS = {
        # ネットワーク関連
        "connection": tr("Connection error. Please check your network and API settings."),
        "urlopen": tr("Cannot connect to server. Please check if the service is running."),
        "timeout": tr("Request timed out. The server may be busy or unreachable."),
        "refused": tr("Connection refused. Please check if the service is running."),
        
        # 認証関連
        "api key": tr("API key error. Please check your API key in settings."),
        "401": tr("Invalid API key. Please check your API key."),
        "403": tr("Access denied. Your API key may not have the required permissions."),
        "invalid_api_key": tr("Invalid API key. Please check your API key in settings."),
        
        # レート制限
        "rate limit": tr("Rate limit exceeded. Please try again later."),
        "429": tr("Too many requests. Please try again later."),
        
        # モデル関連
        "model": tr("Model error. The selected model may not be available."),
        "model not found": tr("Model not found. Please check the model name."),
        "not supported": tr("This model is not supported."),
        
        # ファイル関連
        "file not found": tr("File not found. Please check the file path."),
        "permission denied": tr("Permission denied. Cannot access the file."),
        
        # メモリ関連
        "out of memory": tr("Out of memory. Try using a smaller model or reducing context size."),
        "memory": tr("Memory error. Try reducing the context size."),
    }
    
    # エラーメッセージをチェック
    for key, message in ERROR_MAPPINGS.items():
        if key in error_str:
            return message
    
    # デフォルトメッセージ
    if context:
        return f"{tr('Error')} {tr(context)}: {str(error)}"
    else:
        return f"{tr('Error')}: {str(error)}"


def format_api_error(provider: str, error: Exception) -> str:
    """
    API プロバイダー固有のエラーメッセージをフォーマット
    
    Args:
        provider: プロバイダー名 ("chatgpt", "ollama", "openrouter", etc.)
        error: 発生したException
        
    Returns:
        フォーマットされたエラーメッセージ
    """
    base_message = get_user_friendly_error_message(error)
    
    # プロバイダー固有の追加情報
    provider_tips = {
        "chatgpt": tr("Make sure you have a valid OpenAI API key."),
        "ollama": tr("Make sure Ollama is running on the specified host and port."),
        "lmstudio": tr("Make sure LM Studio server is running."),
        "openrouter": tr("Check your OpenRouter API key and credits."),
        "local": tr("Make sure the model file exists and is not corrupted.")
    }
    
    tip = provider_tips.get(provider, "")
    if tip:
        return f"{base_message}\n{tip}"
    
    return base_message