"""
エラーハンドリングユーティリティ
詳細なエラー情報の記録とユーザーフレンドリーなメッセージ生成
"""
import logging
import traceback
import functools
import time
from typing import Optional, Callable, Any, Dict
from contextlib import contextmanager

from .i18n import tr

logger = logging.getLogger(__name__)


class ErrorContext:
    """エラーコンテキスト情報を保持するクラス"""
    
    def __init__(self, operation: str, details: Optional[Dict[str, Any]] = None):
        self.operation = operation
        self.details = details or {}
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation,
            "details": self.details,
            "timestamp": self.timestamp
        }


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
    # スタックトレースを取得
    stack_trace = traceback.format_exc()
    
    # 詳細なエラー情報を構築
    error_info = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "operation": context.operation,
        "context_details": context.details,
        "stack_trace": stack_trace
    }
    
    # ログに記録
    logger.log(
        log_level,
        f"Error in {context.operation}: {error_info['error_type']} - {error_info['error_message']}",
        extra={"error_info": error_info}
    )
    logger.debug(f"Stack trace:\n{stack_trace}")
    
    # ユーザー向けメッセージを生成
    if user_message is None:
        user_message = _generate_user_message(error, context)
    
    return user_message


def _generate_user_message(error: Exception, context: ErrorContext) -> str:
    """エラータイプに応じたユーザーフレンドリーなメッセージを生成"""
    
    error_type = type(error).__name__
    operation = context.operation
    
    # 一般的なエラータイプに対するメッセージ
    if isinstance(error, FileNotFoundError):
        return tr("File not found during {}: {}").format(operation, str(error))
    elif isinstance(error, PermissionError):
        return tr("Permission denied during {}: {}").format(operation, str(error))
    elif isinstance(error, ConnectionError):
        return tr("Connection failed during {}: {}").format(operation, str(error))
    elif isinstance(error, TimeoutError):
        return tr("Operation timed out during {}: {}").format(operation, str(error))
    elif isinstance(error, ValueError):
        return tr("Invalid value during {}: {}").format(operation, str(error))
    elif isinstance(error, ImportError):
        return tr("Missing dependency during {}: {}").format(operation, str(error))
    else:
        # その他のエラー
        return tr("Error during {}: {}").format(operation, str(error))


def with_error_handling(
    operation: str,
    show_user_message: bool = True,
    default_return: Any = None
):
    """
    エラーハンドリングを追加するデコレーター
    
    Args:
        operation: 操作の説明
        show_user_message: ユーザーにメッセージを表示するか
        default_return: エラー時のデフォルト戻り値
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            context = ErrorContext(
                operation=operation,
                details={
                    "function": func.__name__,
                    "args": str(args)[:200],  # 長すぎる場合は切り詰め
                    "kwargs": str(kwargs)[:200]
                }
            )
            
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


def retry_network_operation(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (ConnectionError, TimeoutError)
):
    """
    ネットワーク操作用のリトライデコレーター
    
    Args:
        max_attempts: 最大試行回数
        delay: 初回リトライまでの待機時間（秒）
        backoff: リトライごとの待機時間の倍率
        exceptions: リトライ対象の例外タプル
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        logger.info(
                            f"Retrying {func.__name__} (attempt {attempt + 1}/{max_attempts}) "
                            f"after {current_delay}s due to: {e}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        # 最後の試行でも失敗
                        raise
            
            # ここには到達しないはずだが、念のため
            if last_error:
                raise last_error
        
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


class RetryableOperation:
    """リトライ可能な操作を表すクラス"""
    
    def __init__(
        self,
        operation: Callable,
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: tuple = (Exception,)
    ):
        self.operation = operation
        self.max_attempts = max_attempts
        self.delay = delay
        self.backoff = backoff
        self.exceptions = exceptions
    
    def execute(self, *args, **kwargs):
        """操作を実行（必要に応じてリトライ）"""
        last_error = None
        current_delay = self.delay
        
        for attempt in range(self.max_attempts):
            try:
                return self.operation(*args, **kwargs)
            except self.exceptions as e:
                last_error = e
                context = ErrorContext(
                    f"retryable operation (attempt {attempt + 1}/{self.max_attempts})",
                    {"error": str(e)}
                )
                
                if attempt < self.max_attempts - 1:
                    logger.info(f"Retrying after {current_delay}s: {e}")
                    time.sleep(current_delay)
                    current_delay *= self.backoff
                else:
                    log_error_with_context(e, context)
        
        raise last_error