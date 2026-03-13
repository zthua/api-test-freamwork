"""
HTTP客户端模块

提供HTTP请求功能,支持超时、重试、连接池管理、响应时间统计和中间件机制。
"""
import time
import requests
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from utils.logger import Logger
from utils.middleware_registry import MiddlewareRegistry


class HTTPClient:
    """
    HTTP客户端
    
    封装HTTP请求功能,支持:
    - POST请求
    - 超时设置
    - 自动重试
    - 连接池管理
    - 响应时间统计
    - 中间件机制(日志、签名、重试、性能统计等)
    """
    
    def __init__(self, timeout: int = 30, max_retries: int = 3, pool_connections: int = 10, 
                 pool_maxsize: int = 10, middleware_registry: Optional[MiddlewareRegistry] = None):
        """
        初始化HTTP客户端
        
        Args:
            timeout: 请求超时时间(秒),默认30秒
            max_retries: 最大重试次数,默认3次
            pool_connections: 连接池大小,默认10
            pool_maxsize: 连接池最大连接数,默认10
            middleware_registry: 中间件注册器,可选
        """
        self.logger = Logger()
        self.timeout = timeout
        self.max_retries = max_retries
        self.middleware_registry = middleware_registry
        
        # 创建session
        self.session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[500, 502, 503, 504],  # 这些状态码会触发重试
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"],  # 允许重试的HTTP方法
            backoff_factor=1  # 重试间隔: {backoff factor} * (2 ** ({number of total retries} - 1))
        )
        
        # 配置HTTP适配器
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize
        )
        
        # 挂载适配器
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 响应时间记录
        self._last_response_time = 0
        
        middleware_info = "with middleware" if middleware_registry else "without middleware"
        self.logger.info(f"HTTPClient initialized: timeout={timeout}s, max_retries={max_retries}, {middleware_info}")
    
    def post(self, url: str, headers: Dict[str, str] = None, body: Dict[str, Any] = None, 
             timeout: int = None, log_request: bool = True, log_response: bool = True) -> Dict[str, Any]:
        """
        发送POST请求
        
        Args:
            url: 请求URL
            headers: 请求头字典
            body: 请求体字典(会自动转换为JSON)
            timeout: 超时时间(秒),不指定则使用默认值
            log_request: 是否记录请求日志,默认True
            log_response: 是否记录响应日志,默认True
            
        Returns:
            响应数据字典,包含:
                - status_code: HTTP状态码
                - headers: 响应头字典
                - body: 响应体(已解析为字典)
                - elapsed_time: 响应时间(秒)
                
        Raises:
            requests.exceptions.RequestException: 请求失败时抛出
        """
        start_time = time.time()
        
        # 构建请求数据
        request_data = {
            'url': url,
            'method': 'POST',
            'headers': headers or {},
            'body': body or {}
        }
        
        # 执行请求前中间件
        if self.middleware_registry:
            request_data = self.middleware_registry.process_request(request_data)
        
        # 记录请求日志(如果没有日志中间件)
        if log_request and not self._has_logging_middleware():
            self._log_request(request_data['url'], request_data.get('headers'), request_data.get('body'))
        
        try:
            # 使用指定的超时时间或默认超时时间
            request_timeout = timeout if timeout is not None else self.timeout
            
            # 发送POST请求
            response = self.session.post(
                url=request_data['url'],
                json=request_data.get('body'),
                headers=request_data.get('headers'),
                timeout=request_timeout
            )
            
            # 计算响应时间
            elapsed_time = time.time() - start_time
            self._last_response_time = elapsed_time
            
            # 解析响应
            try:
                response_body = response.json()
            except ValueError:
                # 如果响应不是JSON格式,返回文本
                response_body = {"text": response.text}
            
            # 构建响应数据
            response_data = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'body': response_body,
                'elapsed_time': elapsed_time
            }
            
            # 执行响应后中间件
            if self.middleware_registry:
                response_data = self.middleware_registry.process_response(response_data, request_data)
            
            # 记录响应日志(如果没有日志中间件)
            if log_response and not self._has_logging_middleware():
                self._log_response(response_data)
            
            self.logger.debug(f"POST request completed: {url} - {response.status_code} - {elapsed_time:.3f}s")
            
            return response_data
            
        except requests.exceptions.Timeout as e:
            elapsed_time = time.time() - start_time
            self._last_response_time = elapsed_time
            self.logger.error(f"Request timeout after {elapsed_time:.3f}s: {url}")
            raise
            
        except requests.exceptions.RequestException as e:
            elapsed_time = time.time() - start_time
            self._last_response_time = elapsed_time
            self.logger.error(f"Request failed after {elapsed_time:.3f}s: {url} - {str(e)}")
            raise
    
    def _has_logging_middleware(self) -> bool:
        """
        检查是否有日志中间件
        
        Returns:
            是否有日志中间件
        """
        if not self.middleware_registry:
            return False
        
        middlewares = self.middleware_registry.get_middlewares()
        return any(middleware.__class__.__name__ == 'LoggingMiddleware' for middleware in middlewares)
    
    def _log_request(self, url: str, headers: Dict[str, str] = None, body: Dict[str, Any] = None) -> None:
        """
        记录请求日志
        
        Args:
            url: 请求URL
            headers: 请求头
            body: 请求体
        """
        import json
        
        log_msg = f"\n{'='*80}\n"
        log_msg += "HTTP REQUEST\n"
        log_msg += f"{'='*80}\n"
        log_msg += f"URL: {url}\n"
        log_msg += f"Method: POST\n"
        
        if headers:
            # 脱敏处理
            masked_headers = self._mask_sensitive_data(headers)
            log_msg += f"Headers: {json.dumps(masked_headers, ensure_ascii=False, indent=2)}\n"
        
        if body:
            # 脱敏处理
            masked_body = self._mask_sensitive_data(body)
            log_msg += f"Body: {json.dumps(masked_body, ensure_ascii=False, indent=2)}\n"
        
        log_msg += f"{'='*80}\n"
        self.logger.info(log_msg)
    
    def _log_response(self, response_data: Dict[str, Any]) -> None:
        """
        记录响应日志
        
        Args:
            response_data: 响应数据
        """
        import json
        
        log_msg = f"\n{'='*80}\n"
        log_msg += "HTTP RESPONSE\n"
        log_msg += f"{'='*80}\n"
        log_msg += f"Status Code: {response_data.get('status_code')}\n"
        log_msg += f"Elapsed Time: {response_data.get('elapsed_time', 0):.3f}s\n"
        
        if response_data.get('headers'):
            log_msg += f"Headers: {json.dumps(dict(response_data['headers']), ensure_ascii=False, indent=2)}\n"
        
        if response_data.get('body'):
            # 脱敏处理
            masked_body = self._mask_sensitive_data(response_data['body'])
            log_msg += f"Body: {json.dumps(masked_body, ensure_ascii=False, indent=2)}\n"
        
        log_msg += f"{'='*80}\n"
        self.logger.info(log_msg)
    
    def _mask_sensitive_data(self, data: Any) -> Any:
        """
        脱敏敏感数据
        
        Args:
            data: 需要脱敏的数据
            
        Returns:
            脱敏后的数据
        """
        sensitive_fields = ['password', 'private_key', 'secret', 'sign', 'token', 'authorization']
        
        if isinstance(data, dict):
            masked_data = {}
            for key, value in data.items():
                if any(field in key.lower() for field in sensitive_fields):
                    # 脱敏处理
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
    
    def get_response_time(self) -> float:
        """
        获取最后一次请求的响应时间
        
        Returns:
            响应时间(秒)
        """
        return self._last_response_time
    
    def close(self) -> None:
        """
        关闭HTTP客户端,释放连接池资源
        """
        if self.session:
            self.session.close()
            self.logger.info("HTTPClient closed")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
    
    def __repr__(self) -> str:
        """返回HTTP客户端的字符串表示"""
        return f"HTTPClient(timeout={self.timeout}s, max_retries={self.max_retries})"
