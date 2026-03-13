"""
并发执行器模块

支持多线程并发执行测试用例,统计性能指标:
- TPS(每秒事务数)
- 响应时间分布(P50/P95/P99)
- 数据隔离
"""

import time
import threading
from typing import Callable, List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import statistics


class ConcurrentExecutor:
    """并发执行器类"""
    
    def __init__(self, workers: int = 10):
        """
        初始化并发执行器
        
        Args:
            workers: 并发线程数,默认10
        """
        self.workers = workers
        self.results = []
        self.response_times = []
        self.start_time = None
        self.end_time = None
        self.lock = threading.Lock()
        self.errors = []
    
    def execute(self, func: Callable, data_list: List[Any], **kwargs) -> List[Dict[str, Any]]:
        """
        并发执行函数
        
        Args:
            func: 要执行的函数
            data_list: 数据列表,每个元素作为函数参数
            **kwargs: 传递给函数的额外关键字参数
            
        Returns:
            执行结果列表,每个元素包含:
            - success: 是否成功
            - result: 执行结果
            - response_time: 响应时间(秒)
            - error: 错误信息(如果失败)
        """
        self.results = []
        self.response_times = []
        self.errors = []
        self.start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            # 提交所有任务
            futures = []
            for data in data_list:
                future = executor.submit(self._execute_single, func, data, **kwargs)
                futures.append(future)
            
            # 收集结果
            for future in as_completed(futures):
                try:
                    result = future.result()
                    with self.lock:
                        self.results.append(result)
                        if result['success']:
                            self.response_times.append(result['response_time'])
                        else:
                            self.errors.append(result)
                except Exception as e:
                    with self.lock:
                        error_result = {
                            'success': False,
                            'result': None,
                            'response_time': 0,
                            'error': str(e)
                        }
                        self.results.append(error_result)
                        self.errors.append(error_result)
        
        self.end_time = time.time()
        return self.results
    
    def _execute_single(self, func: Callable, data: Any, **kwargs) -> Dict[str, Any]:
        """
        执行单个任务
        
        Args:
            func: 要执行的函数
            data: 函数参数
            **kwargs: 额外关键字参数
            
        Returns:
            执行结果字典
        """
        start = time.time()
        try:
            # 如果data是字典,解包为关键字参数
            if isinstance(data, dict):
                result = func(**data, **kwargs)
            else:
                result = func(data, **kwargs)
            
            end = time.time()
            return {
                'success': True,
                'result': result,
                'response_time': end - start,
                'error': None
            }
        except Exception as e:
            end = time.time()
            return {
                'success': False,
                'result': None,
                'response_time': end - start,
                'error': str(e)
            }
    
    def get_tps(self) -> float:
        """
        计算TPS(每秒事务数)
        
        Returns:
            TPS值
        """
        if not self.start_time or not self.end_time:
            return 0.0
        
        duration = self.end_time - self.start_time
        if duration == 0:
            return 0.0
        
        total_requests = len(self.results)
        return total_requests / duration
    
    def get_response_time_percentile(self, percentile: int) -> float:
        """
        计算响应时间百分位
        
        Args:
            percentile: 百分位值(50/95/99)
            
        Returns:
            响应时间(秒)
        """
        if not self.response_times:
            return 0.0
        
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * percentile / 100)
        if index >= len(sorted_times):
            index = len(sorted_times) - 1
        
        return sorted_times[index]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取完整统计信息
        
        Returns:
            统计信息字典,包含:
            - total_requests: 总请求数
            - successful_requests: 成功请求数
            - failed_requests: 失败请求数
            - success_rate: 成功率
            - tps: TPS
            - avg_response_time: 平均响应时间
            - min_response_time: 最小响应时间
            - max_response_time: 最大响应时间
            - p50: P50响应时间
            - p95: P95响应时间
            - p99: P99响应时间
            - duration: 总执行时间
        """
        total = len(self.results)
        successful = len([r for r in self.results if r['success']])
        failed = total - successful
        
        stats = {
            'total_requests': total,
            'successful_requests': successful,
            'failed_requests': failed,
            'success_rate': successful / total if total > 0 else 0.0,
            'tps': self.get_tps(),
            'duration': self.end_time - self.start_time if self.start_time and self.end_time else 0.0
        }
        
        if self.response_times:
            stats.update({
                'avg_response_time': statistics.mean(self.response_times),
                'min_response_time': min(self.response_times),
                'max_response_time': max(self.response_times),
                'p50': self.get_response_time_percentile(50),
                'p95': self.get_response_time_percentile(95),
                'p99': self.get_response_time_percentile(99)
            })
        else:
            stats.update({
                'avg_response_time': 0.0,
                'min_response_time': 0.0,
                'max_response_time': 0.0,
                'p50': 0.0,
                'p95': 0.0,
                'p99': 0.0
            })
        
        return stats
    
    def get_errors(self) -> List[Dict[str, Any]]:
        """
        获取所有错误信息
        
        Returns:
            错误列表
        """
        return self.errors
    
    def clear(self):
        """清空执行结果"""
        self.results = []
        self.response_times = []
        self.errors = []
        self.start_time = None
        self.end_time = None
