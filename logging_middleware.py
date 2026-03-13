"""
日志中间件模块

记录HTTP请求和响应的详细信息,支持敏感信息脱敏。
"""
from typing import Dict, Any, List
import json
import time

from middlewares.base_middleware import BaseMiddleware
from utils.logger import Logger


class LoggingMiddleware(BaseMiddleware):
    """
    日志中间件
    
    记录HTTP请求和响应的详细信息,包括URL、headers、body等。
    支持配置是否记录请求/响应,以及敏感字段脱敏。
    """
    
    def __init__(self, priority: int = 10, enabled: bool = True, **kwargs):
        """
        初始化日志中间件
        
        Args:
            priority: 中间件优先级,默认10(较高优先级)
            enabled: 是否启用,默认True
            **kwargs: 配置参数
                - log_request: 是否记录请求,默认True
                - log_response: 是否记录响应,默认True
                - sensitive_fields: 需要脱敏的字段列表,默认['password', 'private_key', 'secret']
                - log_level: 日志级别,默认'info'
        """
        super().__init__(priority, enabled, **kwargs)
        self.logger = Logger()
        self.log_request = kwargs.get('log_request', True)
        self.log_response = kwargs.get('log_response', True)
        self.sensitive_fields = kwargs.get('sensitive_fields', ['password', 'private_key', 'secret', 'sign'])
        self.log_level = kwargs.get('log_level', 'info')
    
    def _mask_sensitive_data(self, data: Any) -> Any:
        """
        脱敏敏感数据
        
        Args:
            data: 需要脱敏的数据
            
        Returns:
            脱敏后的数据
        """
        if isinstance(data, dict):
            masked_data = {}
            for key, value in data.items():
                if any(field in key.lower() for field in self.sensitive_fields):
                    # 脱敏处理:只显示前3个和后3个字符
                    if isinstance(value, str) and len(value) > 6:
                        masked_data[key] = f"{value[:3]}***{value[-3:]}"
                    else:
                        masked_data[key] = "***"
                else:
                    masked_data[key] = self._mask_sensitive_data(value)
            return masked_data
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        else:
            return data
    
    def _format_data(self, data: Dict[str, Any]) -> str:
        """
        格式化数据为JSON字符串
        
        Args:
            data: 数据字典
            
        Returns:
            格式化后的JSON字符串
        """
        try:
            masked_data = self._mask_sensitive_data(data)
            return json.dumps(masked_data, ensure_ascii=False, indent=2)
        except Exception:
            return str(data)
    
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理请求:记录请求信息
        
        Args:
            request_data: 请求数据字典
            
        Returns:
            原始请求数据(不修改)
        """
        if not self.log_request:
            return request_data
        
        # 记录请求开始时间
        request_data['_start_time'] = time.time()
        
        # 构建日志消息
        log_message = f"\n{'='*80}\n"
        log_message += f"HTTP REQUEST\n"
        log_message += f"{'='*80}\n"
        log_message += f"URL: {request_data.get('url', 'N/A')}\n"
        log_message += f"Method: {request_data.get('method', 'POST')}\n"
        
        if 'headers' in request_data:
            log_message += f"Headers:\n{self._format_data(request_data['headers'])}\n"
        
        if 'body' in request_data:
            log_message += f"Body:\n{self._format_data(request_data['body'])}\n"
        
        log_message += f"{'='*80}\n"
        
        # 根据配置的日志级别记录
        if self.log_level == 'debug':
            self.logger.debug(log_message)
        else:
            self.logger.info(log_message)
        
        return request_data
    
    def process_response(self, response_data: Dict[str, Any], request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理响应:记录响应信息和耗时
        
        Args:
            response_data: 响应数据字典
            request_data: 原始请求数据字典
            
        Returns:
            原始响应数据(不修改)
        """
        if not self.log_response:
            return response_data
        
        # 计算请求耗时
        elapsed_time = 0
        if '_start_time' in request_data:
            elapsed_time = time.time() - request_data['_start_time']
        
        # 构建日志消息
        log_message = f"\n{'='*80}\n"
        log_message += f"HTTP RESPONSE\n"
        log_message += f"{'='*80}\n"
        log_message += f"Status Code: {response_data.get('status_code', 'N/A')}\n"
        log_message += f"Elapsed Time: {elapsed_time:.3f}s\n"
        
        if 'headers' in response_data:
            log_message += f"Headers:\n{self._format_data(response_data['headers'])}\n"
        
        if 'body' in response_data:
            log_message += f"Body:\n{self._format_data(response_data['body'])}\n"
        
        log_message += f"{'='*80}\n"
        
        # 根据配置的日志级别记录
        if self.log_level == 'debug':
            self.logger.debug(log_message)
        else:
            self.logger.info(log_message)
        
        return response_data
