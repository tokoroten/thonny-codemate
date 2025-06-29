"""
パフォーマンスモニターのテスト
"""
import pytest
import time
from unittest.mock import patch
from thonnycontrib.thonny_local_ollama.performance_monitor import (
    PerformanceMonitor,
    measure_performance,
    Timer,
    get_performance_stats,
    reset_performance_stats
)


class TestPerformanceMonitor:
    """PerformanceMonitorクラスのテスト"""
    
    def test_record_and_get_stats(self):
        """統計記録と取得のテスト"""
        monitor = PerformanceMonitor()
        
        # 統計を記録
        monitor.record("operation1", 0.1)
        monitor.record("operation1", 0.2)
        monitor.record("operation2", 0.5)
        
        stats = monitor.get_stats()
        
        # operation1の統計確認
        op1_stats = stats["operation1"]
        assert op1_stats["count"] == 2
        assert op1_stats["total_time"] == 0.3
        assert op1_stats["average_time"] == 0.15
        assert op1_stats["min_time"] == 0.1
        assert op1_stats["max_time"] == 0.2
        
        # operation2の統計確認
        op2_stats = stats["operation2"]
        assert op2_stats["count"] == 1
        assert op2_stats["total_time"] == 0.5
    
    @patch('thonnycontrib.thonny_local_ollama.performance_monitor.logger')
    def test_log_stats(self, mock_logger):
        """統計ログ出力のテスト"""
        monitor = PerformanceMonitor()
        monitor.record("test_operation", 0.1)
        
        monitor.log_stats()
        
        # ログが出力されたか確認
        assert mock_logger.info.called
        log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        assert any("Performance Statistics" in call for call in log_calls)
        assert any("test_operation" in call for call in log_calls)


class TestMeasurePerformanceDecorator:
    """measure_performanceデコレーターのテスト"""
    
    def test_measure_with_custom_name(self):
        """カスタム名での計測テスト"""
        reset_performance_stats()
        
        @measure_performance("custom_operation")
        def test_function():
            time.sleep(0.01)  # 10ms
            return "result"
        
        result = test_function()
        assert result == "result"
        
        stats = get_performance_stats()
        assert "custom_operation" in stats
        assert stats["custom_operation"]["count"] == 1
        assert stats["custom_operation"]["average_time"] >= 0.01
    
    def test_measure_with_auto_name(self):
        """自動命名での計測テスト"""
        reset_performance_stats()
        
        @measure_performance()
        def another_test_function():
            time.sleep(0.01)
            return 42
        
        result = another_test_function()
        assert result == 42
        
        stats = get_performance_stats()
        # 関数の完全名が使われる
        expected_name = f"{another_test_function.__module__}.{another_test_function.__name__}"
        assert expected_name in stats
    
    @patch('thonnycontrib.thonny_local_ollama.performance_monitor.logger')
    def test_slow_operation_warning(self, mock_logger):
        """遅い操作の警告テスト"""
        reset_performance_stats()
        
        @measure_performance("slow_operation")
        def slow_function():
            # 実際にsleepする代わりにmockで時間を操作
            pass
        
        # 実行時間を1.5秒に偽装
        with patch('time.time', side_effect=[0, 1.5]):
            slow_function()
        
        # 警告ログが出力されたか確認
        warning_calls = [call for call in mock_logger.warning.call_args_list]
        assert len(warning_calls) > 0
        assert "Slow operation" in warning_calls[0].args[0]


class TestTimer:
    """Timerコンテキストマネージャーのテスト"""
    
    def test_timer_context_manager(self):
        """Timerコンテキストマネージャーのテスト"""
        reset_performance_stats()
        
        with Timer("timer_test"):
            time.sleep(0.01)
        
        stats = get_performance_stats()
        assert "timer_test" in stats
        assert stats["timer_test"]["count"] == 1
        assert stats["timer_test"]["average_time"] >= 0.01
    
    def test_timer_with_exception(self):
        """例外発生時のTimerテスト"""
        reset_performance_stats()
        
        try:
            with Timer("timer_exception_test"):
                time.sleep(0.01)
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # 例外が発生しても統計は記録される
        stats = get_performance_stats()
        assert "timer_exception_test" in stats
        assert stats["timer_exception_test"]["count"] == 1


class TestPerformanceIntegration:
    """パフォーマンス機能の統合テスト"""
    
    def test_multiple_operations(self):
        """複数操作の統計テスト"""
        reset_performance_stats()
        
        @measure_performance("fast_op")
        def fast_operation():
            time.sleep(0.001)
            return "fast"
        
        @measure_performance("medium_op")
        def medium_operation():
            time.sleep(0.005)
            return "medium"
        
        # 複数回実行
        for _ in range(3):
            fast_operation()
        
        for _ in range(2):
            medium_operation()
        
        with Timer("manual_timer"):
            time.sleep(0.002)
        
        stats = get_performance_stats()
        
        # 各操作の統計確認
        assert stats["fast_op"]["count"] == 3
        assert stats["medium_op"]["count"] == 2
        assert stats["manual_timer"]["count"] == 1
        
        # 平均時間の比較（mediumが一番遅いはず）
        assert stats["medium_op"]["average_time"] > stats["fast_op"]["average_time"]