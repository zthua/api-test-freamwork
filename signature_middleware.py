"""
签名中间件模块

自动对请求进行RSA签名,并验证响应签名。
"""
from typing import Dict, Any
import json

from middlewares.base_middleware import BaseMiddleware
from utils.rsa_signer import RSASigner
from utils.logger import Logger


class SignatureMiddleware(BaseMiddleware):
    """
    签名中间件
    
    自动对HTTP请求进行RSA签名,并验证响应的签名。
    """
    
    def __init__(self, priority: int = 20, enabled: bool = True, **kwargs):
        """
        初始化签名中间件
        
        Args:
            priority: 中间件优先级,默认20
            enabled: 是否启用,默认True
            **kwargs: 配置参数
                - private_key_path: 私钥文件路径,用于签名
                - public_key_path: 公钥文件路径,用于验签
                - sign_field: 签名字段名,默认'sign'
                - verify_response: 是否验证响应签名,默认True
        """
        super().__init__(priority, enabled, **kwargs)
        self.logger = Logger()
        
        # 获取配置
        self.private_key_path = kwargs.get('private_key_path')
        self.public_key_path = kwargs.get('public_key_path')
        self.sign_field = kwargs.get('sign_field', 'sign')
        self.verify_response = kwargs.get('verify_response', True)
        
        # 延迟初始化RSA签名器(只在启用时初始化)
        self.signer = None
        if enabled:
            self._init_signer()
    
    def _init_signer(self):
        """初始化RSA签名器"""
        if not self.private_key_path or not self.public_key_path:
            raise ValueError("SignatureMiddleware requires 'private_key_path' and 'public_key_path' in config")
        
        self.signer = RSASigner(self.private_key_path, self.public_key_path)
    
    def _build_sign_string(self, data: Dict[str, Any], exclude_fields: list = None) -> str:
        """
        构建待签名字符串
        
        将字典按key排序后拼接成字符串,格式: key1=value1&key2=value2
        
        Args:
            data: 数据字典
            exclude_fields: 需要排除的字段列表
            
        Returns:
            待签名字符串
        """
        if exclude_fields is None:
            exclude_fields = [self.sign_field]
        
        # 过滤掉排除字段和空值
        filtered_data = {
            k: v for k, v in data.items()
            if k not in exclude_fields and v is not None and v != ''
        }
        
        # 按key排序
        sorted_keys = sorted(filtered_data.keys())
        
        # 拼接字符串
        sign_parts = []
        for key in sorted_keys:
            value = filtered_data[key]
            # 如果值是字典或列表,转换为JSON字符串
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
            sign_parts.append(f"{key}={value}")
        
        return "&".join(sign_parts)
    
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理请求:对请求body进行签名
        
        Args:
            request_data: 请求数据字典
            
        Returns:
            添加签名后的请求数据
        """
        if self.signer is None:
            self._init_signer()
        
        if 'body' not in request_data or not isinstance(request_data['body'], dict):
            self.logger.warning("Request body is empty or not a dict, skip signing")
            return request_data
        
        try:
            # 构建待签名字符串
            sign_string = self._build_sign_string(request_data['body'])
            self.logger.debug(f"Sign string: {sign_string}")
            
            # 生成签名
            signature = self.signer.sign(sign_string)
            self.logger.debug(f"Generated signature: {signature[:50]}...")
            
            # 将签名添加到请求body
            request_data['body'][self.sign_field] = signature
            
            self.logger.info("Request signed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to sign request: {str(e)}")
            raise Exception(f"SignatureMiddleware failed to sign request: {str(e)}") from e
        
        return request_data
    
    def process_response(self, response_data: Dict[str, Any], request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理响应:验证响应签名
        
        Args:
            response_data: 响应数据字典
            request_data: 原始请求数据字典
            
        Returns:
            原始响应数据
            
        Raises:
            Exception: 签名验证失败时抛出异常
        """
        if not self.verify_response:
            return response_data
        
        if self.signer is None:
            self._init_signer()
        
        if 'body' not in response_data or not isinstance(response_data['body'], dict):
            self.logger.warning("Response body is empty or not a dict, skip signature verification")
            return response_data
        
        # 检查响应中是否包含签名字段
        if self.sign_field not in response_data['body']:
            self.logger.warning(f"Response does not contain '{self.sign_field}' field, skip verification")
            return response_data
        
        try:
            # 获取响应中的签名
            signature = response_data['body'][self.sign_field]
            
            # 构建待验签字符串
            sign_string = self._build_sign_string(response_data['body'])
            self.logger.debug(f"Verify sign string: {sign_string}")
            
            # 验证签名
            is_valid = self.signer.verify(sign_string, signature)
            
            if is_valid:
                self.logger.info("Response signature verified successfully")
            else:
                raise Exception("Response signature verification failed: signature mismatch")
            
        except Exception as e:
            self.logger.error(f"Failed to verify response signature: {str(e)}")
            raise Exception(f"SignatureMiddleware failed to verify response: {str(e)}") from e
        
        return response_data
