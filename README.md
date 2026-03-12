# API Test Automation Framework

通用API测试自动化框架,支持快速对接各类API接口并自动生成测试代码。框架采用插件化架构,可轻松扩展支持新的API。

当前已集成: CreatePay统一创单接口(52个核心测试用例)

## 核心特性

### 🚀 核心创新

1. **通用API架构**: 基于BaseAPI的插件化设计,支持快速对接任意API接口
2. **API注册机制**: 统一的API注册和管理,支持多API并存
3. **测试用例自动转换**: 从Markdown测试用例文档自动生成可执行pytest代码
4. **接口对象化建模**: 使用attrs库进行声明式接口定义,提供完整的IDE类型提示
5. **中间件机制**: 可插拔的请求/响应处理链,支持日志、签名、重试、性能统计
6. **存储管理**: 使用SQLite统一管理配置、缓存、Schema、测试用例和测试结果

### 📋 已集成API



## 项目结构

```
api-test-framework/
├── config/                  # 配置层
│   ├── config.yaml         # 主配置文件
│   ├── middleware.yaml     # 中间件配置
│   ├── env/                # 环境配置
│   └── keys/               # RSA密钥文件
├── utils/                  # 工具层
│   ├── http_client.py      # HTTP客户端
│   ├── rsa_signer.py       # RSA签名验签
│   ├── data_generator.py   # 测试数据生成器
│   ├── logger.py           # 日志记录器
│   ├── config_manager.py   # 配置管理器
│   ├── test_parser.py      # 测试用例解析器
│   ├── code_generator.py   # 代码生成器
│   └── storage_manager.py  # 存储管理器
├── middlewares/            # 中间件
│   ├── logging_middleware.py
│   ├── signature_middleware.py
│   ├── retry_middleware.py
│   └── performance_middleware.py
├── api/                    # 业务层
│   ├── base_api.py         # API基类
│   ├── api_registry.py     # API注册器
│   ├── createpay_api.py    # CreatePay API实现
│   ├── api_scenarios.py    # 场景编排器
│   └── models.py           # 数据模型
├── testcases/              # 用例层
│   ├── generated/          # 自动生成的测试代码
│   └── manual/             # 手工编写的测试代码
├── templates/              # 代码生成模板
├── testdata/               # 测试数据
├── reports/                # 测试报告
├── logs/                   # 日志文件
└── storage/                # SQLite数据库

```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

编辑 `config/config.yaml` 配置文件:

```yaml
environment: test
api:
  base_url: "https://test-api.example.com"
merchant:
  mch_id: "YOUR_MERCHANT_ID"
security:
  private_key_path: "config/keys/private_key.pem"
  public_key_path: "config/keys/public_key.pem"
```

### 3. 转换测试用例

从Markdown文档自动生成测试代码:

```bash
python convert.py --input testdata/统一创单接口createpay测试用例.md --output testcases/generated/
```

### 4. 运行测试

```bash
# 运行所有测试
python run.py

# 运行指定优先级测试
python run.py --markers P0

# 运行指定模式测试
python run.py --markers direct_mode

# 运行指定环境测试
python run.py --env uat
```

### 5. 查看报告

```bash
# 生成Allure报告
allure serve reports/allure-results
```

## 测试用例自动转换

框架的核心创新功能,支持从Markdown测试用例文档自动生成可执行的pytest测试代码。

### 转换流程

```
Markdown测试用例文档
    ↓
[TestCaseParser解析]
    ↓
结构化测试用例数据(JSON)
    ↓
[APIObjectBuilder构建接口对象]
    ↓
接口对象定义(attrs)
    ↓
[CodeGenerator生成代码]
    ↓
可执行测试代码(pytest)
```

### 使用示例

```bash
# 转换所有测试用例
python convert.py --input testdata/统一创单接口createpay测试用例.md

# 转换指定支付模式
python convert.py --input testdata/统一创单接口createpay测试用例.md --mode direct

# 查看转换结果
ls testcases/generated/
```

## CLI转换工具使用指南

### 工具概述

`convert.py` 是测试用例自动转换的命令行工具,支持将Markdown格式的测试用例文档转换为可执行的pytest代码。

### 转换流程

```
Markdown测试用例文档
    ↓
[TestCaseParser解析]
    ↓
结构化测试用例数据(JSON)
    ↓
[APIObjectBuilder构建接口对象]
    ↓
接口对象定义(attrs)
    ↓
[CodeGenerator生成代码]
    ↓
可执行测试代码(pytest)
```

### 命令行参数

#### 必需参数

- `-i, --input`: 输入的Markdown测试用例文件路径

#### 可选参数

- `-o, --output`: 输出目录路径 (默认: `testcases/generated`)
- `-t, --template-dir`: 模板目录路径 (默认: `templates`)
- `-g, --group-by`: 测试用例分组方式 (默认: `payment_mode`)
  - `payment_mode`: 按支付模式分组 (直清/账户/担保/分账)
  - `payment_method`: 按支付方式分组 (微信/支付宝/云闪付等)
  - `priority`: 按优先级分组 (P0/P1/P2/P3)
- `-f, --filter`: 过滤特定的支付模式或支付方式,多个值用逗号分隔
- `--no-save-parsed`: 不保存解析后的JSON数据
- `-v, --verbose`: 详细输出模式
- `--log-level`: 日志级别 (DEBUG/INFO/WARNING/ERROR, 默认: INFO)

### 使用示例

#### 基本用法

```bash
# 转换测试用例文档 (使用默认配置)
python3 convert.py -i ../统一创单接口createpay测试用例.md

# 查看帮助信息
python3 convert.py -h
```

#### 指定输出目录

```bash
# 将生成的测试文件保存到自定义目录
python3 convert.py -i test_cases.md -o testcases/custom
```

#### 按不同方式分组

```bash
# 按支付模式分组 (默认)
python3 convert.py -i test_cases.md -g payment_mode
# 生成: test_direct_gen.py, test_account_gen.py, test_guarantee_gen.py, test_split_gen.py

# 按支付方式分组
python3 convert.py -i test_cases.md -g payment_method
# 生成: test_wechat_gen.py, test_alipay_gen.py, test_cloudpay_gen.py

# 按优先级分组
python3 convert.py -i test_cases.md -g priority
# 生成: test_p0_gen.py, test_p1_gen.py, test_p2_gen.py
```

#### 过滤特定用例

```bash
# 只转换直清和账户模式的用例
python3 convert.py -i test_cases.md -f direct,account

# 只转换微信支付的用例
python3 convert.py -i test_cases.md -g payment_method -f WECHAT_APPLET,WECHAT_NATIVE

# 只转换P0和P1优先级的用例
python3 convert.py -i test_cases.md -g priority -f P0,P1
```

#### 详细输出和调试

```bash
# 启用详细输出
python3 convert.py -i test_cases.md -v

# 设置日志级别为DEBUG
python3 convert.py -i test_cases.md --log-level DEBUG

# 不保存解析数据 (只生成测试代码)
python3 convert.py -i test_cases.md --no-save-parsed
```

### 输出文件说明

#### 生成的测试文件

转换工具会根据分组方式生成不同的测试文件:

**按支付模式分组** (默认):
- `test_direct_gen.py`: 直清模式测试用例
- `test_account_gen.py`: 账户模式测试用例
- `test_guarantee_gen.py`: 担保支付测试用例
- `test_split_gen.py`: 分账支付测试用例
- `test_cloudpay_gen.py`: 云闪付测试用例
- `test_exception_gen.py`: 异常场景测试用例
- `test_performance_gen.py`: 性能测试用例

**按支付方式分组**:
- `test_wechat_gen.py`: 微信支付测试用例
- `test_alipay_gen.py`: 支付宝测试用例
- `test_cloudpay_gen.py`: 云闪付测试用例
- 等等...

**按优先级分组**:
- `test_p0_gen.py`: P0优先级测试用例
- `test_p1_gen.py`: P1优先级测试用例
- `test_p2_gen.py`: P2优先级测试用例
- `test_p3_gen.py`: P3优先级测试用例

#### 解析数据文件

如果未使用 `--no-save-parsed` 参数,会生成以下文件:
- `testdata/parsed/test_cases.json`: JSON格式的解析数据
- `testdata/parsed/test_cases.yaml`: YAML格式的解析数据

### 常见使用场景

#### 场景1: 快速转换所有用例

```bash
# 一键转换,使用默认配置
python3 convert.py -i ../统一创单接口createpay测试用例.md
```

#### 场景2: 只测试特定支付模式

```bash
# 只转换直清模式用例进行快速验证
python3 convert.py -i test_cases.md -f direct -v
```

#### 场景3: 按支付方式组织测试

```bash
# 按支付方式分组,便于按渠道执行测试
python3 convert.py -i test_cases.md -g payment_method
```

#### 场景4: 优先级驱动测试

```bash
# 只转换高优先级用例 (P0, P1)
python3 convert.py -i test_cases.md -g priority -f P0,P1
```

#### 场景5: 调试转换问题

```bash
# 启用详细输出和DEBUG日志
python3 convert.py -i test_cases.md -v --log-level DEBUG
```

### 转换结果验证

转换完成后,可以通过以下方式验证:

```bash
# 1. 查看生成的文件
ls -lh testcases/generated/

# 2. 检查生成代码的语法
python3 -m py_compile testcases/generated/test_*.py

# 3. 运行生成的测试 (需要配置环境)
python3 -m pytest testcases/generated/test_direct_gen.py -v

# 4. 查看解析数据
cat testdata/parsed/test_cases.json | python3 -m json.tool
```

### 故障排查

#### 问题1: 输入文件不存在

```
错误: 输入文件不存在: test_cases.md
解决: 检查文件路径是否正确,使用绝对路径或相对路径
```

#### 问题2: 解析失败

```
错误: 无法解析测试用例
解决: 
  1. 检查Markdown文档格式是否符合规范
  2. 使用 -v 参数查看详细错误信息
  3. 使用 --log-level DEBUG 查看调试日志
```

#### 问题3: 生成代码语法错误

```
错误: 生成的代码有语法错误
解决:
  1. 检查模板文件是否正确
  2. 检查测试用例中的参数是否有特殊字符
  3. 查看日志文件 logs/ConvertCLI.log
```

### 高级用法

#### 自定义模板

```bash
# 使用自定义模板目录
python3 convert.py -i test_cases.md -t custom_templates/
```

#### 批量转换

```bash
# 转换多个测试用例文档
for file in testdata/*.md; do
    python3 convert.py -i "$file" -o "testcases/generated/$(basename $file .md)"
done
```

#### 集成到CI/CD

```bash
# 在CI/CD流水线中使用
python3 convert.py -i test_cases.md --no-save-parsed --log-level WARNING
if [ $? -eq 0 ]; then
    echo "转换成功"
    python3 -m pytest testcases/generated/ -v
else
    echo "转换失败"
    exit 1
fi
```

## 配置说明

### 环境配置

支持多环境配置(TEST/UAT/PROD):

```yaml
# config/env/test.yaml
api:
  base_url: "https://test-api.example.com"
merchant:
  mch_id: "TEST_MERCHANT_ID"
```

### 中间件配置

配置中间件的启用状态和优先级:

```yaml
# config/middleware.yaml
middlewares:
  - name: logging
    enabled: true
    priority: 10
  - name: signature
    enabled: true
    priority: 20
```

## 开发指南

### 扩展框架支持新API

框架采用插件化架构,可以轻松添加新的API支持。详细步骤请参考 [API扩展指南](API_EXTENSION_GUIDE.md)。

#### 快速开始

1. 创建API实现类(继承BaseAPI)
2. 在API注册器中注册
3. 添加配置
4. 编写测试用例

示例:

```python
# api/your_api.py
from api.base_api import BaseAPI

@define
class YourAPI(BaseAPI):
    def __attrs_post_init__(self):
        self.api_name = "your_api"
        super().__attrs_post_init__()
    
    def _build_request_data(self, **kwargs):
        return {"param": kwargs.get("param")}
    
    def _parse_response(self, response_data):
        return response_data
```

完整文档: [API_EXTENSION_GUIDE.md](API_EXTENSION_GUIDE.md)

### 添加新的支付方式(CreatePay)

1. 在 `api/models.py` 中定义新的数据模型
2. 在 `api/generic_api.py` 中添加支付方式支持
3. 在 `testcases/manual/` 中编写测试用例

### 添加自定义中间件

1. 继承 `BaseMiddleware` 类
2. 实现 `process_request` 和 `process_response` 方法
3. 在 `config/middleware.yaml` 中注册

### 扩展断言方法

1. 在 `utils/assertion_engine.py` 中添加新的断言方法
2. 在测试用例中使用新的断言

## 持续集成

### Jenkins

```groovy
pipeline {
    stages {
        stage('Test') {
            steps {
                sh 'python run.py --env test'
            }
        }
        stage('Report') {
            steps {
                allure includeProperties: false, jdk: '', results: [[path: 'reports/allure-results']]
            }
        }
    }
}
```

### GitLab CI

```yaml
test:
  script:
    - pip install -r requirements.txt
    - python run.py --env test
  artifacts:
    paths:
      - reports/
```

## 性能测试

框架支持并发性能测试:

```bash
# 并发100个请求
python run.py --markers performance --concurrent 100

# 查看性能报告
cat reports/performance_report.html
```

## 故障排查

### 常见问题

1. **签名验证失败**: 检查RSA密钥配置是否正确
2. **连接超时**: 检查网络配置和API地址
3. **测试用例解析失败**: 检查Markdown文档格式

### 日志查看

```bash
# 查看最新日志
tail -f logs/test.log

# 查看错误日志
grep ERROR logs/test.log
```

## 贡献指南

欢迎贡献代码和提出建议!

1. Fork 项目
2. 创建特性分支
3. 提交变更
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License

## 联系方式

- 项目维护者: Test Team
- 邮箱: test-team@example.com
- 文档: [Wiki](https://wiki.example.com)

---

**版本**: v1.0.0  
**最后更新**: 2026-03-11
