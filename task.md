# 实现计划: CreatePay测试自动化框架

## 概述

本实现计划将基于Python3构建统一创单接口(createpay)测试自动化框架。框架采用混合方案设计:借鉴aomaker框架的接口对象化建模和中间件机制,同时创新性地提供测试用例自动转换能力(Markdown→可执行代码),实现完整的测试数据管理、接口请求封装、签名验签、报告生成等能力,支持52个核心测试用例的自动化执行,覆盖直清、账户、担保、分账等多种支付模式和15+种支付方式。

## 核心创新点

1. **测试用例自动转换**(任务10-17,优先级最高): 从Markdown测试用例文档自动生成可执行pytest代码,大幅减少手工编写测试代码的工作量
2. **接口对象化建模**(任务11): 使用attrs库进行声明式接口定义,提供完整的IDE类型提示和参数验证
3. **中间件机制**(任务13): 可插拔的请求/响应处理链,支持日志、签名、重试、性能统计等功能
4. **存储管理**(任务14): 使用SQLite统一管理配置、缓存、Schema、测试用例和测试结果

## 任务列表

- [x] 1. 搭建项目基础结构和配置层
  - 创建项目目录结构(config、utils、api、testcases、testdata、reports、logs)
  - 创建requirements.txt文件,定义项目依赖(pytest、requests、cryptography、pyyaml、allure-pytest、openpyxl、jinja2)
  - 创建pytest.ini配置文件
  - 创建README.md项目说明文档
  - _需求: 1.1, 1.3, 1.5_

- [x] 2. 实现配置管理器(ConfigManager)
  - [x] 2.1 实现配置加载和解析功能
    - 实现从YAML文件加载配置的load_config方法
    - 实现支持点号分隔嵌套键的get方法
    - 实现配置验证validate方法
    - 支持环境变量覆盖配置
    - _需求: 8.1, 8.2, 8.3, 8.6_
  
  - [x] 2.2 创建多环境配置文件
    - 创建config/config.yaml主配置文件
    - 创建config/env/test.yaml测试环境配置
    - 创建config/env/uat.yaml UAT环境配置
    - 创建config/env/prod.yaml生产环境配置
    - _需求: 8.4, 16.1, 16.2_
  
  - [ ]* 2.3 编写ConfigManager单元测试
    - 测试配置加载功能
    - 测试嵌套键获取功能
    - 测试配置验证功能
    - 测试环境变量覆盖功能

- [x] 3. 实现日志记录器(Logger)
  - [x] 3.1 实现日志记录核心功能
    - 实现支持五个日志级别的日志记录方法(debug、info、warning、error、critical)
    - 实现日志格式化配置
    - 实现控制台和文件双输出
    - 实现日志文件按日期滚动和大小限制
    - _需求: 7.1, 7.5, 7.6, 7.7, 7.9_
  
  - [x] 3.2 实现敏感信息脱敏功能
    - 实现mask_sensitive_data静态方法
    - 支持对密钥、密码等敏感字段脱敏
    - _需求: 7.8_
  
  - [ ]* 3.3 编写Logger单元测试
    - 测试各级别日志记录
    - 测试日志格式
    - 测试敏感信息脱敏

- [x] 4. 实现测试数据生成器(DataGenerator)
  - [x] 4.1 实现数据生成方法
    - 实现generate_txn_seqno方法生成32位唯一流水号
    - 实现generate_timestamp方法生成时间戳(YYYYMMDDHHmmss格式)
    - 实现generate_date方法生成日期(YYYYMMDD格式)
    - 实现generate_user_id方法生成唯一用户ID
    - 实现generate_amount方法生成订单金额(支持最小0.01元)
    - 实现generate_merchant_id方法生成商户编号
    - _需求: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_
  
  - [ ]* 4.2 编写DataGenerator单元测试
    - 测试流水号唯一性
    - 测试时间戳格式
    - 测试金额范围和格式
    - **属性1: 数据唯一性**
    - **验证: 需求3.7**

- [x] 5. 实现RSA签名验签模块(RSASigner)
  - [x] 5.1 实现RSA签名验签核心功能
    - 实现load_private_key方法从PEM文件加载私钥
    - 实现load_public_key方法从PEM文件加载公钥
    - 实现sign方法使用SHA256WithRSA算法签名
    - 实现verify方法验证签名
    - 实现异常处理和错误信息
    - _需求: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_
  
  - [x] 5.2 创建测试用RSA密钥对
    - 生成测试用私钥文件config/keys/private_key.pem
    - 生成测试用公钥文件config/keys/public_key.pem
    - _需求: 5.4, 5.5_
  
  - [ ]* 5.3 编写RSASigner单元测试
    - 测试签名生成
    - 测试签名验证
    - 测试异常场景
    - **属性2: 签名验签一致性**
    - **验证: 需求5.1, 5.2**

- [x] 6. 实现HTTP客户端(HTTPClient)
  - [x] 6.1 实现HTTP请求核心功能
    - 实现post方法发送POST请求
    - 实现请求超时设置(默认30秒)
    - 实现请求重试机制
    - 实现连接池管理
    - 实现响应时间统计get_response_time方法
    - 实现close方法关闭连接
    - _需求: 4.1, 4.2, 4.3, 4.4, 4.6, 4.8, 4.9_
  
  - [x] 6.2 实现请求响应日志记录
    - 集成Logger记录完整请求和响应信息
    - 实现敏感信息脱敏
    - _需求: 4.7_
  
  - [ ]* 6.3 编写HTTPClient单元测试
    - 测试POST请求
    - 测试超时和重试
    - 测试响应时间统计
    - 使用mock模拟HTTP响应

- [x] 7. 实现断言引擎(AssertionEngine)
  - [x] 7.1 实现断言方法
    - 实现assert_status_code方法断言响应状态码
    - 实现assert_field_exists方法断言字段存在
    - 实现assert_field_equals方法断言字段值相等
    - 实现assert_field_contains方法断言字段值包含
    - 实现assert_response_time方法断言响应时间
    - 实现assert_json_schema方法断言JSON Schema
    - _需求: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_
  
  - [x] 7.2 实现断言失败信息格式化
    - 提供清晰的失败信息,包含期望值和实际值
    - _需求: 9.8_
  
  - [ ]* 7.3 编写AssertionEngine单元测试
    - 测试各类断言方法
    - 测试断言失败信息格式
    - 测试边界条件

- [x] 8. 实现数据驱动引擎(DataDriver)
  - [x] 8.1 实现数据加载方法
    - 实现load_from_csv方法从CSV文件加载数据
    - 实现load_from_excel方法从Excel文件加载数据
    - 实现load_from_json方法从JSON文件加载数据
    - 实现load_from_yaml方法从YAML文件加载数据
    - _需求: 10.1, 10.2, 10.3, 10.4_
  
  - [x] 8.2 创建测试数据文件示例
    - 创建testdata/payment_data.csv示例文件
    - 创建testdata/payment_data.xlsx示例文件
    - 创建testdata/payment_data.json示例文件
    - _需求: 10.1, 10.2, 10.3_
  
  - [ ]* 8.3 编写DataDriver单元测试
    - 测试各种格式数据加载
    - 测试数据格式转换
    - 测试异常文件处理

- [x] 9. 实现并发执行器(ConcurrentExecutor)
  - [x] 9.1 实现并发执行核心功能
    - 实现execute方法支持多线程并发执行
    - 实现线程数配置(默认10)
    - 实现数据隔离机制
    - _需求: 11.1, 11.2, 11.3, 11.6_
  
  - [x] 9.2 实现性能指标统计
    - 实现get_tps方法计算TPS
    - 实现get_response_time_percentile方法计算响应时间百分位(P50/P95/P99)
    - 实现get_statistics方法获取完整统计信息
    - _需求: 11.4, 11.5, 15.1, 15.2_
  
  - [ ]* 9.3 编写ConcurrentExecutor单元测试
    - 测试并发执行功能
    - 测试TPS计算
    - 测试响应时间百分位计算
    - **属性3: 并发数据唯一性**
    - **验证: 需求11.6**

- [x] 10. 实现增强版测试用例解析器(TestCaseParser)
  - [x] 10.1 实现核心数据模型
    - 创建TestStep、ExpectedResult、TestCase数据类
    - 实现数据类的基本验证方法
    - _需求: 19.1, 19.2_
  
  - [x] 10.2 实现Markdown解析功能
    - 实现parse方法解析Markdown格式测试用例
    - 实现_extract_case_id和_extract_case_name方法提取用例基本信息
    - 实现_extract_test_objective和_extract_preconditions方法
    - 实现_extract_test_steps方法提取测试步骤
    - 实现_extract_parameters方法从步骤文本提取业务参数(支付方式、金额等)
    - 实现_extract_expected_results方法提取预期结果
    - 实现_extract_assertions方法从预期结果提取断言条件
    - _需求: 19.1, 19.2, 19.5_
  
  - [x] 10.3 实现智能推断功能
    - 实现_infer_payment_method方法推断支付方式
    - 实现_infer_payment_mode方法推断支付模式(直清/账户/担保/分账)
    - 实现_assign_priority方法分配优先级(P0/P1/P2/P3)
    - 实现_generate_tags方法生成标签
    - _需求: 19.2_
  
  - [x] 10.4 实现格式转换和保存功能
    - 实现validate方法验证用例完整性
    - 实现to_json方法转换为JSON格式
    - 实现to_yaml方法转换为YAML格式
    - 实现save_parsed_data方法保存解析结果
    - _需求: 19.3, 19.4_
  
  - [ ]* 10.5 编写TestCaseParser单元测试
    - 测试Markdown解析功能
    - 测试参数提取功能
    - 测试断言提取功能
    - 测试智能推断功能
    - 测试格式转换功能
    - **属性4: 解析往返一致性**
    - **验证: 需求19.6**

- [x] 11. 实现接口对象构建器(APIObjectBuilder)
  - [x] 11.1 实现接口对象数据模型(attrs)
    - 创建WeChatData、AlipayData扩展数据类(attrs定义)
    - 创建PayeeInfo收款方信息类(attrs定义,包含金额验证)
    - 创建CreatePayRequest请求对象类(attrs定义,包含参数验证)
    - 创建CreatePayResponse响应对象类(attrs定义)
    - 实现to_dict和from_dict转换方法
    - _需求: 1.2_
  
  - [x] 11.2 实现对象构建功能
    - 实现build_request方法从参数字典构建请求对象
    - 实现build_response方法从响应数据构建响应对象
    - 集成attrs验证器进行参数验证
    - _需求: 1.2_
  
  - [x] 11.3 实现代码生成功能
    - 实现generate_request_class_code方法生成请求类代码
    - 实现generate_response_class_code方法生成响应类代码
    - 支持动态字段定义和验证器生成
    - _需求: 19.4_
  
  - [ ]* 11.4 编写APIObjectBuilder单元测试
    - 测试请求对象构建
    - 测试响应对象构建
    - 测试参数验证功能
    - 测试代码生成功能

- [x] 12. 实现代码生成器(CodeGenerator)
  - [x] 12.1 创建Jinja2模板
    - 创建templates/test_case.py.j2测试用例模板
    - 创建templates/api_object.py.j2接口对象模板
    - 创建templates/test_data.py.j2测试数据模板
    - 设计模板变量和过滤器
    - _需求: 19.4_
  
  - [x] 12.2 实现代码生成核心功能
    - 实现generate_test_function方法生成pytest测试函数
    - 实现generate_request_builder方法生成请求构造代码
    - 实现generate_assertions方法生成断言代码
    - 实现_render_template方法渲染Jinja2模板
    - _需求: 19.4_
  
  - [x] 12.3 实现文件生成功能
    - 实现generate_test_file方法生成完整测试文件
    - 实现generate_test_data_file方法生成测试数据文件
    - 实现generate_api_object_file方法生成接口对象文件
    - 支持按支付模式分组生成测试文件
    - _需求: 19.4_
  
  - [ ]* 12.4 编写CodeGenerator单元测试
    - 测试模板渲染功能
    - 测试测试函数生成
    - 测试断言代码生成
    - 测试文件生成功能

- [x] 13. 实现中间件注册器和中间件(MiddlewareRegistry)
  - [x] 13.1 实现中间件基类
    - 创建middlewares/base_middleware.py
    - 定义BaseMiddleware抽象基类
    - 定义process_request和process_response抽象方法
    - 实现优先级和启用状态管理
    - _需求: 20.1_
  
  - [x] 13.2 实现中间件注册器
    - 创建utils/middleware_registry.py
    - 实现register和unregister方法
    - 实现get_middlewares方法按优先级排序
    - 实现process_request和process_response执行中间件链
    - 实现load_from_config方法从配置文件加载中间件
    - _需求: 20.1, 20.2_
  
  - [x] 13.3 实现日志中间件(LoggingMiddleware)
    - 创建middlewares/logging_middleware.py
    - 实现请求和响应日志记录
    - 实现敏感信息脱敏功能
    - 支持配置日志开关和脱敏字段
    - _需求: 7.1, 7.8_
  
  - [x] 13.4 实现签名中间件(SignatureMiddleware)
    - 创建middlewares/signature_middleware.py
    - 实现请求自动签名功能
    - 实现响应自动验签功能
    - 集成RSASigner
    - _需求: 5.1, 5.2_
  
  - [x] 13.5 实现重试中间件(RetryMiddleware)
    - 创建middlewares/retry_middleware.py
    - 实现请求重试逻辑
    - 支持配置重试次数和退避策略
    - 支持配置需要重试的状态码
    - _需求: 4.4_
  
  - [x] 13.6 实现性能统计中间件(PerformanceMiddleware)
    - 创建middlewares/performance_middleware.py
    - 实现响应时间统计
    - 实现性能指标收集(P50/P95/P99)
    - 实现性能告警功能
    - _需求: 15.1, 15.2_
  
  - [x] 13.7 创建中间件配置文件
    - 创建config/middleware.yaml
    - 配置各中间件的启用状态、优先级和参数
    - _需求: 8.1, 8.2_
  
  - [ ]* 13.8 编写中间件单元测试
    - 测试中间件注册和排序
    - 测试中间件链执行
    - 测试各中间件功能
    - 测试配置加载

- [x] 14. 实现存储管理器(StorageManager)
  - [x] 14.1 实现数据库初始化
    - 创建utils/storage_manager.py
    - 设计数据库表结构(config、cache、schema、test_cases、test_results)
    - 实现_init_database方法创建表
    - _需求: 1.1_
  
  - [x] 14.2 实现配置存储功能
    - 实现save_config和get_config方法
    - 支持配置的增删改查
    - _需求: 8.1, 8.2_
  
  - [x] 14.3 实现Schema存储功能
    - 实现save_schema和get_schema方法
    - 支持JSON Schema的存储和查询
    - _需求: 9.6_
  
  - [x] 14.4 实现测试用例存储功能
    - 实现save_test_case和get_test_cases方法
    - 支持测试用例的持久化和查询
    - 支持按条件过滤查询
    - _需求: 2.1, 2.2_
  
  - [x] 14.5 实现测试结果存储功能
    - 实现save_test_result和get_test_results方法
    - 支持测试结果的持久化和统计
    - _需求: 6.2, 6.3_
  
  - [ ]* 14.6 编写StorageManager单元测试
    - 测试数据库初始化
    - 测试各类数据的存储和查询
    - 测试数据库连接管理

- [x] 15. 检查点 - 确保转换层所有组件测试通过
  - 确保TestCaseParser、APIObjectBuilder、CodeGenerator、MiddlewareRegistry、StorageManager测试通过
  - 询问用户是否有问题

- [x] 16. 实现完整测试用例转换流程
  - [x] 16.1 实现转换流程脚本
    - 创建utils/conversion_workflow.py
    - 实现parse_test_cases方法调用TestCaseParser解析Markdown
    - 实现build_api_objects方法调用APIObjectBuilder构建接口对象
    - 实现generate_test_code方法调用CodeGenerator生成测试代码
    - 实现完整的转换流程编排
    - _需求: 19.1, 19.2, 19.3, 19.4_
  
  - [x] 16.2 转换统一创单接口测试用例
    - 解析testdata/统一创单接口createpay测试用例.md
    - 生成testcases/generated/test_direct_mode_gen.py(13个用例)
    - 生成testcases/generated/test_account_mode_gen.py(10个用例)
    - 生成testcases/generated/test_guarantee_mode_gen.py(6个用例)
    - 生成testcases/generated/test_split_mode_gen.py(12个用例)
    - 生成testcases/generated/test_cloudpay_gen.py(3个用例)
    - 生成testcases/generated/test_exception_gen.py(6个用例)
    - 生成testcases/generated/test_performance_gen.py(2个用例)
    - _需求: 2.2, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 13.1, 13.2, 13.3, 13.4, 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_
  
  - [x] 16.3 验证生成代码的正确性
    - 检查生成的测试代码语法正确性
    - 验证导入语句完整性
    - 验证测试函数命名规范
    - 验证断言逻辑正确性
    - _需求: 19.5_
  
  - [ ]* 16.4 编写转换流程集成测试
    - 测试完整转换流程
    - 测试生成代码的可执行性
    - **属性7: 生成代码可执行性**
    - **验证: 需求19.4**

- [x] 17. 实现CLI转换工具
  - [x] 17.1 创建命令行工具
    - 创建convert.py命令行工具脚本
    - 实现命令行参数解析(输入文件、输出目录、支付模式过滤等)
    - 集成转换流程
    - _需求: 18.1, 18.2, 18.3_
  
  - [x] 17.2 添加CLI使用说明
    - 在README.md中添加CLI工具使用示例
    - 说明各参数含义和使用场景
    - _需求: 18.1_

- [x] 18. 实现数据模型定义
  - 创建api/models.py文件
  - 定义TestResult数据类
  - 定义PerformanceMetrics数据类
  - 定义SplitRule数据类
  - _需求: 1.2_

- [x] 19. 检查点 - 确保工具层所有测试通过
  - 确保所有工具层组件测试通过,询问用户是否有问题

- [x] 20. 增强HTTP客户端支持中间件(HTTPClient)
  - [x] 20.1 集成中间件注册器
    - 修改HTTPClient构造函数接受MiddlewareRegistry参数
    - 在post方法中执行请求中间件链
    - 在post方法中执行响应中间件链
    - _需求: 4.1, 4.7_
  
  - [x] 20.2 保持原有HTTP客户端功能
    - 保持请求超时、重试、连接池等功能
    - 保持响应时间统计功能
    - _需求: 4.2, 4.3, 4.4, 4.8, 4.9_
  
  - [ ]* 20.3 编写增强版HTTPClient单元测试
    - 测试中间件集成
    - 测试中间件链执行顺序
    - 测试原有功能兼容性

- [x] 21. 实现创单接口封装(CreatePayAPI)
  - [x] 21.1 实现接口调用核心功能(attrs版本)
    - 创建api/createpay_api.py,使用attrs定义CreatePayAPI类
    - 实现create_order方法创建支付订单
    - 实现_build_request_data方法构建请求数据
    - 实现_sign_request方法对请求签名
    - 实现_verify_response方法验证响应签名
    - 集成HTTPClient、RSASigner、ConfigManager、MiddlewareRegistry
    - _需求: 4.1, 5.1, 5.2_
  
  - [ ]* 21.2 编写CreatePayAPI单元测试
    - 测试订单创建流程
    - 测试请求签名
    - 测试响应验签
    - 使用mock模拟接口响应

- [x] 22. 实现支付场景编排(PaymentScenarios)
  - [x] 22.1 实现支付场景方法
    - 实现direct_mode_payment方法支持直清模式支付
    - 实现account_mode_payment方法支持账户模式支付
    - 实现guarantee_payment方法支持担保支付
    - 实现split_payment方法支持分账支付
    - 集成CreatePayAPI和DataGenerator
    - _需求: 13.1, 13.2, 13.3, 13.4_
  
  - [ ]* 22.2 编写PaymentScenarios单元测试
    - 测试各种支付场景
    - 测试数据构造
    - 使用mock模拟接口调用

- [ ] 23. 实现测试报告生成器(ReportGenerator)
  - [ ] 23.1 实现报告生成功能
    - 实现generate_html_report方法生成HTML报告
    - 实现generate_allure_report方法生成Allure报告
    - 实现calculate_statistics方法计算测试统计信息
    - 使用jinja2模板引擎渲染HTML报告
    - _需求: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.9_
  
  - [ ] 23.2 创建HTML报告模板
    - 创建reports/template.html报告模板文件
    - 设计报告样式和布局
    - _需求: 6.1_
  
  - [ ]* 23.3 编写ReportGenerator单元测试
    - 测试HTML报告生成
    - 测试统计信息计算
    - 测试报告内容完整性

- [x] 24. 实现pytest配置和fixtures
  - [x] 24.1 创建conftest.py配置文件
    - 创建testcases/conftest.py
    - 定义全局fixtures(config、logger、http_client、rsa_signer、data_generator、middleware_registry等)
    - 配置pytest钩子函数
    - 集成Allure报告
    - _需求: 1.2, 6.7_
  
  - [x] 24.2 配置pytest.ini
    - 配置测试发现规则
    - 配置日志输出
    - 配置标记(markers)定义
    - 配置Allure报告路径
    - _需求: 2.3, 2.4_

- [x] 25. 检查点 - 确保业务层所有测试通过
  - 确保所有业务层组件测试通过,询问用户是否有问题

- [x] 26. 验证自动生成的测试用例
  - [x] 26.1 验证直清模式生成的测试用例
    - 检查testcases/generated/test_direct_mode_gen.py
    - 验证13个直清模式测试用例的正确性
    - 运行生成的测试用例确保可执行
    - _需求: 2.2, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 13.1_
  
  - [x] 26.2 验证账户模式生成的测试用例
    - 检查testcases/generated/test_account_mode_gen.py
    - 验证10个账户模式测试用例的正确性
    - _需求: 2.2, 13.2_
  
  - [x] 26.3 验证担保支付生成的测试用例
    - 检查testcases/generated/test_guarantee_mode_gen.py
    - 验证6个担保支付测试用例的正确性
    - _需求: 2.2, 13.3_
  
  - [x] 26.4 验证分账支付生成的测试用例
    - 检查testcases/generated/test_split_mode_gen.py
    - 验证12个分账支付测试用例的正确性
    - _需求: 2.2, 13.4_
  
  - [x] 26.5 验证云闪付生成的测试用例
    - 检查testcases/generated/test_cloudpay_gen.py
    - 验证3个云闪付测试用例的正确性
    - _需求: 2.2, 12.3_
  
  - [x] 26.6 验证异常场景生成的测试用例
    - 检查testcases/generated/test_exception_gen.py
    - 验证6个异常场景测试用例的正确性
    - _需求: 2.2, 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_
  
  - [x] 26.7 验证性能测试生成的测试用例
    - 检查testcases/generated/test_performance_gen.py
    - 验证2个性能测试用例的正确性
    - _需求: 2.2, 15.1, 15.2, 15.3, 15.6_
  
  - [ ]* 26.8 编写生成代码的集成测试
    - 测试端到端支付流程
    - 验证响应数据完整性
    - 验证签名正确性
    - **属性5: 收款方金额总和等于订单金额**
    - **验证: 需求14.4**
    - **属性6: 分账金额总和等于订单金额**
    - **验证: 需求14.4**

- [ ] 27. 实现手工编写的补充测试用例
  - [ ] 27.1 创建自定义场景测试
    - 创建testcases/manual/test_custom_scenarios.py
    - 实现组合支付测试用例
    - 实现充值消费场景测试用例
    - _需求: 13.5, 13.6_
  
  - [ ] 27.2 创建数据驱动测试用例
    - 创建testcases/manual/test_data_driven.py
    - 使用DataDriver从CSV/Excel/JSON加载测试数据
    - 实现参数化测试用例
    - 验证数据驱动功能
    - _需求: 10.5, 10.6, 10.7_
  
  - [ ]* 27.3 编写手工测试用例的集成测试
    - 测试自定义场景
    - 测试数据驱动功能

- [ ] 28. 实现测试执行入口
  - [ ] 28.1 创建run.py测试执行脚本
    - 实现命令行参数解析(环境、用例、标签等)
    - 实现测试执行逻辑
    - 实现测试报告生成
    - 实现退出码返回
    - _需求: 18.1, 18.2, 18.3, 18.4_
  
  - [ ] 28.2 添加命令行使用说明
    - 在README.md中添加命令行使用示例
    - 说明各参数含义
    - _需求: 18.1, 18.2, 18.3_

- [ ] 29. 实现CI/CD集成支持
  - 创建.gitlab-ci.yml或Jenkinsfile示例文件
  - 配置JUnit XML报告生成
  - 配置Allure报告发布
  - 添加CI/CD集成说明文档
  - _需求: 18.5, 18.6_

- [ ] 30. 实现测试数据清理功能
  - 在utils中添加data_cleaner.py模块
  - 实现自动清理测试订单数据功能
  - 实现数据保留策略配置
  - 实现数据清理日志记录
  - _需求: 17.1, 17.2, 17.3, 17.4, 17.5_

- [ ] 31. 实现框架扩展机制
  - 设计插件接口
  - 实现支付方式插件注册机制
  - 实现自定义断言函数注册
  - 实现自定义数据生成器注册
  - 编写扩展开发文档
  - _需求: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6_

- [ ] 32. 完善项目文档
  - 完善README.md,包含项目介绍、安装说明、快速开始、配置说明、测试用例自动转换使用指南
  - 创建docs/architecture.md架构设计文档
  - 创建docs/user_guide.md用户使用指南
  - 创建docs/developer_guide.md开发者指南
  - 创建docs/extension_guide.md扩展开发指南
  - 创建docs/conversion_guide.md测试用例转换指南(新增)
  - _需求: 1.1, 20.5_

- [ ] 33. 最终检查点 - 执行完整测试套件
  - 执行所有测试用例,确保全部通过
  - 生成测试报告,验证报告完整性
  - 验证日志记录功能
  - 验证多环境配置切换
  - 验证测试用例自动转换功能
  - 询问用户是否有问题或需要调整

## 注意事项

- 标记为`*`的任务为可选任务,可根据项目进度跳过以加快MVP交付
- 每个任务都引用了具体的需求编号,确保需求可追溯性
- 检查点任务用于确保增量验证,及时发现问题
- 属性测试用于验证通用正确性属性
- 单元测试和集成测试确保代码质量
- 任务10-17为核心创新功能(测试用例自动转换),优先级最高
- 转换层组件(TestCaseParser、APIObjectBuilder、CodeGenerator、MiddlewareRegistry、StorageManager)是框架的核心创新点
