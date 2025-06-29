"""
パフォーマンスモニタリングユーティリティ
実行時間の計測とボトルネックの特定
"""
import time
import functools
import logging
from typing import Callable, Dict, Any
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """パフォーマンス統計を収集するクラス"""
    
    def __init__(self):
        self.stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0
        })
        self._lock = threading.Lock()
    
    def record(self, operation: str, duration: float):
        """操作の実行時間を記録"""
        with self._lock:
            stat = self.stats[operation]
            stat['count'] += 1
            stat['total_time'] += duration
            stat['min_time'] = min(stat['min_time'], duration)
            stat['max_time'] = max(stat['max_time'], duration)
    
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """統計情報を取得"""
        with self._lock:
            result = {}
            for operation, stat in self.stats.items():
                if stat['count'] > 0:
                    result[operation] = {
                        'count': stat['count'],
                        'total_time': stat['total_time'],
                        'average_time': stat['total_time'] / stat['count'],
                        'min_time': stat['min_time'],
                        'max_time': stat['max_time']
                    }
            return result
    
    def log_stats(self):
        """統計情報をログに出力"""
        stats = self.get_stats()
        if not stats:
            return
        
        logger.info("=== Performance Statistics ===")
        for operation, stat in sorted(stats.items(), key=lambda x: x[1]['total_time'], reverse=True):
            logger.info(
                f"{operation}: "
                f"count={stat['count']}, "
                f"avg={stat['average_time']*1000:.2f}ms, "
                f"min={stat['min_time']*1000:.2f}ms, "
                f"max={stat['max_time']*1000:.2f}ms, "
                f"total={stat['total_time']:.2f}s"
            )


# グローバルインスタンス
_monitor = PerformanceMonitor()


def measure_performance(operation: str = None):
    """
    パフォーマンスを計測するデコレーター
    
    Args:
        operation: 操作名（None の場合は関数名を使用）
    """
    def decorator(func: Callable) -> Callable:
        op_name = operation or f"{func.__module__}.{func.__name__}"
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                _monitor.record(op_name, duration)
                
                # 遅い操作を警告
                if duration > 1.0:
                    logger.warning(f"Slow operation: {op_name} took {duration:.2f}s")
        
        return wrapper
    return decorator


class Timer:
    """コンテキストマネージャーとして使用できるタイマー"""
    
    def __init__(self, operation: str):
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            _monitor.record(self.operation, duration)


def get_performance_stats() -> Dict[str, Dict[str, Any]]:
    """現在のパフォーマンス統計を取得"""
    return _monitor.get_stats()


def log_performance_stats():
    """パフォーマンス統計をログに出力"""
    _monitor.log_stats()


def reset_performance_stats():
    """パフォーマンス統計をリセット"""
    global _monitor
    _monitor = PerformanceMonitor()


# 使用例:
# @measure_performance()
# def slow_function():
#     time.sleep(1)
#
# with Timer("database_query"):
#     # データベースクエリ実行
#     pass