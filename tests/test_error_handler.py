"""
エラーハンドラーのテスト
"""
import pytest
import time
from unittest.mock import Mock, patch
from thonnycontrib.thonny_codemate.utils.unified_error_handler import (
    ErrorContext,
    log_error_with_context,
    with_error_handling,
    retry_decorator as retry_network_operation
)


class TestErrorContext:
    """ErrorContextクラスのテスト"""
    
    def test_error_context_creation(self):
        """ErrorContextの作成テスト"""
        context = ErrorContext("test_operation", {"key": "value"})
        assert context.operation == "test_operation"
        assert context.details == {"key": "value"}
        assert isinstance(context.timestamp, float)
    
    def test_error_context_to_dict(self):
        """ErrorContextのdict変換テスト"""
        context = ErrorContext("test_op", {"test": 123})
        result = context.to_dict()
        assert result["operation"] == "test_op"
        assert result["details"] == {"test": 123}
        assert "timestamp" in result


class TestErrorLogging:
    """エラーログ機能のテスト"""
    
    @patch('thonnycontrib.thonny_codemate.utils.unified_error_handler.logger')
    def test_log_error_with_context(self, mock_logger):
        """コンテキスト付きエラーログのテスト"""
        error = ValueError("Test error")
        context = ErrorContext("test_operation", {"param": "value"})
        
        message = log_error_with_context(error, context)
        
        # ログが記録されたか確認
        assert mock_logger.log.called
        assert mock_logger.debug.called
        assert "Test error" in message
    
    @patch('thonnycontrib.thonny_codemate.utils.unified_error_handler.logger')
    def test_user_message_generation(self, mock_logger):
        """ユーザーメッセージ生成のテスト"""
        # FileNotFoundError
        error = FileNotFoundError("file.txt")
        context = ErrorContext("loading file")
        message = log_error_with_context(error, context)
        assert "File not found" in message
        
        # ConnectionError
        error = ConnectionError("Connection refused")
        context = ErrorContext("API call")
        message = log_error_with_context(error, context)
        assert "Connection failed" in message


class TestErrorHandlingDecorator:
    """エラーハンドリングデコレーターのテスト"""
    
    def test_successful_execution(self):
        """正常実行時のテスト"""
        @with_error_handling("test operation", show_user_message=False)
        def successful_function():
            return "success"
        
        result = successful_function()
        assert result == "success"
    
    @patch('thonnycontrib.thonny_codemate.utils.unified_error_handler.logger')
    def test_error_handling(self, mock_logger):
        """エラー処理のテスト"""
        @with_error_handling("test operation", show_user_message=False, default_return="default")
        def failing_function():
            raise ValueError("Test error")
        
        result = failing_function()
        assert result == "default"
        assert mock_logger.error.called


class TestRetryDecorator:
    """リトライデコレーターのテスト"""
    
    def test_successful_on_first_try(self):
        """初回成功時のテスト"""
        call_count = 0
        
        @retry_network_operation(max_attempts=3)
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = successful_function()
        assert result == "success"
        assert call_count == 1
    
    def test_retry_on_network_error(self):
        """ネットワークエラー時のリトライテスト"""
        call_count = 0
        
        @retry_network_operation(max_attempts=3, delay=0.1, backoff=1.0)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Network error")
            return "success"
        
        start_time = time.time()
        result = flaky_function()
        duration = time.time() - start_time
        
        assert result == "success"
        assert call_count == 3
        assert duration >= 0.2  # 2回のリトライで0.1秒×2
    
    def test_max_retries_exceeded(self):
        """最大リトライ回数超過時のテスト"""
        call_count = 0
        
        @retry_network_operation(max_attempts=3, delay=0.01)
        def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Network error")
        
        with pytest.raises(ConnectionError):
            always_failing_function()
        
        assert call_count == 3


class TestRetryableOperation:
    """RetryableOperationクラスのテスト"""
    
    def test_successful_operation(self):
        """正常実行時のテスト"""
        def operation(x, y):
            return x + y
        
        retryable = RetryableOperation(operation)
        result = retryable.execute(1, 2)
        assert result == 3
    
    def test_retry_with_eventual_success(self):
        """最終的に成功するリトライのテスト"""
        attempt = 0
        
        def flaky_operation():
            nonlocal attempt
            attempt += 1
            if attempt < 3:
                raise ValueError("Temporary error")
            return "success"
        
        retryable = RetryableOperation(
            flaky_operation,
            max_attempts=3,
            delay=0.01,
            exceptions=(ValueError,)
        )
        
        result = retryable.execute()
        assert result == "success"
        assert attempt == 3