"""
中间件基类模块

定义中间件的抽象基类,所有中间件必须继承此类并实现process_request和process_response方法。
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseMiddleware(ABC):
    """
    中间件抽象基类
    
    所有中间件必须继承此类并实现process_request和process_response方法。
    中间件按优先级顺序执行,优先级数字越小越先执行。
    """
    
    def __init__(self, priority: int = 100, enabled: bool = True, **kwargs):
        """
        初始化中间件
        
        Args:
            priority: 中间件优先级,数字越小优先级越高,默认100
            enabled: 是否启用此中间件,默认True
            **kwargs: 其他配置参数
        """
        self._priority = priority
        self._enabled = enabled
        self._config = kwargs
    
    @property
    def priority(self) -> int:
        """获取中间件优先级"""
        return self._priority
    
    @property
    def enabled(self) -> bool:
        """获取中间件启用状态"""
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool):
        """设置中间件启用状态"""
        self._enabled = value
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取中间件配置"""
        return self._config
    
    @abstractmethod
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理请求数据
        
        在发送HTTP请求之前调用,可以修改请求数据、添加签名、记录日志等。
        
        Args:
            request_data: 请求数据字典,包含url、headers、body等
            
        Returns:
            处理后的请求数据字典
            
        Raises:
            Exception: 处理失败时抛出异常
        """
        pass
    
    @abstractmethod
    def process_response(self, response_data: Dict[str, Any], request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理响应数据
        
        在接收到HTTP响应之后调用,可以验证签名、记录日志、统计性能等。
        
        Args:
            response_data: 响应数据字典,包含status_code、headers、body等
            request_data: 原始请求数据字典
            
        Returns:
            处理后的响应数据字典
            
        Raises:
            Exception: 处理失败时抛出异常
        """
        pass
    
    def __repr__(self) -> str:
        """返回中间件的字符串表示"""
        return f"{self.__class__.__name__}(priority={self._priority}, enabled={self._enabled})"
