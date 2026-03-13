"""
中间件注册器模块

管理中间件的注册、排序和执行。
"""
from typing import List, Dict, Any, Optional, Type
import yaml
from pathlib import Path

from middlewares.base_middleware import BaseMiddleware


class MiddlewareRegistry:
    """
    中间件注册器
    
    负责管理所有中间件的注册、排序和执行。
    中间件按优先级顺序执行,优先级数字越小越先执行。
    """
    
    def __init__(self):
        """初始化中间件注册器"""
        self._middlewares: List[BaseMiddleware] = []
    
    def register(self, middleware: BaseMiddleware) -> None:
        """
        注册中间件
        
        Args:
            middleware: 中间件实例
            
        Raises:
            TypeError: 如果middleware不是BaseMiddleware的实例
        """
        if not isinstance(middleware, BaseMiddleware):
            raise TypeError(f"Middleware must be an instance of BaseMiddleware, got {type(middleware)}")
        
        self._middlewares.append(middleware)
        # 按优先级排序(优先级数字越小越先执行)
        self._middlewares.sort(key=lambda m: m.priority)
    
    def unregister(self, middleware_class: Type[BaseMiddleware]) -> bool:
        """
        注销中间件
        
        Args:
            middleware_class: 中间件类
            
        Returns:
            是否成功注销
        """
        original_count = len(self._middlewares)
        self._middlewares = [m for m in self._middlewares if not isinstance(m, middleware_class)]
        return len(self._middlewares) < original_count
    
    def get_middlewares(self, enabled_only: bool = True) -> List[BaseMiddleware]:
        """
        获取中间件列表
        
        Args:
            enabled_only: 是否只返回启用的中间件,默认True
            
        Returns:
            中间件列表,已按优先级排序
        """
        if enabled_only:
            return [m for m in self._middlewares if m.enabled]
        return self._middlewares.copy()
    
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行请求中间件链
        
        按优先级顺序依次执行所有启用的中间件的process_request方法。
        
        Args:
            request_data: 请求数据字典
            
        Returns:
            处理后的请求数据字典
            
        Raises:
            Exception: 任何中间件处理失败时抛出异常
        """
        data = request_data.copy()
        
        for middleware in self.get_middlewares(enabled_only=True):
            try:
                data = middleware.process_request(data)
            except Exception as e:
                raise Exception(f"Middleware {middleware.__class__.__name__} failed to process request: {str(e)}") from e
        
        return data
    
    def process_response(self, response_data: Dict[str, Any], request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行响应中间件链
        
        按优先级顺序依次执行所有启用的中间件的process_response方法。
        
        Args:
            response_data: 响应数据字典
            request_data: 原始请求数据字典
            
        Returns:
            处理后的响应数据字典
            
        Raises:
            Exception: 任何中间件处理失败时抛出异常
        """
        data = response_data.copy()
        
        for middleware in self.get_middlewares(enabled_only=True):
            try:
                data = middleware.process_response(data, request_data)
            except Exception as e:
                raise Exception(f"Middleware {middleware.__class__.__name__} failed to process response: {str(e)}") from e
        
        return data
    
    def load_from_config(self, config_path: str) -> None:
        """
        从配置文件加载中间件
        
        配置文件格式(YAML):
        middlewares:
          - class: middlewares.logging_middleware.LoggingMiddleware
            priority: 10
            enabled: true
            config:
              log_request: true
              log_response: true
          - class: middlewares.signature_middleware.SignatureMiddleware
            priority: 20
            enabled: true
        
        Args:
            config_path: 配置文件路径
            
        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置格式错误
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Middleware config file not found: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not config or 'middlewares' not in config:
            raise ValueError("Invalid middleware config: 'middlewares' key not found")
        
        for middleware_config in config['middlewares']:
            try:
                # 动态导入中间件类
                class_path = middleware_config.get('class')
                if not class_path:
                    raise ValueError("Middleware config missing 'class' field")
                
                module_path, class_name = class_path.rsplit('.', 1)
                module = __import__(module_path, fromlist=[class_name])
                middleware_class = getattr(module, class_name)
                
                # 创建中间件实例
                priority = middleware_config.get('priority', 100)
                enabled = middleware_config.get('enabled', True)
                middleware_config_data = middleware_config.get('config', {})
                
                middleware = middleware_class(priority=priority, enabled=enabled, **middleware_config_data)
                self.register(middleware)
                
            except Exception as e:
                raise ValueError(f"Failed to load middleware from config: {str(e)}") from e
    
    def clear(self) -> None:
        """清空所有已注册的中间件"""
        self._middlewares.clear()
    
    def __len__(self) -> int:
        """返回已注册的中间件数量"""
        return len(self._middlewares)
    
    def __repr__(self) -> str:
        """返回注册器的字符串表示"""
        return f"MiddlewareRegistry(middlewares={len(self._middlewares)})"
