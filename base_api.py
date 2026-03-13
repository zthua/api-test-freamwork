"""
通用API基类

提供所有API接口的基础功能:
- HTTP请求封装
- 认证处理（支持多种认证方式）
- 请求/响应处理
- 中间件集成
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from attrs import define, field

from utils.http_client import HTTPClient
from utils.config_manager import ConfigManager
from utils.middleware_registry import MiddlewareRegistry
from utils.logger import Logger


@define
class BaseAPI(ABC):
    """
    API基类
    
    所有具体API实现都应继承此类，并实现抽象方法。
    提供统一的接口调用模式和扩展点。
    """
    
    # 必需组件
    config: ConfigManager = field()
    logger: Logger = field(default=None)
    
    # 可选组件
    http_client: Optional[HTTPClient] = field(default=None)
    middleware_registry: Optional[MiddlewareRegistry] = field(default=None)
    
    # API配置
    api_name: str = field(default="base_api")
    base_url: Optional[str] = field(default=None)
    
    def __attrs_post_init__(self):
        """初始化后处理"""
        # 如果没有提供logger,创建默认logger
        if self.logger is None:
            self.logger = Logger(name=self.api_name)
        
        # 如果没有提供base_url,从配置中获取
        if self.base_url is None:
            self.base_url = self.config.get(f'{self.api_name}.base_url') or self.config.get('api.base_url')
        
        # 如果没有提供http_client,创建默认http_client
        if self.http_client is None:
            timeout = self.config.get(f'{self.api_name}.timeout') or self.config.get('api.timeout', 30)
            max_retries = self.config.get(f'{self.api_name}.max_retries') or self.config.get('api.max_retries', 3)
            self.http_client = HTTPClient(
                timeout=timeout,
                max_retries=max_retries,
                middleware_registry=self.middleware_registry
            )
        
        self.logger.info(f"{self.api_name} initialized")
    
    @abstractmethod
    def _build_request_data(self, **kwargs) -> Dict[str, Any]:
        """
        构建请求数据
        
        子类必须实现此方法，定义如何构建请求数据
        
        Returns:
            请求数据字典
        """
        pass
    
    @abstractmethod
    def _parse_response(self, response_data: Dict[str, Any]) -> Any:
        """
        解析响应数据
        
        子类必须实现此方法，定义如何解析响应数据
        
        Args:
            response_data: 原始响应数据
            
        Returns:
            解析后的响应对象
        """
        pass
    
    def _authenticate_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        对请求进行认证
        
        子类可以重写此方法实现特定的认证逻辑
        默认实现不做任何处理
        
        Args:
            request_data: 请求数据
            
        Returns:
            添加认证信息后的请求数据
        """
        return request_data
    
    def _validate_response(self, response_data: Dict[str, Any]) -> None:
        """
        验证响应数据
        
        子类可以重写此方法实现特定的验证逻辑
        默认实现不做任何处理
        
        Args:
            response_data: 响应数据
            
        Raises:
            Exception: 验证失败
        """
        pass
    
    def call_api(self, 
                 endpoint: str,
                 method: str = 'POST',
                 headers: Optional[Dict[str, str]] = None,
                 authenticate: bool = True,
                 validate: bool = True,
                 **kwargs) -> Any:
        """
        调用API接口
        
        Args:
            endpoint: API端点路径
            method: HTTP方法（GET, POST, PUT, DELETE等）
            headers: 请求头
            authenticate: 是否进行认证
            validate: 是否验证响应
            **kwargs: 传递给_build_request_data的参数
            
        Returns:
            解析后的响应对象
            
        Raises:
            requests.exceptions.RequestException: HTTP请求失败
            Exception: 认证或验证失败
        """
        self.logger.info(f"Calling API: {method} {endpoint}")
        
        # 构建请求数据
        request_data = self._build_request_data(**kwargs)
        
        # 认证请求
        if authenticate:
            request_data = self._authenticate_request(request_data)
        
        # 构建完整URL
        url = f"{self.base_url}{endpoint}"
        
        # 设置默认请求头
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        
        # 发送HTTP请求
        if method.upper() == 'GET':
            response_data = self.http_client.get(url=url, headers=headers, params=request_data)
        elif method.upper() == 'POST':
            response_data = self.http_client.post(url=url, headers=headers, body=request_data)
        elif method.upper() == 'PUT':
            response_data = self.http_client.put(url=url, headers=headers, body=request_data)
        elif method.upper() == 'DELETE':
            response_data = self.http_client.delete(url=url, headers=headers, params=request_data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        # 验证响应
        if validate:
            self._validate_response(response_data['body'])
        
        # 解析响应
        result = self._parse_response(response_data['body'])
        
        self.logger.info(f"API call completed: {endpoint}")
        
        return result
    
    def close(self) -> None:
        """关闭API客户端,释放资源"""
        if self.http_client:
            self.http_client.close()
        self.logger.info(f"{self.api_name} closed")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
    
    def __repr__(self) -> str:
        """返回API客户端的字符串表示"""
        return f"{self.__class__.__name__}(base_url={self.base_url})"
