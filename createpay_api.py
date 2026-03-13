"""
CreatePay API实现

这是一个具体的API实现示例，展示如何使用BaseAPI创建特定的API封装。
"""

from typing import Dict, Any
from attrs import define, field

from api.base_api import BaseAPI
from api.models import APIRequest, APIResponse
from utils.rsa_signer import RSASigner


@define
class CreatePayAPI(BaseAPI):
    """
    CreatePay API封装类
    
    继承BaseAPI，实现创单接口的特定逻辑：
    - RSA签名认证
    - 创单请求构建
    - 创单响应解析
    """
    
    # CreatePay特有组件
    rsa_signer: RSASigner = field(default=None)
    
    def __attrs_post_init__(self):
        """初始化后处理"""
        # 设置API名称
        self.api_name = "createpay"
        
        # 调用父类初始化
        super().__attrs_post_init__()
        
        # 初始化RSA签名器
        if self.rsa_signer is None:
            private_key_path = self.config.get('security.private_key_path')
            public_key_path = self.config.get('security.public_key_path')
            if private_key_path and public_key_path:
                self.rsa_signer = RSASigner(
                    private_key_path=private_key_path,
                    public_key_path=public_key_path
                )
    
    def _build_request_data(self, request: APIRequest = None, **kwargs) -> Dict[str, Any]:
        """
        构建创单请求数据
        
        Args:
            request: 创单请求对象
            **kwargs: 额外参数
            
        Returns:
            请求数据字典
        """
        if request is None:
            # 如果没有提供request对象，从kwargs构建
            request = APIRequest(**kwargs)
        
        # 转换为字典
        request_data = request.to_dict()
        
        # 移除sign字段(稍后会重新计算)
        if 'sign' in request_data:
            del request_data['sign']
        
        self.logger.debug(f"Request data built: {len(request_data)} fields")
        
        return request_data
    
    def _authenticate_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        对请求进行RSA签名
        
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
    
    def _validate_response(self, response_data: Dict[str, Any]) -> None:
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
    
    def _parse_response(self, response_data: Dict[str, Any]) -> APIResponse:
        """
        解析创单响应数据
        
        Args:
            response_data: 响应数据字典
            
        Returns:
            创单响应对象
        """
        return APIResponse.from_dict(response_data)
    
    def create_order(self, request: APIRequest, sign_request: bool = True, 
                    verify_response: bool = True) -> APIResponse:
        """
        创建支付订单（便捷方法）
        
        Args:
            request: 创单请求对象
            sign_request: 是否对请求签名,默认True
            verify_response: 是否验证响应签名,默认True
            
        Returns:
            创单响应对象
        """
        endpoint = self.config.get('createpay.endpoint', '/api/createpay')
        
        return self.call_api(
            endpoint=endpoint,
            method='POST',
            request=request,
            authenticate=sign_request,
            validate=verify_response
        )
