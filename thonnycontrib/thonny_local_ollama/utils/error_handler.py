"""
エラーハンドリングのユーティリティ
統一的なエラー処理とユーザーフレンドリーなメッセージ生成
"""
import logging
import traceback
from typing import Optional, Dict, Any, Callable
from functools import wraps

logger = logging.getLogger(__name__)


class ErrorContext:
    """エラーコンテキスト情報を保持するクラス"""
    
    def __init__(self, operation: str, details: Optional[Dict[str, Any]] = None):
        self.operation = operation
        self.details = details or {}
        self.error: Optional[Exception] = None
        self.traceback: Optional[str] = None
    
    def capture_error(self, error: Exception):
        """エラー情報をキャプチャ"""
        self.error = error
        self.traceback = traceback.format_exc()
        
        # ログに記録
        logger.error(
            f"Error in {self.operation}: {error}\n"
            f"Context: {self.details}\n"
            f"Traceback:\n{self.traceback}"
        )
    
    def get_user_message(self, translate_func: Optional[Callable] = None) -> str:
        """ユーザー向けのエラーメッセージを生成"""
        if not self.error:
            return "Unknown error occurred"
        
        tr = translate_func or (lambda x: x)
        error_str = str(self.error).lower()
        
        # エラータイプに応じたメッセージ
        if "connection" in error_str or "urlopen" in error_str:
            base_msg = "Connection error. Please check your network and server status."
        elif "api key" in error_str or "401" in error_str or "unauthorized" in error_str:
            base_msg = "Authentication error. Please check your API key."
        elif "404" in error_str or "not found" in error_str:
            base_msg = "Resource not found. Please check your settings."
        elif "rate limit" in error_str or "429" in error_str:
            base_msg = "Rate limit exceeded. Please wait and try again."
        elif "timeout" in error_str:
            base_msg = "Request timed out. Please try again."
        elif "model" in error_str:
            base_msg = "Model error. Please check if the model is available."
        elif "memory" in error_str or "oom" in error_str:
            base_msg = "Out of memory. Try using a smaller model or reducing context size."
        elif "permission" in error_str or "access denied" in error_str:
            base_msg = "Permission denied. Please check file/folder permissions."
        else:
            # 一般的なエラー
            base_msg = f"Error in {self.operation}: {str(self.error)}"
        
        return tr(base_msg)


def with_error_context(operation: str, details: Optional[Dict[str, Any]] = None):
    """
    エラーコンテキスト付きのデコレーター
    
    Args:
        operation: 操作の説明
        details: 追加のコンテキスト情報
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            context = ErrorContext(operation, details)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context.capture_error(e)
                # コンテキスト情報を含む新しい例外を発生
                raise RuntimeError(f"Error in {operation}: {str(e)}") from e
        return wrapper
    return decorator


def handle_api_error(error: Exception, provider: str) -> str:
    """
    API エラーを処理してユーザーフレンドリーなメッセージを返す
    
    Args:
        error: 発生したエラー
        provider: APIプロバイダー名
        
    Returns:
        ユーザー向けのエラーメッセージ
    """
    error_str = str(error).lower()
    
    # HTTPステータスコードのチェック
    if "401" in error_str:
        return f"Invalid {provider} API key. Please check your API key in settings."
    elif "403" in error_str:
        return f"Access forbidden. Please check your {provider} account permissions."
    elif "404" in error_str:
        return f"API endpoint not found. Please check your {provider} configuration."
    elif "429" in error_str:
        return f"Rate limit exceeded for {provider}. Please wait a moment and try again."
    elif "500" in error_str or "502" in error_str or "503" in error_str:
        return f"{provider} server error. Please try again later."
    
    # 接続エラー
    if "connection" in error_str or "urlopen" in error_str:
        return f"Cannot connect to {provider}. Please check your internet connection."
    
    # タイムアウト
    if "timeout" in error_str:
        return f"Request to {provider} timed out. Please try again."
    
    # デフォルト
    return f"{provider} error: {str(error)}"


def safe_execute(func: Callable, default_value: Any = None, log_errors: bool = True):
    """
    関数を安全に実行し、エラー時はデフォルト値を返す
    
    Args:
        func: 実行する関数
        default_value: エラー時のデフォルト値
        log_errors: エラーをログに記録するか
        
    Returns:
        関数の実行結果またはデフォルト値
    """
    try:
        return func()
    except Exception as e:
        if log_errors:
            logger.error(f"Error in safe_execute: {e}\n{traceback.format_exc()}")
        return default_value