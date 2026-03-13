"""
创单接口封装模块

提供统一创单接口(CreatePay)的封装,支持:
- 创建支付订单
- 请求签名
- 响应验签
- 中间件集成
"""

from typing import Dict, Any, Optional
from attrs import define, field

from utils.http_client import HTTPClient
from utils.rsa_signer import RSASigner
from utils.config_manager import ConfigManager
from utils.middleware_registry import MiddlewareRegistry
from utils.logger import Logger
from api.models import APIRequest, APIResponse


@define
class GenericAPI:
    """
    创单接口封装类
    
    封装统一创单接口的调用逻辑,包括:
    - 请求数据构建
    - 请求签名
    - HTTP请求发送
    - 响应验签
    - 响应数据解析
    """
    
    # 必需组件
    config: ConfigManager = field()
    logger: Logger = field(default=None)
    
    # 可选组件
    http_client: Optional[HTTPClient] = field(default=None)
    rsa_signer: Optional[RSASigner] = field(default=None)
    middleware_registry: Optional[MiddlewareRegistry] = field(default=None)
    
    def __attrs_post_init__(self):
        """初始化后处理"""
        # 如果没有提供logger,创建默认logger
        if self.logger is None:
            self.logger = Logger(name="GenericAPI")
        
        # 如果没有提供http_client,创建默认http_client
        if self.http_client is None:
            timeout = self.config.get('api.timeout', 30)
            max_retries = self.config.get('api.max_retries', 3)
            self.http_client = HTTPClient(
                timeout=timeout,
                max_retries=max_retries,
                middleware_registry=self.middleware_registry
            )
        
        # 如果没有提供rsa_signer,创建默认rsa_signer
        if self.rsa_signer is None:
            private_key_path = self.config.get('security.private_key_path')
            public_key_path = self.config.get('security.public_key_path')
            if private_key_path and public_key_path:
                self.rsa_signer = RSASigner(
                    private_key_path=private_key_path,
                    public_key_path=public_key_path
                )
        
        self.logger.info("GenericAPI initialized")
    
    def call_api(self, request: APIRequest, sign_request: bool = True, 
                    verify_response: bool = True) -> APIResponse:
        """
        创建支付订单
        
        Args:
            request: 创单请求对象
            sign_request: 是否对请求签名,默认True
            verify_response: 是否验证响应签名,默认True
            
        Returns:
            创单响应对象
            
        Raises:
            ValueError: 参数验证失败
            requests.exceptions.RequestException: HTTP请求失败
            Exception: 签名验证失败
        """
        self.logger.info(f"Creating order: txn_seqno={request.txn_seqno}")
        
        # 构建请求数据
        request_data = self._build_request_data(request)
        
        # 对请求签名
        if sign_request and self.rsa_signer:
            request_data = self._sign_request(request_data)
        
        # 获取API URL
        api_url = self.config.get('api.base_url') + self.config.get('api.createpay_path', '/api/createpay')
        
        # 发送HTTP请求
        response_data = self.http_client.post(
            url=api_url,
            headers={'Content-Type': 'application/json'},
            body=request_data
        )
        
        # 验证响应签名
        if verify_response and self.rsa_signer:
            self._verify_response(response_data['body'])
        
        # 构建响应对象
        response = APIResponse.from_dict(response_data['body'])
        
        self.logger.info(f"Order created: return_code={response.return_code}, order_id={response.order_id}")
        
        return response
    
    def _build_request_data(self, request: APIRequest) -> Dict[str, Any]:
        """
        构建请求数据
        
        Args:
            request: 创单请求对象
            
        Returns:
            请求数据字典
        """
        # 转换为字典
        request_data = request.to_dict()
        
        # 移除sign字段(稍后会重新计算)
        if 'sign' in request_data:
            del request_data['sign']
        
        self.logger.debug(f"Request data built: {len(request_data)} fields")
        
        return request_data
    
    def _sign_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        对请求签名
        
        Args:
            request_data: 请求数据字典
            
        Returns:
            包含签名的请求数据字典
        """
        if not self.rsa_signer:
            self.logger.warning("RSA signer not configured, skip signing")
            return request_data
        
        # 构建待签名字符串(按字段名排序)
        sorted_keys = sorted(request_data.keys())
        sign_str = '&'.join([f"{key}={request_data[key]}" for key in sorted_keys if request_data[key] is not None])
        
        # 签名
        signature = self.rsa_signer.sign(sign_str)
        request_data['sign'] = signature
        
        self.logger.debug("Request signed")
        
        return request_data
    
    def _verify_response(self, response_data: Dict[str, Any]) -> None:
        """
        验证响应签名
        
        Args:
            response_data: 响应数据字典
            
        Raises:
            Exception: 签名验证失败
        """
        if not self.rsa_signer:
            self.logger.warning("RSA signer not configured, skip verification")
            return
        
        # 提取签名
        signature = response_data.get('sign')
        if not signature:
            self.logger.warning("Response has no signature, skip verification")
            return
        
        # 构建待验签字符串(按字段名排序,排除sign字段)
        sorted_keys = sorted([k for k in response_data.keys() if k != 'sign'])
        verify_str = '&'.join([f"{key}={response_data[key]}" for key in sorted_keys if response_data[key] is not None])
        
        # 验签
        is_valid = self.rsa_signer.verify(verify_str, signature)
        
        if not is_valid:
            self.logger.error("Response signature verification failed")
            raise Exception("Response signature verification failed")
        
        self.logger.debug("Response signature verified")
    
    def close(self) -> None:
        """关闭API客户端,释放资源"""
        if self.http_client:
            self.http_client.close()
        self.logger.info("GenericAPI closed")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
    
    def __repr__(self) -> str:
        """返回API客户端的字符串表示"""
        return f"GenericAPI(base_url={self.config.get('api.base_url')})"
