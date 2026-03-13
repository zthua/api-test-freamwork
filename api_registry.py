"""
API注册器

提供API的注册、发现和管理功能，支持：
- 动态注册API实现
- API实例创建和缓存
- API配置管理
"""

from typing import Dict, Type, Optional, Any
from api.base_api import BaseAPI
from utils.config_manager import ConfigManager
from utils.logger import Logger


class APIRegistry:
    """
    API注册器
    
    管理所有已注册的API实现，提供统一的API访问接口。
    """
    
    def __init__(self, config: ConfigManager, logger: Logger = None):
        """
        初始化API注册器
        
        Args:
            config: 配置管理器
            logger: 日志记录器
        """
        self.config = config
        self.logger = logger or Logger(name="APIRegistry")
        
        # API类注册表: {api_name: API_Class}
        self._api_classes: Dict[str, Type[BaseAPI]] = {}
        
        # API实例缓存: {api_name: api_instance}
        self._api_instances: Dict[str, BaseAPI] = {}
        
        self.logger.info("APIRegistry initialized")
    
    def register(self, api_name: str, api_class: Type[BaseAPI]) -> None:
        """
        注册API实现类
        
        Args:
            api_name: API名称（唯一标识）
            api_class: API实现类（必须继承BaseAPI）
            
        Raises:
            ValueError: API名称已存在或API类不是BaseAPI的子类
        """
        if api_name in self._api_classes:
            raise ValueError(f"API '{api_name}' already registered")
        
        if not issubclass(api_class, BaseAPI):
            raise ValueError(f"API class must inherit from BaseAPI")
        
        self._api_classes[api_name] = api_class
        self.logger.info(f"Registered API: {api_name} -> {api_class.__name__}")
    
    def unregister(self, api_name: str) -> None:
        """
        注销API实现
        
        Args:
            api_name: API名称
        """
        if api_name in self._api_classes:
            del self._api_classes[api_name]
            self.logger.info(f"Unregistered API: {api_name}")
        
        # 同时清理实例缓存
        if api_name in self._api_instances:
            instance = self._api_instances[api_name]
            instance.close()
            del self._api_instances[api_name]
    
    def get_api(self, api_name: str, use_cache: bool = True, **kwargs) -> BaseAPI:
        """
        获取API实例
        
        Args:
            api_name: API名称
            use_cache: 是否使用缓存的实例
            **kwargs: 传递给API构造函数的额外参数
            
        Returns:
            API实例
            
        Raises:
            ValueError: API未注册
        """
        if api_name not in self._api_classes:
            raise ValueError(f"API '{api_name}' not registered. Available APIs: {list(self._api_classes.keys())}")
        
        # 如果使用缓存且实例已存在，直接返回
        if use_cache and api_name in self._api_instances:
            return self._api_instances[api_name]
        
        # 创建新实例
        api_class = self._api_classes[api_name]
        
        # 合并配置和额外参数
        init_params = {
            'config': self.config,
            'logger': Logger(name=api_name),
            **kwargs
        }
        
        instance = api_class(**init_params)
        
        # 缓存实例
        if use_cache:
            self._api_instances[api_name] = instance
        
        self.logger.info(f"Created API instance: {api_name}")
        
        return instance
    
    def list_apis(self) -> Dict[str, Type[BaseAPI]]:
        """
        列出所有已注册的API
        
        Returns:
            API名称到API类的映射
        """
        return self._api_classes.copy()
    
    def has_api(self, api_name: str) -> bool:
        """
        检查API是否已注册
        
        Args:
            api_name: API名称
            
        Returns:
            是否已注册
        """
        return api_name in self._api_classes
    
    def close_all(self) -> None:
        """关闭所有缓存的API实例"""
        for api_name, instance in self._api_instances.items():
            try:
                instance.close()
                self.logger.info(f"Closed API instance: {api_name}")
            except Exception as e:
                self.logger.error(f"Error closing API instance {api_name}: {e}")
        
        self._api_instances.clear()
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close_all()
    
    def __repr__(self) -> str:
        """返回注册器的字符串表示"""
        return f"APIRegistry(registered_apis={list(self._api_classes.keys())})"


# 全局API注册器实例（可选）
_global_registry: Optional[APIRegistry] = None


def get_global_registry(config: ConfigManager = None) -> APIRegistry:
    """
    获取全局API注册器实例
    
    Args:
        config: 配置管理器（首次调用时必需）
        
    Returns:
        全局API注册器实例
        
    Raises:
        ValueError: 首次调用时未提供config
    """
    global _global_registry
    
    if _global_registry is None:
        if config is None:
            raise ValueError("Config is required for first-time initialization")
        _global_registry = APIRegistry(config)
    
    return _global_registry


def register_builtin_apis(registry: APIRegistry) -> None:
    """
    注册内置的API实现
    
    Args:
        registry: API注册器
    """
    # 导入内置API实现
    from api.createpay_api import CreatePayAPI
    
    # 注册
    registry.register('createpay', CreatePayAPI)
    
    # 可以在这里注册更多内置API
    # registry.register('refund', RefundAPI)
    # registry.register('query', QueryAPI)
