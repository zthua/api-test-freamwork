"""
性能统计中间件模块

统计HTTP请求的响应时间和性能指标,支持性能告警。
"""
from typing import Dict, Any, List
import time
import statistics

from middlewares.base_middleware import BaseMiddleware
from utils.logger import Logger


class PerformanceMiddleware(BaseMiddleware):
    """
    性能统计中间件
    
    统计HTTP请求的响应时间,计算性能指标(P50/P95/P99),并支持性能告警。
    """
    
    def __init__(self, priority: int = 40, enabled: bool = True, **kwargs):
        """
        初始化性能统计中间件
        
        Args:
            priority: 中间件优先级,默认40
            enabled: 是否启用,默认True
            **kwargs: 配置参数
                - enable_alert: 是否启用性能告警,默认False
                - alert_threshold: 告警阈值(秒),默认5.0
                - collect_metrics: 是否收集性能指标,默认True
                - max_samples: 最大样本数,默认1000
        """
        super().__init__(priority, enabled, **kwargs)
        self.logger = Logger()
        
        self.enable_alert = kwargs.get('enable_alert', False)
        self.alert_threshold = kwargs.get('alert_threshold', 5.0)
        self.collect_metrics = kwargs.get('collect_metrics', True)
        self.max_samples = kwargs.get('max_samples', 1000)
        
        # 存储响应时间样本
        self._response_times: List[float] = []
    
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理请求:记录请求开始时间
        
        Args:
            request_data: 请求数据字典
            
        Returns:
            添加开始时间的请求数据
        """
        request_data['_perf_start_time'] = time.time()
        return request_data
    
    def process_response(self, response_data: Dict[str, Any], request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理响应:计算响应时间并收集性能指标
        
        Args:
            response_data: 响应数据字典
            request_data: 原始请求数据字典
            
        Returns:
            添加性能指标的响应数据
        """
        # 计算响应时间
        start_time = request_data.get('_perf_start_time')
        if start_time is None:
            self.logger.warning("Request start time not found, skip performance statistics")
            return response_data
        
        elapsed_time = time.time() - start_time
        response_data['_elapsed_time'] = elapsed_time
        
        # 收集性能指标
        if self.collect_metrics:
            self._response_times.append(elapsed_time)
            
            # 限制样本数量,避免内存溢出
            if len(self._response_times) > self.max_samples:
                self._response_times = self._response_times[-self.max_samples:]
        
        # 性能告警
        if self.enable_alert and elapsed_time > self.alert_threshold:
            self.logger.warning(
                f"Performance alert: Request took {elapsed_time:.3f}s, "
                f"exceeds threshold {self.alert_threshold}s"
            )
            response_data['_performance_alert'] = True
        
        # 记录性能日志
        self.logger.debug(f"Request completed in {elapsed_time:.3f}s")
        
        return response_data
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Returns:
            性能统计字典,包含:
                - total_requests: 总请求数
                - avg_response_time: 平均响应时间
                - min_response_time: 最小响应时间
                - max_response_time: 最大响应时间
                - p50: 50分位响应时间
                - p95: 95分位响应时间
                - p99: 99分位响应时间
        """
        if not self._response_times:
            return {
                'total_requests': 0,
                'avg_response_time': 0,
                'min_response_time': 0,
                'max_response_time': 0,
                'p50': 0,
                'p95': 0,
                'p99': 0
            }
        
        sorted_times = sorted(self._response_times)
        total = len(sorted_times)
        
        return {
            'total_requests': total,
            'avg_response_time': statistics.mean(sorted_times),
            'min_response_time': min(sorted_times),
            'max_response_time': max(sorted_times),
            'p50': self._calculate_percentile(sorted_times, 50),
            'p95': self._calculate_percentile(sorted_times, 95),
            'p99': self._calculate_percentile(sorted_times, 99)
        }
    
    def _calculate_percentile(self, sorted_data: List[float], percentile: int) -> float:
        """
        计算百分位数
        
        Args:
            sorted_data: 已排序的数据列表
            percentile: 百分位(0-100)
            
        Returns:
            百分位值
        """
        if not sorted_data:
            return 0.0
        
        index = (len(sorted_data) - 1) * percentile / 100
        lower_index = int(index)
        upper_index = min(lower_index + 1, len(sorted_data) - 1)
        
        # 线性插值
        weight = index - lower_index
        return sorted_data[lower_index] * (1 - weight) + sorted_data[upper_index] * weight
    
    def reset_statistics(self) -> None:
        """重置性能统计数据"""
        self._response_times.clear()
        self.logger.info("Performance statistics reset")
    
    def get_response_times(self) -> List[float]:
        """
        获取所有响应时间样本
        
        Returns:
            响应时间列表
        """
        return self._response_times.copy()
