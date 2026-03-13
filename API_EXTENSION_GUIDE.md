# API扩展指南

本文档说明如何在通用API测试框架中添加新的API实现。

## 框架架构

```
api-test-framework/
├── api/
│   ├── base_api.py          # API基类（所有API的父类）
│   ├── api_registry.py      # API注册器（管理所有API）
│   ├── createpay_api.py     # CreatePay API实现（示例）
│   └── models.py            # 数据模型
├── utils/                   # 工具类
├── testcases/              # 测试用例
└── config/                 # 配置文件
```

## 添加新API的步骤

### 1. 创建API实现类

继承`BaseAPI`类并实现必需的抽象方法：

```python
# api/your_api.py
from typing import Dict, Any
from attrs import define
from api.base_api import BaseAPI

@define
class YourAPI(BaseAPI):
    """你的API实现"""
    
    def __attrs_post_init__(self):
        """初始化"""
        self.api_name = "your_api"  # 设置API名称
        super().__attrs_post_init__()
    
    def _build_request_data(self, **kwargs) -> Dict[str, Any]:
        """构建请求数据"""
        # 实现你的请求数据构建逻辑
        return {
            "param1": kwargs.get("param1"),
            "param2": kwargs.get("param2"),
        }
    
    def _parse_response(self, response_data: Dict[str, Any]) -> Any:
        """解析响应数据"""
        # 实现你的响应解析逻辑
        return response_data
    
    def _authenticate_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """认证请求（可选）"""
        # 如果需要特殊认证，在这里实现
        # 例如：添加API Key、OAuth token等
        request_data['api_key'] = self.config.get('your_api.api_key')
        return request_data
    
    def _validate_response(self, response_data: Dict[str, Any]) -> None:
        """验证响应（可选）"""
        # 如果需要验证响应，在这里实现
        if response_data.get('code') != 200:
            raise Exception(f"API error: {response_data.get('message')}")
```

### 2. 注册API

在`api/api_registry.py`的`register_builtin_apis`函数中注册你的API：

```python
def register_builtin_apis(registry: APIRegistry) -> None:
    """注册内置的API实现"""
    from api.createpay_api import CreatePayAPI
    from api.your_api import YourAPI  # 导入你的API
    
    registry.register('createpay', CreatePayAPI)
    registry.register('your_api', YourAPI)  # 注册你的API
```

### 3. 添加配置

在`config/config.yaml`中添加你的API配置：

```yaml
your_api:
  base_url: "https://api.example.com"
  endpoint: "/api/v1/your_endpoint"
  timeout: 30
  max_retries: 3
  api_key: "your_api_key_here"
```

### 4. 使用API

在测试用例中使用你的API：

```python
def test_your_api(api_registry):
    """测试你的API"""
    # 获取API实例
    api = api_registry.get_api('your_api')
    
    # 调用API
    response = api.call_api(
        endpoint="/api/v1/your_endpoint",
        method="POST",
        param1="value1",
        param2="value2"
    )
    
    # 断言
    assert response is not None
```

## 支持的认证方式

框架支持多种认证方式，你可以在`_authenticate_request`方法中实现：

### 1. API Key认证

```python
def _authenticate_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
    api_key = self.config.get('your_api.api_key')
    request_data['api_key'] = api_key
    return request_data
```

### 2. Bearer Token认证

```python
def _authenticate_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
    # Token通常放在请求头中，需要在call_api时传递
    return request_data

# 在调用时：
api.call_api(
    endpoint="/api/endpoint",
    headers={'Authorization': f'Bearer {token}'},
    ...
)
```

### 3. RSA签名认证（参考CreatePayAPI）

```python
from utils.rsa_signer import RSASigner

@define
class YourAPI(BaseAPI):
    rsa_signer: RSASigner = field(default=None)
    
    def __attrs_post_init__(self):
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
    
    def _authenticate_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        if self.rsa_signer:
            # 构建签名字符串
            sign_str = '&'.join([f"{k}={v}" for k, v in sorted(request_data.items())])
            # 签名
            signature = self.rsa_signer.sign(sign_str)
            request_data['sign'] = signature
        return request_data
```

### 4. OAuth 2.0认证

```python
def _authenticate_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
    # 获取access token
    access_token = self._get_access_token()
    # 添加到请求头（在call_api时传递）
    return request_data

def _get_access_token(self) -> str:
    # 实现OAuth token获取逻辑
    pass
```

## 支持的HTTP方法

框架支持所有标准HTTP方法：

```python
# GET请求
response = api.call_api(endpoint="/api/resource", method="GET", param1="value1")

# POST请求
response = api.call_api(endpoint="/api/resource", method="POST", data={"key": "value"})

# PUT请求
response = api.call_api(endpoint="/api/resource/123", method="PUT", data={"key": "new_value"})

# DELETE请求
response = api.call_api(endpoint="/api/resource/123", method="DELETE")
```

## 中间件支持

框架支持中间件机制，可以在请求/响应处理过程中插入自定义逻辑：

- 日志记录中间件
- 签名中间件
- 重试中间件
- 性能统计中间件

中间件会自动应用到所有API调用，无需额外配置。

## 完整示例

参考`api/createpay_api.py`查看完整的API实现示例。

## 最佳实践

1. **使用attrs定义数据类**：利用attrs的验证功能确保数据正确性
2. **实现便捷方法**：为常用操作提供便捷方法（如`create_order`）
3. **完善日志记录**：在关键步骤添加日志，便于调试
4. **错误处理**：在`_validate_response`中实现完善的错误处理
5. **配置外部化**：将所有配置项放在配置文件中，不要硬编码
6. **编写测试**：为你的API实现编写单元测试和集成测试

## 常见问题

### Q: 如何处理分页API？

A: 在API类中添加分页处理方法：

```python
def get_all_pages(self, endpoint: str, **kwargs):
    """获取所有分页数据"""
    all_data = []
    page = 1
    while True:
        response = self.call_api(endpoint=endpoint, page=page, **kwargs)
        data = response.get('data', [])
        if not data:
            break
        all_data.extend(data)
        page += 1
    return all_data
```

### Q: 如何处理文件上传？

A: 使用multipart/form-data格式：

```python
def upload_file(self, file_path: str):
    """上传文件"""
    with open(file_path, 'rb') as f:
        files = {'file': f}
        # 需要在http_client中添加文件上传支持
        response = self.http_client.post(
            url=f"{self.base_url}/upload",
            files=files
        )
    return response
```

### Q: 如何处理WebSocket API？

A: WebSocket需要单独实现，不适合使用BaseAPI。建议创建独立的WebSocket客户端类。
