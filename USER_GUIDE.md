# API测试自动化框架 - 使用指南

## 目录
1. [快速开始](#快速开始)
2. [环境配置](#环境配置)
3. [RSA密钥配置](#rsa密钥配置)
4. [API接口定义](#api接口定义)
5. [编写测试用例](#编写测试用例)
6. [执行测试](#执行测试)
7. [测试用例自动转换](#测试用例自动转换)
8. [高级功能](#高级功能)

---

## 快速开始

### 1. 安装依赖

```bash
cd api-test-framework
pip install -r requirements.txt
```

### 2. 配置环境

编辑 `config/config.yaml` 文件,配置基本信息:

```yaml
api:
  base_url: "https://test-api.example.com"
  timeout: 30
  
merchant:
  mch_id: "你的商户号"
  
security:
  private_key_path: "config/keys/test_private_key.pem"
  public_key_path: "config/keys/test_public_key.pem"
```

### 3. 运行测试

```bash
# 运行所有测试
python3 -m pytest testcases/ -v

# 运行特定测试文件
python3 -m pytest testcases/generated/test_direct_mode_gen.py -v
```

---

## 环境配置

### 配置文件结构

```
config/
├── config.yaml          # 主配置文件
├── middleware.yaml      # 中间件配置
└── env/                 # 环境配置
    ├── test.yaml        # 测试环境
    ├── uat.yaml         # UAT环境
    └── prod.yaml        # 生产环境
```

### 主配置文件 (config/config.yaml)

```yaml
# 环境标识
environment: test

# API配置
api:
  base_url: "https://test-api.example.com"
  timeout: 30
  max_retries: 3
  notify_url: "https://your-domain.com/notify"

# 商户配置
merchant:
  mch_id: "192302209280000045154"
  sub_mch_id: "302209280000045154"
  service_provider_id: "602303290000064"

# 安全配置
security:
  private_key_path: "config/keys/test_private_key.pem"
  public_key_path: "config/keys/test_public_key.pem"
  sign_type: "RSA"

# 日志配置
logging:
  level: "INFO"
  console_output: true
  file_output: true

# 并发测试配置
concurrent:
  thread_count: 10
  enable_parallel: false

# 性能测试配置
performance:
  response_time_threshold:
    p50: 1000  # 毫秒
    p95: 2000
    p99: 3000
  tps_threshold: 100
```

### 环境切换

通过环境变量切换环境:

```bash
# 使用测试环境
export ENV=test
python3 -m pytest testcases/

# 使用UAT环境
export ENV=uat
python3 -m pytest testcases/

# 使用生产环境
export ENV=prod
python3 -m pytest testcases/
```

### 环境变量覆盖

使用环境变量覆盖配置:

```bash
# 覆盖API地址
export CREATEPAY_API_BASE_URL="https://custom-api.example.com"

# 覆盖商户号
export CREATEPAY_MERCHANT_MCH_ID="your_merchant_id"
```

---

## RSA密钥配置

### 1. 生成测试密钥对

框架提供了密钥生成脚本:

```bash
python3 scripts/generate_test_keys.py
```

这将在 `config/keys/` 目录下生成:
- `test_private_key.pem` - 私钥文件
- `test_public_key.pem` - 公钥文件

### 2. 使用生产密钥

将生产环境的密钥文件放到 `config/keys/` 目录:

```bash
config/keys/
├── prod_private_key.pem
└── prod_public_key.pem
```

然后在 `config/env/prod.yaml` 中配置:

```yaml
security:
  private_key_path: "config/keys/prod_private_key.pem"
  public_key_path: "config/keys/prod_public_key.pem"
```

### 3. 密钥格式要求

密钥文件必须是PEM格式:

**私钥格式:**
```
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
-----END RSA PRIVATE KEY-----
```

**公钥格式:**
```
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
-----END PUBLIC KEY-----
```

### 4. 在代码中使用RSA签名

```python
from utils.rsa_signer import RSASigner

# 创建签名器
signer = RSASigner(
    private_key_path="config/keys/test_private_key.pem",
    public_key_path="config/keys/test_public_key.pem"
)

# 签名
data = "key1=value1&key2=value2"
signature = signer.sign(data)

# 验签
is_valid = signer.verify(data, signature)
```

---

## API接口定义

### 1. 使用GenericAPI

```python
from api.generic_api import GenericAPI
from api.models import APIRequest
from utils.config_manager import ConfigManager

# 创建配置管理器
config = ConfigManager()

# 创建API客户端
api = GenericAPI(config=config)

# 构建请求
request = APIRequest(
    txn_seqno="TEST20260312001",
    txn_time="20260312140000",
    mch_id="M123456",
    total_amount="100.00",
    pay_type="WECHAT_APPLET",
    notify_url="https://example.com/notify"
)

# 发送请求
response = api.call_api(request)

# 处理响应
if response.is_success():
    print(f"订单创建成功: {response.order_id}")
else:
    print(f"订单创建失败: {response.return_msg}")

# 关闭连接
api.close()
```

### 2. 使用上下文管理器

```python
from api.generic_api import GenericAPI
from utils.config_manager import ConfigManager

config = ConfigManager()

# 使用with语句自动管理资源
with GenericAPI(config=config) as api:
    request = APIRequest(...)
    response = api.call_api(request)
    # 资源会自动释放
```

### 3. 定义新的API接口

如果需要添加新的API接口,在 `api/` 目录下创建新文件:

```python
# api/refund_api.py
from attrs import define, field
from typing import Optional
from utils.http_client import HTTPClient
from utils.config_manager import ConfigManager

@define
class RefundAPI:
    """退款接口封装"""
    
    config: ConfigManager = field()
    http_client: Optional[HTTPClient] = field(default=None)
    
    def __attrs_post_init__(self):
        if self.http_client is None:
            self.http_client = HTTPClient(
                timeout=self.config.get('api.timeout', 30)
            )
    
    def refund_order(self, order_id: str, refund_amount: str):
        """退款接口"""
        url = self.config.get('api.base_url') + '/api/refund'
        
        request_data = {
            'order_id': order_id,
            'refund_amount': refund_amount
        }
        
        response = self.http_client.post(
            url=url,
            headers={'Content-Type': 'application/json'},
            body=request_data
        )
        
        return response['body']
```

### 4. 定义数据模型

在 `api/models.py` 中定义新的数据模型:

```python
from attrs import define, field, validators
from typing import Optional

@define
class RefundRequest:
    """退款请求对象"""
    
    order_id: str = field(validator=validators.instance_of(str))
    refund_amount: str = field(validator=validators.instance_of(str))
    refund_reason: Optional[str] = field(default=None)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'order_id': self.order_id,
            'refund_amount': self.refund_amount,
            'refund_reason': self.refund_reason
        }
```

---

## 编写测试用例

### 1. 使用pytest fixtures

框架提供了丰富的fixtures,在 `testcases/conftest.py` 中定义:

```python
def test_call_api(generic_api, data_generator):
    """测试创建订单"""
    # 使用data_generator生成测试数据
    txn_seqno = data_generator.generate_txn_seqno()
    txn_time = data_generator.generate_timestamp()
    
    # 构建请求
    request = APIRequest(
        txn_seqno=txn_seqno,
        txn_time=txn_time,
        mch_id="M123456",
        total_amount="100.00",
        pay_type="WECHAT_APPLET",
        notify_url="https://example.com/notify"
    )
    
    # 调用API
    response = generic_api.call_api(request)
    
    # 断言
    assert response.is_success()
    assert response.order_id is not None
```

### 2. 使用支付场景编排器

```python
def test_direct_mode_payment(api_scenarios):
    """测试直清模式支付"""
    response = api_scenarios.direct_mode_payment(
        pay_type='WECHAT_APPLET',
        total_amount='100.00'
    )
    
    assert response.is_success()
```

### 3. 使用断言引擎

```python
from utils.assertion_engine import AssertionEngine

def test_with_assertions(generic_api):
    """使用断言引擎测试"""
    response = generic_api.call_api(...)
    
    # 创建断言引擎
    assertion = AssertionEngine()
    
    # 执行断言
    assertion.assert_field_equals(response.to_dict(), 'return_code', '0000')
    assertion.assert_field_exists(response.to_dict(), 'order_id')
```

### 4. 数据驱动测试

```python
import pytest
from utils.data_driver import DataDriver

# 加载测试数据
driver = DataDriver()
test_data = driver.load_from_csv('testdata/payment_data.csv')

@pytest.mark.parametrize('data', test_data)
def test_payment_with_data(api_scenarios, data):
    """数据驱动测试"""
    response = api_scenarios.direct_mode_payment(
        pay_type=data['pay_type'],
        total_amount=data['amount']
    )
    
    assert response.is_success()
```

### 5. 使用pytest标记

```python
import pytest

@pytest.mark.smoke
def test_smoke_case():
    """冒烟测试用例"""
    pass

@pytest.mark.direct_mode
def test_direct_mode():
    """直清模式测试"""
    pass

@pytest.mark.performance
def test_performance():
    """性能测试"""
    pass
```

---

## 执行测试

### 1. 基本执行命令

```bash
# 运行所有测试
python3 -m pytest testcases/

# 运行特定目录
python3 -m pytest testcases/generated/

# 运行特定文件
python3 -m pytest testcases/generated/test_direct_mode_gen.py

# 运行特定测试函数
python3 -m pytest testcases/generated/test_direct_mode_gen.py::test_wechat_applet_payment
```

### 2. 使用标记过滤

```bash
# 只运行冒烟测试
python3 -m pytest testcases/ -m smoke

# 只运行直清模式测试
python3 -m pytest testcases/ -m direct_mode

# 运行多个标记
python3 -m pytest testcases/ -m "smoke or regression"

# 排除某些标记
python3 -m pytest testcases/ -m "not performance"
```

### 3. 控制输出详细程度

```bash
# 详细输出
python3 -m pytest testcases/ -v

# 非常详细的输出
python3 -m pytest testcases/ -vv

# 简洁输出
python3 -m pytest testcases/ -q

# 显示print输出
python3 -m pytest testcases/ -s
```

### 4. 失败时的行为

```bash
# 第一个失败后停止
python3 -m pytest testcases/ -x

# 失败N次后停止
python3 -m pytest testcases/ --maxfail=3

# 只运行上次失败的用例
python3 -m pytest testcases/ --lf

# 先运行上次失败的用例
python3 -m pytest testcases/ --ff
```

### 5. 并行执行

```bash
# 安装pytest-xdist
pip install pytest-xdist

# 自动检测CPU核心数并行执行
python3 -m pytest testcases/ -n auto

# 指定并行进程数
python3 -m pytest testcases/ -n 4
```

### 6. 生成测试报告

```bash
# 生成HTML报告
python3 -m pytest testcases/ --html=reports/report.html

# 生成JUnit XML报告
python3 -m pytest testcases/ --junitxml=reports/junit.xml
```

---

## 测试用例自动转换

### 1. 从Markdown转换测试用例

框架支持从Markdown格式的测试用例文档自动生成可执行的pytest代码。

**Markdown测试用例格式:**

```markdown
## TC001 - 微信小程序支付

**测试目标:** 验证微信小程序支付功能

**前置条件:**
- 商户已开通微信小程序支付
- 用户已授权

**测试步骤:**
1. 构建支付请求,支付方式为WECHAT_APPLET,金额为100.00元
2. 调用创单接口
3. 验证返回结果

**预期结果:**
- 返回码为0000
- 返回订单号
- 返回支付信息
```

### 2. 使用CLI转换工具

```bash
# 基本转换
python3 convert.py -i testdata/test_cases.md -o testcases/generated/

# 按支付模式分组
python3 convert.py -i testdata/test_cases.md -o testcases/generated/ -g payment_mode

# 过滤特定支付方式
python3 convert.py -i testdata/test_cases.md -o testcases/generated/ -f "pay_type=WECHAT_APPLET"

# 指定输出格式
python3 convert.py -i testdata/test_cases.md -o testcases/generated/ --format pytest
```

### 3. 在代码中使用转换功能

```python
from utils.test_parser import TestCaseParser
from utils.code_generator import CodeGenerator

# 解析Markdown测试用例
parser = TestCaseParser()
test_cases = parser.parse('testdata/test_cases.md')

# 生成pytest代码
generator = CodeGenerator()
generator.generate_test_file(
    test_cases=test_cases,
    output_path='testcases/generated/test_generated.py',
    group_by='payment_mode'
)
```

---

## 高级功能

### 1. 中间件配置

编辑 `config/middleware.yaml`:

```yaml
middlewares:
  - name: logging
    enabled: true
    priority: 100
    config:
      log_request: true
      log_response: true
      
  - name: signature
    enabled: true
    priority: 90
    config:
      sign_request: true
      verify_response: true
      
  - name: retry
    enabled: true
    priority: 80
    config:
      max_retries: 3
      retry_codes: [500, 502, 503]
```

### 2. 并发执行测试

```python
from utils.concurrent_executor import ConcurrentExecutor

def payment_task(data):
    """支付任务"""
    # 执行支付逻辑
    return result

# 创建并发执行器
executor = ConcurrentExecutor(thread_count=10)

# 准备测试数据
test_data = [...]

# 并发执行
results = executor.execute(payment_task, test_data)

# 获取统计信息
stats = executor.get_statistics()
print(f"TPS: {stats['tps']}")
print(f"P95响应时间: {stats['p95_response_time']}ms")
```

### 3. 存储管理

```python
from utils.storage_manager import StorageManager

# 创建存储管理器
storage = StorageManager(db_path="storage/test.db")

# 保存测试结果
storage.save_test_result({
    'test_id': 'TC001',
    'status': 'passed',
    'duration': 1.5,
    'timestamp': '2026-03-12 14:00:00'
})

# 查询测试结果
results = storage.get_test_results(
    filters={'status': 'passed'},
    limit=10
)

# 关闭连接
storage.close()
```

### 4. 自定义数据生成

```python
from utils.data_generator import DataGenerator

generator = DataGenerator()

# 生成唯一流水号
txn_seqno = generator.generate_txn_seqno()

# 生成时间戳
txn_time = generator.generate_timestamp()

# 生成订单金额
amount = generator.generate_amount(min_amount=0.01, max_amount=1000.0)

# 生成用户ID
user_id = generator.generate_user_id()
```

### 5. 环境变量配置

```bash
# 设置环境
export ENV=test

# 覆盖API地址
export CREATEPAY_API_BASE_URL="https://custom-api.com"

# 覆盖商户号
export CREATEPAY_MERCHANT_MCH_ID="M123456"

# 覆盖日志级别
export CREATEPAY_LOGGING_LEVEL="DEBUG"
```

---

## 常见问题

### 1. 密钥文件找不到

**问题:** `RSASignerError: Private key file not found`

**解决方案:**
- 检查 `config/config.yaml` 中的密钥路径配置
- 确保密钥文件存在于指定路径
- 使用 `python3 scripts/generate_test_keys.py` 生成测试密钥

### 2. 配置文件加载失败

**问题:** `ConfigError: Configuration file not found`

**解决方案:**
- 确保在 `api-test-framework` 目录下运行命令
- 检查配置文件路径是否正确
- 使用绝对路径或相对于项目根目录的路径

### 3. 测试执行失败

**问题:** 测试用例执行失败

**解决方案:**
- 检查API地址配置是否正确
- 确认网络连接正常
- 查看日志文件 `logs/pytest.log` 获取详细错误信息
- 使用 `-vv` 参数查看详细输出

### 4. 中间件不生效

**问题:** 配置的中间件没有生效

**解决方案:**
- 检查 `config/middleware.yaml` 配置
- 确认中间件的 `enabled` 字段为 `true`
- 检查中间件优先级配置

---

## 技术支持

如有问题,请查看:
- 项目README: `README.md`
- API文档: `api/` 目录下的源码注释
- 测试示例: `testcases/` 目录下的测试用例

或联系开发团队获取支持。
