"""
重试中间件模块

在请求失败时自动重试,支持配置重试次数和退避策略。
"""
from typing import Dict, Any, List
import time

from middlewares.base_middleware import BaseMiddleware
from utils.logger import Logger


class RetryMiddleware(BaseMiddleware):
    """
    重试中间件
    
    当HTTP请求失败时自动重试,支持配置重试次数、退避策略和需要重试的状态码。
    注意:此中间件主要在响应处理阶段标记是否需要重试,实际重试逻辑由HTTPClient实现。
    """
    
    def __init__(self, priority: int = 30, enabled: bool = True, **kwargs):
        """
        初始化重试中间件
        
        Args:
            priority: 中间件优先级,默认30
            enabled: 是否启用,默认True
            **kwargs: 配置参数
                - max_retries: 最大重试次数,默认3
                - retry_status_codes: 需要重试的HTTP状态码列表,默认[500, 502, 503, 504]
                - backoff_factor: 退避因子,默认1.0(重试间隔=backoff_factor * (2 ** retry_count))
                - max_backoff: 最大退避时间(秒),默认60
        """
        super().__init__(priority, enabled, **kwargs)
        self.logger = Logger()
        
        self.max_retries = kwargs.get('max_retries', 3)
        self.retry_status_codes = kwargs.get('retry_status_codes', [500, 502, 503, 504])
        self.backoff_factor = kwargs.get('backoff_factor', 1.0)
        self.max_backoff = kwargs.get('max_backoff', 60)
    
    def _calculate_backoff_time(self, retry_count: int) -> float:
        """
        计算退避时间
        
        使用指数退避策略: backoff_time = backoff_factor * (2 ** retry_count)
        
        Args:
            retry_count: 当前重试次数
            
        Returns:
            退避时间(秒)
        """
        backoff_time = self.backoff_factor * (2 ** retry_count)
        return min(backoff_time, self.max_backoff)
    
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理请求:初始化重试计数器
        
        Args:
            request_data: 请求数据字典
            
        Returns:
            添加重试配置的请求数据
        """
        # 在请求数据中添加重试配置
        request_data['_retry_config'] = {
            'max_retries': self.max_retries,
            'retry_count': 0,
            'retry_status_codes': self.retry_status_codes,
            'backoff_factor': self.backoff_factor,
            'max_backoff': self.max_backoff
        }
        
        return request_data
    
    def process_response(self, response_data: Dict[str, Any], request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理响应:判断是否需要重试
        
        Args:
            response_data: 响应数据字典
            request_data: 原始请求数据字典
            
        Returns:
            添加重试标记的响应数据
        """
        # 获取重试配置
        retry_config = request_data.get('_retry_config', {})
        retry_count = retry_config.get('retry_count', 0)
        max_retries = retry_config.get('max_retries', self.max_retries)
        retry_status_codes = retry_config.get('retry_status_codes', self.retry_status_codes)
        
        # 获取响应状态码
        status_code = response_data.get('status_code')
        
        # 判断是否需要重试
        should_retry = False
        if status_code in retry_status_codes and retry_count < max_retries:
            should_retry = True
            
            # 计算退避时间
            backoff_time = self._calculate_backoff_time(retry_count)
            
            self.logger.warning(
                f"Request failed with status code {status_code}, "
                f"will retry ({retry_count + 1}/{max_retries}) after {backoff_time:.2f}s"
            )
            
            # 标记需要重试
            response_data['_should_retry'] = True
            response_data['_retry_count'] = retry_count + 1
            response_data['_backoff_time'] = backoff_time
        else:
            if status_code in retry_status_codes and retry_count >= max_retries:
                self.logger.error(
                    f"Request failed with status code {status_code}, "
                    f"max retries ({max_retries}) exceeded"
                )
            
            response_data['_should_retry'] = False
        
        return response_data
