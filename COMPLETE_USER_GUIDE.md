# API测试自动化框架 - 完整使用手册

## 目录

1. [快速开始](#快速开始)
2. [环境配置](#环境配置)
3. [API对接指南](#api对接指南)
4. [数据构造](#数据构造)
5. [编写测试用例](#编写测试用例)
6. [测试用例自动转换](#测试用例自动转换)
7. [执行测试](#执行测试)
8. [高级功能](#高级功能)
9. [最佳实践](#最佳实践)
10. [常见问题](#常见问题)

---

## 快速开始

### 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 或使用pip3
pip3 install -r requirements.txt
```

### 验证安装

```bash
# 运行示例测试
python3 -m pytest testcases/generated/test_direct_mode_gen.py::test_1_1_1_微信小程序支付_wechat_applet -v
```

### 快速体验

```bash
# 1. 转换测试用例
python3 convert.py -i testdata/test_cases.md

# 2. 运行测试
python3 -m pytest testcases/generated/ -v

# 3. 查看报告
allure serve reports/allure-results
```

---

## 环境配置

### 1. 配置文件结构

```
config/
├── config.yaml          # 主配置文件
├── middleware.yaml      # 中间件配置
├── env/
│   ├── test.yaml       # 测试环境
│   ├── uat.yaml        # UAT环境
│   └── prod.yaml       # 生产环境
└── keys/
    ├── private_key.pem # RSA私钥
    └── public_key.pem  # RSA公钥
```

### 2. 主配置文件 (config/config.yaml)

```yaml
# API基础配置
api:
  base_url: "https://test-api.example.com"
  timeout: 30
  max_retries: 3
  notify_url: "https://test.example.com/notify"

# 环境配置
environment: test  # test, uat, prod

# 安全配置
security:
  private_key_path: "config/keys/private_key.pem"
  public_key_path: "config/keys/public_key.pem"

# 商户配置
merchant:
  mch_id: "M123456789"
  
# 微信配置
wechat:
  appid: "wx_test_appid"
  sub_mchid: "wx_sub_mchid"

# 支付宝配置
alipay:
  sub_mchid: "ali_sub_mchid"
```

### 3. 环境配置文件 (config/env/test.yaml)

```yaml
# 测试环境配置
api:
  base_url: "https://test-api.example.com"
  
merchant:
  mch_id: "TEST_MERCHANT_123"
  
wechat:
  appid: "wx_test_appid_123"
  sub_mchid: "wx_test_sub_123"
```

### 4. 中间件配置 (config/middleware.yaml)

```yaml
# 中间件配置
middlewares:
  - name: logging
    enabled: true
    priority: 10
    config:
      log_request: true
      log_response: true
      
  - name: signature
    enabled: true
    priority: 20
    config:
      sign_field: "sign"
      
  - name: retry
    enabled: true
    priority: 30
    config:
      max_retries: 3
      retry_delay: 1
      
  - name: performance
    enabled: true
    priority: 40
    config:
      threshold_ms: 1000
```

### 5. 生成RSA密钥

```bash
# 使用框架提供的脚本生成测试密钥
python3 scripts/generate_test_keys.py

# 或手动生成
openssl genrsa -out config/keys/private_key.pem 2048
openssl rsa -in config/keys/private_key.pem -pubout -out config/keys/public_key.pem
```

---

## API对接指南

### 1. 框架架构

```
api-test-framework/
├── api/
│   ├── base_api.py          # API基类（所有API的父类）
│   ├── api_registry.py      # API注册器（管理所有API）
│   ├── createpay_api.py     # CreatePay API实现（示例）
│   └── models.py            # 数据模型
```

### 2. 创建新的API实现

#### 步骤1: 创建API类

创建文件 `api/your_api.py`:

```python
from typing import Dict, Any
from attrs import define
from api.base_api import BaseAPI

@define
class YourAPI(BaseAPI):
    """你的API实现"""
    
    def __attrs_post_init__(self):
        """初始化"""
        self.api_name = "your_api"
        super().__attrs_post_init__()
    
    def _build_request_data(self, **kwargs) -> Dict[str, Any]:
        """构建请求数据"""
        return {
            "param1": kwargs.get("param1"),
            "param2": kwargs.get("param2"),
        }
    
    def _parse_response(self, response_data: Dict[str, Any]) -> Any:
        """解析响应数据"""
        return response_data
```

#### 步骤2: 注册API

在 `api/api_registry.py` 的 `register_builtin_apis` 函数中注册:

```python
def register_builtin_apis(registry: APIRegistry) -> None:
    """注册内置的API实现"""
    from api.createpay_api import CreatePayAPI
    from api.your_api import YourAPI
    
    registry.register('createpay', CreatePayAPI)
    registry.register('your_api', YourAPI)  # 注册你的API
```

#### 步骤3: 添加配置

在 `config/config.yaml` 中添加配置:

```yaml
your_api:
  base_url: "https://api.example.com"
  endpoint: "/api/v1/your_endpoint"
  timeout: 30
  api_key: "your_api_key"
```

#### 步骤4: 使用API

在测试用例中使用:

```python
def test_your_api(api_registry):
    """测试你的API"""
    api = api_registry.get_api('your_api')
    
    response = api.call_api(
        endpoint="/api/v1/your_endpoint",
        method="POST",
        param1="value1",
        param2="value2"
    )
    
    assert response is not None
```

### 3. 支持的认证方式

#### API Key认证

```python
def _authenticate_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
    api_key = self.config.get('your_api.api_key')
    request_data['api_key'] = api_key
    return request_data
```

#### Bearer Token认证

```python
def _authenticate_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
    return request_data

# 在调用时传递token
api.call_api(
    endpoint="/api/endpoint",
    headers={'Authorization': f'Bearer {token}'},
    ...
)
```

#### RSA签名认证

```python
from utils.rsa_signer import RSASigner

@define
class YourAPI(BaseAPI):
    rsa_signer: RSASigner = field(default=None)
    
    def __attrs_post_init__(self):
        super().__attrs_post_init__()
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
            sign_str = '&'.join([f"{k}={v}" for k, v in sorted(request_data.items())])
            signature = self.rsa_signer.sign(sign_str)
            request_data['sign'] = signature
        return request_data
```

### 4. 完整示例

参考 `api/createpay_api.py` 查看完整的API实现示例。

---

## 数据构造

### 1. 使用DataGenerator

框架提供了 `DataGenerator` 类用于生成各种测试数据。

#### 基本用法

```python
from utils.data_generator import DataGenerator

data_gen = DataGenerator()

# 生成交易流水号
txn_seqno = data_gen.generate_txn_seqno()

# 生成时间戳
timestamp = data_gen.generate_timestamp()

# 生成订单金额
amount = data_gen.generate_amount(min_amount=0.01, max_amount=1000.0)

# 生成用户ID
user_id = data_gen.generate_user_id()
```

#### 支持的数据类型

| 数据类型 | 方法 | 说明 |
|---------|------|------|
| 交易流水号 | `generate_txn_seqno()` | 32位唯一流水号 |
| 时间戳 | `generate_timestamp()` | YYYYMMDDHHmmss格式 |
| 日期 | `generate_date()` | YYYYMMDD格式 |
| 用户ID | `generate_user_id()` | 唯一用户标识 |
| 订单金额 | `generate_amount()` | 指定范围的金额 |
| 商户ID | `generate_merchant_id()` | 商户标识 |
| OpenID | `generate_openid()` | 微信/支付宝OpenID |
| AppID | `generate_appid()` | 应用ID |
| 手机号 | `generate_phone_number()` | 11位手机号 |
| 邮箱 | `generate_email()` | 邮箱地址 |
| IP地址 | `generate_ip_address()` | IPv4地址 |
| MAC地址 | `generate_mac_address()` | MAC地址 |
| 设备ID | `generate_device_id()` | 设备唯一标识 |

#### 在测试中使用

```python
def test_payment(data_generator, createpay_api):
    """测试支付"""
    # 构造测试数据
    request_data = {
        "txn_seqno": data_generator.generate_txn_seqno(),
        "txn_time": data_generator.generate_timestamp(),
        "total_amount": data_generator.generate_amount(min_amount=0.01, max_amount=100.0),
        "user_id": data_generator.generate_user_id(),
    }
    
    # 调用API
    response = createpay_api.create_order(**request_data)
    
    # 断言
    assert response.is_success()
```

### 2. 使用数据模型

框架使用 `attrs` 库定义数据模型,提供类型检查和验证。

#### 定义数据模型

```python
from attrs import define, field
from typing import Optional

@define
class PaymentRequest:
    """支付请求"""
    txn_seqno: str = field()
    txn_time: str = field()
    total_amount: str = field()
    mch_id: str = field()
    notify_url: str = field()
    payment_method: str = field()
    openid: Optional[str] = field(default=None)
    
    @total_amount.validator
    def _validate_amount(self, attribute, value):
        """验证金额格式"""
        try:
            amount = float(value)
            if amount <= 0:
                raise ValueError("金额必须大于0")
        except ValueError:
            raise ValueError("金额格式错误")
```

#### 使用数据模型

```python
from api.models import CreatePayRequest

# 创建请求对象
request = CreatePayRequest(
    txn_seqno=data_generator.generate_txn_seqno(),
    txn_time=data_generator.generate_timestamp(),
    total_amount="100.00",
    mch_id="M123456789",
    notify_url="https://example.com/notify",
    payment_method="WECHAT_APPLET",
    openid="test_openid"
)

# attrs会自动验证数据
# 如果数据不符合要求,会抛出异常
```

### 3. 从文件加载测试数据

框架支持从多种格式加载测试数据。

#### JSON格式

```json
{
  "test_cases": [
    {
      "case_id": "TC001",
      "payment_method": "WECHAT_APPLET",
      "total_amount": "100.00",
      "expected_result": "SUCCESS"
    }
  ]
}
```

```python
import json

with open('testdata/payment_data.json', 'r') as f:
    test_data = json.load(f)
    
for case in test_data['test_cases']:
    # 使用测试数据
    pass
```

#### YAML格式

```yaml
test_cases:
  - case_id: TC001
    payment_method: WECHAT_APPLET
    total_amount: "100.00"
    expected_result: SUCCESS
```

```python
import yaml

with open('testdata/payment_data.yaml', 'r') as f:
    test_data = yaml.safe_load(f)
```

#### Excel格式

```python
import pandas as pd

df = pd.read_excel('testdata/payment_data.xlsx')
for index, row in df.iterrows():
    case_id = row['case_id']
    payment_method = row['payment_method']
    # 使用测试数据
```

---

## 编写测试用例

### 1. 手工编写测试用例

#### 基本测试用例

```python
import pytest

def test_wechat_payment(createpay_api, data_generator):
    """测试微信小程序支付"""
    # 构造请求数据
    response = createpay_api.create_order(
        txn_seqno=data_generator.generate_txn_seqno(),
        txn_time=data_generator.generate_timestamp(),
        total_amount="100.00",
        payment_method="WECHAT_APPLET",
        openid="test_openid"
    )
    
    # 断言
    assert response.is_success()
    assert response.return_code == "0000"
    assert response.pay_info is not None
```

#### 参数化测试

```python
import pytest

@pytest.mark.parametrize("payment_method,expected_code", [
    ("WECHAT_APPLET", "0000"),
    ("ALIPAY_APP", "0000"),
    ("CLOUDPAY_APP", "0000"),
])
def test_multiple_payment_methods(createpay_api, data_generator, payment_method, expected_code):
    """测试多种支付方式"""
    response = createpay_api.create_order(
        txn_seqno=data_generator.generate_txn_seqno(),
        txn_time=data_generator.generate_timestamp(),
        total_amount="100.00",
        payment_method=payment_method
    )
    
    assert response.return_code == expected_code
```

#### 使用pytest标记

```python
@pytest.mark.smoke
@pytest.mark.direct_mode
@pytest.mark.wechat
def test_wechat_payment_smoke(createpay_api, data_generator):
    """冒烟测试: 微信支付"""
    response = createpay_api.create_order(
        txn_seqno=data_generator.generate_txn_seqno(),
        txn_time=data_generator.generate_timestamp(),
        total_amount="100.00",
        payment_method="WECHAT_APPLET"
    )
    
    assert response.is_success()
```

#### 异常场景测试

```python
def test_invalid_amount(createpay_api, data_generator):
    """测试无效金额"""
    with pytest.raises(ValueError):
        createpay_api.create_order(
            txn_seqno=data_generator.generate_txn_seqno(),
            txn_time=data_generator.generate_timestamp(),
            total_amount="-100.00",  # 负数金额
            payment_method="WECHAT_APPLET"
        )
```

### 2. 使用场景编排器

框架提供 `APIScenarios` 类用于编排复杂的业务场景。

#### 基本用法

```python
def test_payment_scenario(api_scenarios):
    """测试完整支付场景"""
    # 创建订单
    order = api_scenarios.create_order_scenario(
        payment_method="WECHAT_APPLET",
        total_amount="100.00"
    )
    
    # 查询订单
    query_result = api_scenarios.query_order_scenario(
        txn_seqno=order.txn_seqno
    )
    
    # 断言
    assert query_result.order_status == "SUCCESS"
```

#### 复杂场景

```python
def test_refund_scenario(api_scenarios):
    """测试退款场景"""
    # 1. 创建订单并支付
    order = api_scenarios.create_and_pay_scenario(
        payment_method="WECHAT_APPLET",
        total_amount="100.00"
    )
    
    # 2. 申请退款
    refund = api_scenarios.refund_scenario(
        orig_txn_seqno=order.txn_seqno,
        refund_amount="50.00"
    )
    
    # 3. 查询退款状态
    refund_query = api_scenarios.query_refund_scenario(
        refund_seqno=refund.refund_seqno
    )
    
    # 断言
    assert refund_query.refund_status == "SUCCESS"
```

### 3. 测试用例组织

#### 目录结构

```
testcases/
├── generated/              # 自动生成的测试
│   ├── test_direct_mode_gen.py
│   ├── test_account_mode_gen.py
│   └── test_guarantee_mode_gen.py
├── manual/                 # 手工编写的测试
│   ├── test_smoke.py
│   ├── test_regression.py
│   └── test_integration.py
└── conftest.py            # pytest配置
```

#### 测试分类

使用pytest标记对测试进行分类:

```python
# pytest.ini
[pytest]
markers =
    smoke: 冒烟测试
    regression: 回归测试
    integration: 集成测试
    direct_mode: 直清模式
    account_mode: 账户模式
    wechat: 微信支付
    alipay: 支付宝
    P0: 最高优先级
    P1: 高优先级
    P2: 中优先级
    P3: 低优先级
```

---

## 测试用例自动转换

### 1. 转换流程

```
Markdown测试用例文档
    ↓
[TestCaseParser解析]
    ↓
结构化测试用例数据(JSON)
    ↓
[CodeGenerator生成代码]
    ↓
可执行测试代码(pytest)
```

### 2. Markdown格式规范

#### 测试用例模板

```markdown
## 1.1 直清模式

### 1.1.1 微信小程序支付

**用例ID**: TC_DIRECT_001
**优先级**: P0
**支付方式**: WECHAT_APPLET

**测试步骤**:
1. 构造支付请求
   - total_amount: 100.00
   - payment_method: WECHAT_APPLET
   - openid: test_openid

**预期结果**:
- return_code == "0000"
- return_msg == "成功"
- pay_info is not None
```

### 3. 使用转换工具

#### 基本转换

```bash
# 转换测试用例文档
python3 convert.py -i testdata/test_cases.md

# 指定输出目录
python3 convert.py -i testdata/test_cases.md -o testcases/custom/
```

#### 按模式分组

```bash
# 按支付模式分组 (默认)
python3 convert.py -i testdata/test_cases.md -g payment_mode

# 按支付方式分组
python3 convert.py -i testdata/test_cases.md -g payment_method

# 按优先级分组
python3 convert.py -i testdata/test_cases.md -g priority
```

#### 过滤用例

```bash
# 只转换直清模式
python3 convert.py -i testdata/test_cases.md -f direct

# 只转换微信支付
python3 convert.py -i testdata/test_cases.md -g payment_method -f WECHAT_APPLET,WECHAT_NATIVE

# 只转换P0和P1优先级
python3 convert.py -i testdata/test_cases.md -g priority -f P0,P1
```

#### 详细输出

```bash
# 启用详细输出
python3 convert.py -i testdata/test_cases.md -v

# 设置日志级别
python3 convert.py -i testdata/test_cases.md --log-level DEBUG
```

### 4. 转换结果

转换工具会生成以下文件:

```
testcases/generated/
├── test_direct_mode_gen.py      # 直清模式测试
├── test_account_mode_gen.py     # 账户模式测试
├── test_guarantee_mode_gen.py   # 担保支付测试
└── test_split_mode_gen.py       # 分账支付测试

testdata/parsed/
├── test_cases.json              # JSON格式解析数据
└── test_cases.yaml              # YAML格式解析数据
```

### 5. 验证生成的代码

```bash
# 检查语法
python3 -m py_compile testcases/generated/test_*.py

# 运行测试
python3 -m pytest testcases/generated/test_direct_mode_gen.py -v
```

---

## 执行测试

### 1. 基本执行

```bash
# 运行所有测试
python3 -m pytest testcases/ -v

# 运行指定文件
python3 -m pytest testcases/generated/test_direct_mode_gen.py -v

# 运行指定测试用例
python3 -m pytest testcases/generated/test_direct_mode_gen.py::test_1_1_1_微信小程序支付 -v
```

### 2. 使用标记过滤

```bash
# 运行冒烟测试
python3 -m pytest -m smoke -v

# 运行直清模式测试
python3 -m pytest -m direct_mode -v

# 运行微信支付测试
python3 -m pytest -m wechat -v

# 运行P0优先级测试
python3 -m pytest -m P0 -v

# 组合标记
python3 -m pytest -m "direct_mode and wechat" -v
```

### 3. 输出控制

```bash
# 简洁输出
python3 -m pytest testcases/ -v --tb=short

# 详细输出
python3 -m pytest testcases/ -vv

# 显示print输出
python3 -m pytest testcases/ -v -s

# 只显示失败的测试
python3 -m pytest testcases/ -v --tb=short -x
```

### 4. 并发执行

```bash
# 安装pytest-xdist
pip3 install pytest-xdist

# 并发执行 (4个进程)
python3 -m pytest testcases/ -v -n 4

# 自动检测CPU核心数
python3 -m pytest testcases/ -v -n auto
```

### 5. 生成测试报告

#### HTML报告

```bash
# 安装pytest-html
pip3 install pytest-html

# 生成HTML报告
python3 -m pytest testcases/ -v --html=reports/report.html --self-contained-html
```

#### Allure报告

```bash
# 安装allure-pytest
pip3 install allure-pytest

# 生成Allure数据
python3 -m pytest testcases/ -v --alluredir=reports/allure-results

# 查看报告
allure serve reports/allure-results
```

#### JUnit XML报告

```bash
# 生成JUnit XML报告
python3 -m pytest testcases/ -v --junitxml=reports/junit.xml
```

### 6. 重试失败的测试

```bash
# 安装pytest-rerunfailures
pip3 install pytest-rerunfailures

# 失败重试3次
python3 -m pytest testcases/ -v --reruns 3

# 重试间隔2秒
python3 -m pytest testcases/ -v --reruns 3 --reruns-delay 2
```

### 7. 测试覆盖率

```bash
# 安装pytest-cov
pip3 install pytest-cov

# 生成覆盖率报告
python3 -m pytest testcases/ -v --cov=api --cov=utils --cov-report=html

# 查看报告
open htmlcov/index.html
```

### 8. 环境切换

```bash
# 使用测试环境
python3 -m pytest testcases/ -v --env=test

# 使用UAT环境
python3 -m pytest testcases/ -v --env=uat

# 使用生产环境
python3 -m pytest testcases/ -v --env=prod
```

---

## 高级功能

### 1. 中间件机制

框架提供可插拔的中间件机制,用于处理请求和响应。

#### 内置中间件

| 中间件 | 功能 | 配置 |
|--------|------|------|
| LoggingMiddleware | 日志记录 | log_request, log_response |
| SignatureMiddleware | 签名验签 | sign_field |
| RetryMiddleware | 失败重试 | max_retries, retry_delay |
| PerformanceMiddleware | 性能统计 | threshold_ms |

#### 自定义中间件

```python
from middlewares.base_middleware import BaseMiddleware
from typing import Dict, Any

class CustomMiddleware(BaseMiddleware):
    """自定义中间件"""
    
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求"""
        # 在请求发送前执行
        self.logger.info("Custom middleware: processing request")
        request_data['custom_field'] = 'custom_value'
        return request_data
    
    def process_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理响应"""
        # 在响应返回后执行
        self.logger.info("Custom middleware: processing response")
        return response_data
```

#### 注册中间件

在 `config/middleware.yaml` 中注册:

```yaml
middlewares:
  - name: custom
    enabled: true
    priority: 50
    class: middlewares.custom_middleware.CustomMiddleware
    config:
      custom_param: value
```

### 2. 存储管理

框架使用SQLite统一管理配置、缓存、Schema和测试结果。

#### 使用存储管理器

```python
from utils.storage_manager import StorageManager

storage = StorageManager()

# 保存配置
storage.save_config('api.base_url', 'https://api.example.com')

# 读取配置
base_url = storage.get_config('api.base_url')

# 保存缓存
storage.save_cache('token', 'abc123', ttl=3600)

# 读取缓存
token = storage.get_cache('token')

# 保存测试结果
storage.save_test_result({
    'test_id': 'TC001',
    'status': 'PASS',
    'duration': 1.23
})

# 查询测试结果
results = storage.query_test_results(status='PASS')
```

### 3. 并发执行器

框架提供并发执行器用于性能测试。

#### 基本用法

```python
from utils.concurrent_executor import ConcurrentExecutor

executor = ConcurrentExecutor(max_workers=10)

def payment_task(task_id):
    """支付任务"""
    response = createpay_api.create_order(
        txn_seqno=f"TXN{task_id}",
        total_amount="100.00",
        payment_method="WECHAT_APPLET"
    )
    return response

# 并发执行100个任务
results = executor.execute_concurrent(
    task_func=payment_task,
    task_count=100
)

# 查看结果
print(f"成功: {results['success_count']}")
print(f"失败: {results['failure_count']}")
print(f"平均响应时间: {results['avg_response_time']}ms")
```

### 4. 断言引擎

框架提供强大的断言引擎。

#### 基本断言

```python
from utils.assertion_engine import AssertionEngine

assertion = AssertionEngine()

# 相等断言
assertion.assert_equal(response.return_code, "0000", "返回码应为0000")

# 包含断言
assertion.assert_contains(response.return_msg, "成功", "返回消息应包含'成功'")

# 不为空断言
assertion.assert_not_none(response.pay_info, "支付信息不应为空")

# 正则断言
assertion.assert_regex(response.txn_seqno, r"^\d{32}$", "流水号应为32位数字")
```

#### JSON Schema断言

```python
schema = {
    "type": "object",
    "properties": {
        "return_code": {"type": "string"},
        "return_msg": {"type": "string"},
        "pay_info": {"type": "object"}
    },
    "required": ["return_code", "return_msg"]
}

assertion.assert_json_schema(response_data, schema, "响应应符合Schema")
```

### 5. 数据驱动测试

框架支持从多种数据源驱动测试。

#### 从CSV驱动

```python
from utils.data_driver import DataDriver

driver = DataDriver()

# 加载CSV数据
test_data = driver.load_from_csv('testdata/payment_data.csv')

# 执行测试
for data in test_data:
    response = createpay_api.create_order(**data)
    assert response.is_success()
```

#### 从Excel驱动

```python
# 加载Excel数据
test_data = driver.load_from_excel('testdata/payment_data.xlsx', sheet_name='TestCases')

# 执行测试
for data in test_data:
    response = createpay_api.create_order(**data)
    assert response.is_success()
```

#### 从数据库驱动

```python
# 从数据库加载
test_data = driver.load_from_database(
    query="SELECT * FROM test_cases WHERE status='ACTIVE'"
)

# 执行测试
for data in test_data:
    response = createpay_api.create_order(**data)
    assert response.is_success()
```

---

## 最佳实践

### 1. 测试用例设计

#### 遵循AAA模式

```python
def test_payment():
    """测试支付"""
    # Arrange (准备)
    request_data = {
        "txn_seqno": data_generator.generate_txn_seqno(),
        "total_amount": "100.00",
        "payment_method": "WECHAT_APPLET"
    }
    
    # Act (执行)
    response = createpay_api.create_order(**request_data)
    
    # Assert (断言)
    assert response.is_success()
    assert response.return_code == "0000"
```

#### 使用有意义的测试名称

```python
# 好的命名
def test_wechat_applet_payment_with_valid_amount():
    pass

# 不好的命名
def test_1():
    pass
```

#### 一个测试只测一个功能点

```python
# 好的做法
def test_payment_success():
    """测试支付成功"""
    pass

def test_payment_with_invalid_amount():
    """测试无效金额"""
    pass

# 不好的做法
def test_payment():
    """测试支付的所有情况"""
    # 测试成功
    # 测试失败
    # 测试异常
    pass
```

### 2. 数据管理

#### 使用数据生成器

```python
# 好的做法 - 使用数据生成器
txn_seqno = data_generator.generate_txn_seqno()

# 不好的做法 - 硬编码
txn_seqno = "12345678901234567890123456789012"
```

#### 敏感数据外部化

```python
# 好的做法 - 从配置读取
mch_id = config.get('merchant.mch_id')

# 不好的做法 - 硬编码
mch_id = "M123456789"
```

### 3. 错误处理

#### 使用pytest.raises

```python
def test_invalid_payment_method():
    """测试无效支付方式"""
    with pytest.raises(ValueError) as exc_info:
        createpay_api.create_order(
            txn_seqno=data_generator.generate_txn_seqno(),
            payment_method="INVALID_METHOD"
        )
    
    assert "不支持的支付方式" in str(exc_info.value)
```

#### 提供清晰的错误消息

```python
# 好的做法
assert response.return_code == "0000", f"支付失败: {response.return_msg}"

# 不好的做法
assert response.return_code == "0000"
```

### 4. 测试隔离

#### 使用fixture确保测试独立

```python
@pytest.fixture
def clean_test_data():
    """清理测试数据"""
    yield
    # 测试后清理
    storage.delete_test_data()
```

#### 避免测试间依赖

```python
# 好的做法 - 每个测试独立
def test_create_order():
    order = create_order()
    assert order is not None

def test_query_order():
    order = create_order()  # 自己创建订单
    result = query_order(order.txn_seqno)
    assert result is not None

# 不好的做法 - 测试间依赖
order = None

def test_create_order():
    global order
    order = create_order()

def test_query_order():
    result = query_order(order.txn_seqno)  # 依赖前一个测试
```

### 5. 性能优化

#### 使用session级别的fixture

```python
@pytest.fixture(scope="session")
def api_client():
    """API客户端 (session级别)"""
    client = APIClient()
    yield client
    client.close()
```

#### 并发执行测试

```bash
# 使用pytest-xdist并发执行
python3 -m pytest testcases/ -n auto
```

### 6. 日志记录

#### 记录关键信息

```python
def test_payment(logger):
    """测试支付"""
    logger.info("开始测试支付")
    
    response = createpay_api.create_order(...)
    
    logger.info(f"支付响应: {response.return_code}")
    
    assert response.is_success()
```

#### 使用不同日志级别

```python
logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
```

---

## 常见问题

### 1. 安装问题

#### Q: pip install失败

A: 尝试使用国内镜像源:

```bash
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### Q: Python版本不兼容

A: 框架要求Python 3.8+,检查版本:

```bash
python3 --version
```

### 2. 配置问题

#### Q: 找不到配置文件

A: 确保配置文件在正确位置:

```bash
ls -la config/config.yaml
```

#### Q: RSA签名失败

A: 检查密钥文件:

```bash
# 检查密钥文件是否存在
ls -la config/keys/

# 重新生成密钥
python3 scripts/generate_test_keys.py
```

### 3. 测试执行问题

#### Q: 测试用例无法发现

A: 确保测试文件命名符合规范:

```bash
# 正确命名
test_*.py
*_test.py

# 错误命名
my_tests.py
```

#### Q: fixture未找到

A: 确保conftest.py在正确位置:

```bash
testcases/conftest.py
```

### 4. API调用问题

#### Q: 连接超时

A: 检查网络和API地址:

```yaml
# config/config.yaml
api:
  base_url: "https://correct-api-url.com"
  timeout: 60  # 增加超时时间
```

#### Q: 签名验证失败

A: 检查签名逻辑和密钥:

```python
# 打印签名字符串
logger.debug(f"签名字符串: {sign_str}")
logger.debug(f"签名结果: {signature}")
```

### 5. 转换工具问题

#### Q: Markdown解析失败

A: 检查Markdown格式:

```bash
# 使用详细模式查看错误
python3 convert.py -i test_cases.md -v --log-level DEBUG
```

#### Q: 生成的代码有语法错误

A: 检查模板文件:

```bash
ls -la templates/
```

### 6. 性能问题

#### Q: 测试执行太慢

A: 使用并发执行:

```bash
# 安装pytest-xdist
pip3 install pytest-xdist

# 并发执行
python3 -m pytest testcases/ -n auto
```

#### Q: 内存占用过高

A: 减少并发数或使用session级别的fixture:

```python
@pytest.fixture(scope="session")
def expensive_resource():
    pass
```

### 7. 报告问题

#### Q: Allure报告无法生成

A: 确保allure已安装:

```bash
# 安装allure命令行工具
brew install allure  # macOS
# 或从官网下载: https://docs.qameta.io/allure/

# 生成报告
allure serve reports/allure-results
```

#### Q: HTML报告样式错乱

A: 使用--self-contained-html选项:

```bash
python3 -m pytest testcases/ --html=report.html --self-contained-html
```

### 8. 调试技巧

#### 使用pdb调试

```python
def test_payment():
    import pdb; pdb.set_trace()
    response = createpay_api.create_order(...)
```

#### 查看详细日志

```bash
# 启用详细日志
python3 -m pytest testcases/ -v -s --log-cli-level=DEBUG
```

#### 只运行失败的测试

```bash
# 第一次运行
python3 -m pytest testcases/ -v

# 只运行失败的测试
python3 -m pytest testcases/ -v --lf
```

---

## 附录

### A. 命令速查表

```bash
# 安装依赖
pip3 install -r requirements.txt

# 转换测试用例
python3 convert.py -i testdata/test_cases.md

# 运行所有测试
python3 -m pytest testcases/ -v

# 运行指定标记
python3 -m pytest -m smoke -v

# 并发执行
python3 -m pytest testcases/ -n auto

# 生成HTML报告
python3 -m pytest testcases/ --html=report.html --self-contained-html

# 生成Allure报告
python3 -m pytest testcases/ --alluredir=reports/allure-results
allure serve reports/allure-results

# 查看覆盖率
python3 -m pytest testcases/ --cov=api --cov=utils --cov-report=html
```

### B. 配置模板

完整的配置模板请参考:
- `config/config.yaml.template`
- `config/middleware.yaml.template`
- `config/env/test.yaml.template`

### C. 参考资源

- [pytest文档](https://docs.pytest.org/)
- [attrs文档](https://www.attrs.org/)
- [Allure文档](https://docs.qameta.io/allure/)
- [API扩展指南](API_EXTENSION_GUIDE.md)
- [框架README](README.md)

---

**版本**: v1.0.0  
**最后更新**: 2026-03-12  
**维护者**: Test Team
