"""
リトライ処理のユーティリティ
ネットワークエラーなどの一時的なエラーに対する再試行機能を提供
"""
import time
import logging
from typing import TypeVar, Callable, Optional, Tuple, Type
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


def retry_on_error(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    log_errors: bool = True
) -> Callable:
    """
    エラー時にリトライするデコレーター
    
    Args:
        max_attempts: 最大試行回数
        delay: 初回リトライまでの待機時間（秒）
        backoff: リトライ間隔の倍率
        exceptions: リトライ対象の例外タプル
        log_errors: エラーをログに記録するか
    
    Returns:
        デコレーターされた関数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception: Optional[Exception] = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        if log_errors:
                            logger.warning(
                                f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {e}"
                                f" Retrying in {current_delay:.1f} seconds..."
                            )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        if log_errors:
                            logger.error(
                                f"{func.__name__} failed after {max_attempts} attempts: {e}"
                            )
            
            # 最後の例外を再発生
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


def retry_network_operation(func: Callable[..., T]) -> Callable[..., T]:
    """
    ネットワーク操作用のリトライデコレーター
    URLError, HTTPError, TimeoutErrorに対してリトライを行う
    """
    import urllib.error
    
    return retry_on_error(
        max_attempts=3,
        delay=1.0,
        backoff=2.0,
        exceptions=(
            urllib.error.URLError,
            urllib.error.HTTPError,
            TimeoutError,
            ConnectionError,
            OSError  # ネットワーク関連のOSError
        ),
        log_errors=True
    )(func)


class RetryableOperation:
    """
    リトライ可能な操作のコンテキストマネージャー
    
    Usage:
        with RetryableOperation(max_attempts=3) as retry:
            while retry.should_retry():
                try:
                    # 操作を実行
                    result = perform_operation()
                    break
                except Exception as e:
                    retry.handle_error(e)
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        self.max_attempts = max_attempts
        self.delay = delay
        self.backoff = backoff
        self.exceptions = exceptions
        self.current_attempt = 0
        self.current_delay = delay
        self.last_exception: Optional[Exception] = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
    
    def should_retry(self) -> bool:
        """まだリトライすべきか判定"""
        return self.current_attempt < self.max_attempts
    
    def handle_error(self, exception: Exception) -> None:
        """エラーを処理し、必要に応じて待機"""
        self.current_attempt += 1
        self.last_exception = exception
        
        if not isinstance(exception, self.exceptions):
            raise exception
        
        if self.current_attempt < self.max_attempts:
            logger.warning(
                f"Operation failed (attempt {self.current_attempt}/{self.max_attempts}): {exception}"
                f" Retrying in {self.current_delay:.1f} seconds..."
            )
            time.sleep(self.current_delay)
            self.current_delay *= self.backoff
        else:
            logger.error(
                f"Operation failed after {self.max_attempts} attempts: {exception}"
            )
            raise exception