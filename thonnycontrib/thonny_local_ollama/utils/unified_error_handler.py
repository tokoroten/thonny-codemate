"""
統一エラーハンドリングモジュール
重複していたエラーハンドリング機能を統合
"""
import logging
import traceback
import functools
import time
from typing import Optional, Callable, Any, Dict, Tuple
from contextlib import contextmanager
from ..i18n import tr

logger = logging.getLogger(__name__)


class ErrorContext:
    """エラーコンテキスト情報を保持するクラス"""
    
    def __init__(self, operation: str, details: Optional[Dict[str, Any]] = None):
        self.operation = operation
        self.details = details or {}
        self.timestamp = time.time()
        self.error: Optional[Exception] = None
        self.traceback: Optional[str] = None
    
    def capture_error(self, error: Exception):
        """エラー情報をキャプチャ"""
        self.error = error
        self.traceback = traceback.format_exc()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation,
            "details": self.details,
            "timestamp": self.timestamp,
            "error": str(self.error) if self.error else None,
            "traceback": self.traceback
        }
    
    def get_user_message(self) -> str:
        """ユーザー向けのエラーメッセージを生成"""
        if not self.error:
            return tr("Unknown error occurred")
        
        error_str = str(self.error).lower()
        error_type = type(self.error).__name__
        
        # 特定のエラータイプに対するメッセージ
        if isinstance(self.error, FileNotFoundError):
            return tr("File not found during {}: {}").format(self.operation, str(self.error))
        elif isinstance(self.error, PermissionError):
            return tr("Permission denied during {}: {}").format(self.operation, str(self.error))
        elif isinstance(self.error, ConnectionError) or "connection" in error_str or "urlopen" in error_str:
            return tr("Connection failed during {}: {}").format(self.operation, str(self.error))
        elif isinstance(self.error, TimeoutError) or "timeout" in error_str:
            return tr("Operation timed out during {}: {}").format(self.operation, str(self.error))
        elif isinstance(self.error, ValueError):
            return tr("Invalid value during {}: {}").format(self.operation, str(self.error))
        elif isinstance(self.error, ImportError):
            return tr("Missing dependency during {}: {}").format(self.operation, str(self.error))
        elif isinstance(self.error, MemoryError) or "memory" in error_str or "oom" in error_str:
            return tr("Out of memory. Try using a smaller model or reducing context size.")
        else:
            # その他のエラー
            return tr("Error during {}: {}").format(self.operation, str(self.error))


def log_error_with_context(
    error: Exception,
    context: ErrorContext,
    user_message: Optional[str] = None,
    log_level: int = logging.ERROR
) -> str:
    """
    エラーを詳細なコンテキスト情報と共にログに記録
    
    Args:
        error: 発生したエラー
        context: エラーコンテキスト
        user_message: ユーザーに表示するメッセージ（None の場合は自動生成）
        log_level: ログレベル
        
    Returns:
        ユーザーに表示するメッセージ
    """
    # エラー情報をキャプチャ
    context.capture_error(error)
    
    # ログに記録
    logger.log(
        log_level,
        f"Error in {context.operation}: {type(error).__name__} - {str(error)}",
        extra={"error_context": context.to_dict()}
    )
    
    if context.traceback:
        logger.debug(f"Stack trace:\n{context.traceback}")
    
    # ユーザー向けメッセージを生成
    if user_message is None:
        user_message = context.get_user_message()
    
    return user_message


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
    if "401" in error_str or "unauthorized" in error_str:
        return tr("API key error. Please check your API key in settings.")
    elif "403" in error_str:
        return tr(f"Access forbidden. Please check your {provider} account permissions.")
    elif "404" in error_str or "not found" in error_str:
        return tr(f"API endpoint not found. Please check your {provider} configuration.")
    elif "429" in error_str or "rate limit" in error_str:
        return tr(f"Rate limit exceeded for {provider}. Please wait a moment and try again.")
    elif any(code in error_str for code in ["500", "502", "503"]):
        return tr(f"{provider} server error. Please try again later.")
    
    # 接続エラー
    if "connection" in error_str or "urlopen" in error_str:
        return tr("Connection failed. Please check your internet connection or server settings.")
    
    # タイムアウト
    if "timeout" in error_str:
        return tr("Request timed out. Please try again.")
    
    # モデルエラー
    if "model" in error_str:
        return tr("Model error. Please check if the model is properly loaded.")
    
    # デフォルト
    return tr(f"{provider} error: {str(error)}")


def with_error_handling(
    operation: str,
    show_user_message: bool = True,
    default_return: Any = None,
    details: Optional[Dict[str, Any]] = None
):
    """
    エラーハンドリングを追加するデコレーター
    
    Args:
        operation: 操作の説明
        show_user_message: ユーザーにメッセージを表示するか
        default_return: エラー時のデフォルト戻り値
        details: 追加のコンテキスト情報
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            context_details = details or {}
            context_details.update({
                "function": func.__name__,
                "args": str(args)[:200],  # 長すぎる場合は切り詰め
                "kwargs": str(kwargs)[:200]
            })
            
            context = ErrorContext(operation=operation, details=context_details)
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                user_message = log_error_with_context(e, context)
                
                if show_user_message:
                    # UIスレッドでメッセージボックスを表示
                    try:
                        from tkinter import messagebox
                        messagebox.showerror(tr("Error"), user_message)
                    except:
                        # UIが利用できない場合はログのみ
                        pass
                
                return default_return
        
        return wrapper
    return decorator


@contextmanager
def error_context(operation: str, **details):
    """
    エラーコンテキストを提供するコンテキストマネージャー
    
    使用例:
        with error_context("loading model", model_path=path):
            # モデルロード処理
    """
    context = ErrorContext(operation, details)
    try:
        yield context
    except Exception as e:
        log_error_with_context(e, context)
        raise


def retry_operation(
    func: Callable,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[type, ...] = (Exception,),
    operation_name: Optional[str] = None
) -> Any:
    """
    操作をリトライ付きで実行
    
    Args:
        func: 実行する関数
        max_attempts: 最大試行回数
        delay: 初回リトライまでの待機時間（秒）
        backoff: リトライごとの待機時間の倍率
        exceptions: リトライ対象の例外タプル
        operation_name: 操作名（ログ用）
        
    Returns:
        関数の実行結果
        
    Raises:
        最後の試行でも失敗した場合は例外を再発生
    """
    operation_name = operation_name or func.__name__
    last_error = None
    current_delay = delay
    
    for attempt in range(max_attempts):
        try:
            return func()
        except exceptions as e:
            last_error = e
            context = ErrorContext(
                f"{operation_name} (attempt {attempt + 1}/{max_attempts})",
                {"error": str(e)}
            )
            
            if attempt < max_attempts - 1:
                logger.info(
                    f"Retrying {operation_name} after {current_delay}s due to: {e}"
                )
                time.sleep(current_delay)
                current_delay *= backoff
            else:
                log_error_with_context(e, context)
    
    raise last_error


def retry_decorator(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[type, ...] = (ConnectionError, TimeoutError)
):
    """
    リトライ機能を追加するデコレーター
    
    Args:
        max_attempts: 最大試行回数
        delay: 初回リトライまでの待機時間（秒）
        backoff: リトライごとの待機時間の倍率
        exceptions: リトライ対象の例外タプル
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return retry_operation(
                lambda: func(*args, **kwargs),
                max_attempts=max_attempts,
                delay=delay,
                backoff=backoff,
                exceptions=exceptions,
                operation_name=func.__name__
            )
        return wrapper
    return decorator


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
            context = ErrorContext("safe_execute", {"function": str(func)})
            log_error_with_context(e, context, log_level=logging.WARNING)
        return default_value