"""
测试用例解析器 (TestCaseParser)
从Markdown格式的测试用例文档中提取结构化信息
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import re
import json
import yaml


@dataclass
class TestStep:
    """测试步骤"""
    step_no: int
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExpectedResult:
    """预期结果"""
    description: str
    assertions: List[str] = field(default_factory=list)
    response_time_threshold: Optional[float] = None


@dataclass
class TestCase:
    """测试用例数据模型"""
    case_id: str
    case_name: str
    test_objective: str
    priority: str
    preconditions: List[str] = field(default_factory=list)
    test_steps: List[TestStep] = field(default_factory=list)
    expected_results: List[ExpectedResult] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    payment_method: Optional[str] = None
    payment_mode: Optional[str] = None


class TestCaseParser:
    """测试用例解析器"""
    
    # 支付方式映射
    PAYMENT_METHODS = {
        'WECHAT_APPLET': 'wechat',
        'WECHAT_NATIVE': 'wechat',
        'WECHAT_JSAPI': 'wechat',
        'WECHAT_APP': 'wechat',
        'WECHAT_H5': 'wechat',
        'ALIPAY_NATIVE': 'alipay',
        'ALIPAY_APP': 'alipay',
        'ALIPAY_APPLET': 'alipay',
        'ALIPAY_H5': 'alipay',
        'CLOUDPAY_APP': 'cloudpay',
        'CLOUDPAY_APPLET': 'cloudpay',
        'AGGREGATE_CODE': 'aggregate',
        'POS_NATIVE': 'pos',
        'DC_NATIVE': 'digital_currency',
        'DC_MICROPAY': 'digital_currency',
        'DC_APP': 'digital_currency',
        'BALANCE_PAY': 'balance'
    }
    
    # 支付模式映射 (基于用例编号)
    PAYMENT_MODE_MAP = {
        '1.': 'direct',      # 1.x 直清模式
        '2.': 'account',     # 2.x 账户模式
        '3.': 'guarantee',   # 3.x 担保支付
        '4.': 'split',       # 4.x 分账支付
        '5.': 'cloudpay',    # 5.x 云闪付
        '6.': 'exception',   # 6.x 异常场景
        '7.': 'performance'  # 7.x 性能测试
    }
    
    def __init__(self, markdown_file: str):
        """初始化解析器
        
        Args:
            markdown_file: Markdown文件路径
        """
        self.markdown_file = markdown_file
        self.test_cases: List[TestCase] = []
        self.raw_content = ""
        
    def parse(self) -> List[TestCase]:
        """解析测试用例
        
        Returns:
            测试用例列表
            
        Raises:
            ParseError: 解析失败
        """
        try:
            # 读取文件内容
            with open(self.markdown_file, 'r', encoding='utf-8') as f:
                self.raw_content = f.read()
            
            # 按用例分割内容
            case_blocks = self._split_test_cases()
            
            # 解析每个用例
            for block in case_blocks:
                test_case = self._parse_test_case_block(block)
                if test_case and self.validate(test_case):
                    self.test_cases.append(test_case)
            
            return self.test_cases
            
        except Exception as e:
            raise ParseError(f"解析测试用例失败: {str(e)}")
    
    def _split_test_cases(self) -> List[str]:
        """分割测试用例块
        
        Returns:
            测试用例块列表
        """
        # 使用正则表达式匹配用例标题 (#### 用例X.X.X:)
        pattern = r'####\s+用例\d+\.\d+\.\d+:'
        
        # 找到所有用例的起始位置
        matches = list(re.finditer(pattern, self.raw_content))
        
        if not matches:
            return []
        
        # 分割用例块
        blocks = []
        for i, match in enumerate(matches):
            start = match.start()
            # 下一个用例的起始位置,或文件末尾
            end = matches[i + 1].start() if i + 1 < len(matches) else len(self.raw_content)
            blocks.append(self.raw_content[start:end])
        
        return blocks
    
    def _parse_test_case_block(self, block: str) -> Optional[TestCase]:
        """解析单个测试用例块
        
        Args:
            block: 测试用例文本块
            
        Returns:
            TestCase对象或None
        """
        try:
            # 提取用例标题行
            title_match = re.search(r'####\s+用例([\d.]+):\s*(.+)', block)
            if not title_match:
                return None
            
            case_id = title_match.group(1).strip()
            case_name = title_match.group(2).strip()
            
            # 提取测试目标
            test_objective = self._extract_test_objective(block)
            
            # 提取前置条件
            preconditions = self._extract_preconditions(block)
            
            # 提取测试步骤
            test_steps = self._extract_test_steps(block)
            
            # 提取预期结果
            expected_results = self._extract_expected_results(block)
            
            # 推断支付方式
            payment_method = self._infer_payment_method(case_name, test_steps)
            
            # 推断支付模式
            payment_mode = self._infer_payment_mode(case_id, case_name)
            
            # 分配优先级
            priority = self._assign_priority(case_id, payment_method)
            
            # 创建测试用例对象
            test_case = TestCase(
                case_id=case_id,
                case_name=case_name,
                test_objective=test_objective,
                priority=priority,
                preconditions=preconditions,
                test_steps=test_steps,
                expected_results=expected_results,
                payment_method=payment_method,
                payment_mode=payment_mode
            )
            
            # 生成标签
            test_case.tags = self._generate_tags(test_case)
            
            return test_case
            
        except Exception as e:
            print(f"解析用例块失败: {str(e)}")
            return None
    
    def _extract_case_id(self, heading: str) -> str:
        """从标题提取用例编号
        
        Args:
            heading: 标题文本(如: "用例1.1.1: 微信小程序支付")
            
        Returns:
            用例编号(如: "1.1.1")
        """
        match = re.search(r'用例([\d.]+):', heading)
        return match.group(1) if match else ""
    
    def _extract_case_name(self, heading: str) -> str:
        """从标题提取用例名称
        
        Args:
            heading: 标题文本
            
        Returns:
            用例名称(如: "微信小程序支付-WECHAT_APPLET")
        """
        match = re.search(r':\s*(.+)', heading)
        return match.group(1).strip() if match else ""
    
    def _extract_test_objective(self, content: str) -> str:
        """提取测试目标
        
        Args:
            content: 用例内容
            
        Returns:
            测试目标描述
        """
        match = re.search(r'\*\*测试目标\*\*:\s*(.+)', content)
        return match.group(1).strip() if match else ""
    
    def _extract_preconditions(self, content: str) -> List[str]:
        """提取前置条件
        
        Args:
            content: 用例内容
            
        Returns:
            前置条件列表
        """
        preconditions = []
        
        # 查找前置条件部分
        match = re.search(r'\*\*前置条件\*\*:(.*?)(?=\*\*测试步骤\*\*|$)', content, re.DOTALL)
        if match:
            precond_text = match.group(1)
            # 提取列表项
            items = re.findall(r'-\s*(.+)', precond_text)
            preconditions = [item.strip() for item in items]
        
        return preconditions
    
    def _extract_test_steps(self, content: str) -> List[TestStep]:
        """提取测试步骤和参数
        
        Args:
            content: 用例内容
            
        Returns:
            测试步骤列表,包含提取的参数
        """
        test_steps = []
        
        # 查找测试步骤部分
        match = re.search(r'\*\*测试步骤\*\*:(.*?)(?=\*\*预期结果\*\*|$)', content, re.DOTALL)
        if not match:
            return test_steps
        
        steps_text = match.group(1)
        
        # 提取步骤 (1. 2. 3. 等)
        step_matches = re.finditer(r'(\d+)\.\s*(.+?)(?=\d+\.|$)', steps_text, re.DOTALL)
        
        for step_match in step_matches:
            step_no = int(step_match.group(1))
            step_desc = step_match.group(2).strip()
            
            # 提取参数
            parameters = self._extract_parameters(step_desc)
            
            test_steps.append(TestStep(
                step_no=step_no,
                description=step_desc,
                parameters=parameters
            ))
        
        return test_steps
    
    def _extract_parameters(self, step_text: str) -> Dict[str, Any]:
        """从步骤文本提取参数
        
        Args:
            step_text: 步骤文本
            
        Returns:
            参数字典(如: {"pay_type": "WECHAT_APPLET", "order_amount": "40"})
        """
        parameters = {}
        
        # 提取参数行 (- key: value 格式)
        param_matches = re.findall(r'-\s*(\w+):\s*(.+)', step_text)
        
        for key, value in param_matches:
            # 清理值
            value = value.strip()
            
            # 移除括号中的注释
            value = re.sub(r'\(.*?\)', '', value).strip()
            
            # 处理特殊标记
            if value.startswith('自动生成'):
                value = 'auto_generate'
            elif value.startswith('包含'):
                value = 'complex_object'
            
            parameters[key] = value
        
        return parameters
    
    def _extract_expected_results(self, content: str) -> List[ExpectedResult]:
        """提取预期结果和断言条件
        
        Args:
            content: 用例内容
            
        Returns:
            预期结果列表,包含断言条件
        """
        expected_results = []
        
        # 查找预期结果部分
        match = re.search(r'\*\*预期结果\*\*:(.*?)(?=---|####|$)', content, re.DOTALL)
        if not match:
            return expected_results
        
        results_text = match.group(1)
        
        # 提取列表项
        result_items = re.findall(r'-\s*(.+)', results_text)
        
        for item in result_items:
            item = item.strip()
            
            # 提取断言条件
            assertions = self._extract_assertions(item)
            
            # 提取响应时间阈值
            response_time_threshold = None
            time_match = re.search(r'响应时间[<＜](\d+)秒', item)
            if time_match:
                response_time_threshold = float(time_match.group(1)) * 1000  # 转换为毫秒
            
            expected_results.append(ExpectedResult(
                description=item,
                assertions=assertions,
                response_time_threshold=response_time_threshold
            ))
        
        return expected_results
    
    def _extract_assertions(self, result_text: str) -> List[str]:
        """从预期结果提取断言条件
        
        Args:
            result_text: 预期结果文本
            
        Returns:
            断言条件列表(如: ["return_code == '0000'", "pay_info is not None"])
        """
        assertions = []
        
        # 常见断言模式映射
        assertion_patterns = {
            r'接口返回成功': "response.is_success()",
            r'返回.*参数': "response.pay_info is not None",
            r'返回.*URL': "response.pay_info is not None",
            r'订单状态为待支付': "response.result_code == '0000'",
            r'可.*支付': "response.pay_info is not None",
            r'返回.*信息': "response.pay_info is not None"
        }
        
        for pattern, assertion in assertion_patterns.items():
            if re.search(pattern, result_text):
                if assertion not in assertions:
                    assertions.append(assertion)
        
        return assertions
    
    def _infer_payment_method(self, case_name: str, test_steps: List[TestStep]) -> str:
        """推断支付方式
        
        Args:
            case_name: 用例名称
            test_steps: 测试步骤列表
            
        Returns:
            支付方式(如: "WECHAT_APPLET")
        """
        # 从用例名称中提取支付方式
        for method_key in self.PAYMENT_METHODS.keys():
            if method_key in case_name:
                return method_key
        
        # 从测试步骤参数中提取
        for step in test_steps:
            if 'pay_type' in step.parameters:
                pay_type = step.parameters['pay_type']
                if pay_type in self.PAYMENT_METHODS:
                    return pay_type
        
        return "UNKNOWN"
    
    def _infer_payment_mode(self, case_id: str, case_name: str) -> str:
        """推断支付模式
        
        Args:
            case_id: 用例编号
            case_name: 用例名称
            
        Returns:
            支付模式(如: "direct", "account", "guarantee", "split")
        """
        # 基于用例编号推断
        for prefix, mode in self.PAYMENT_MODE_MAP.items():
            if case_id.startswith(prefix):
                return mode
        
        # 基于用例名称关键词推断
        if '账户' in case_name or 'account' in case_name.lower():
            return 'account'
        elif '担保' in case_name or 'guarantee' in case_name.lower():
            return 'guarantee'
        elif '分账' in case_name or 'split' in case_name.lower():
            return 'split'
        elif '云闪付' in case_name or 'cloudpay' in case_name.lower():
            return 'cloudpay'
        elif '异常' in case_name or 'exception' in case_name.lower():
            return 'exception'
        elif '性能' in case_name or 'performance' in case_name.lower():
            return 'performance'
        
        return 'direct'  # 默认直清模式
    
    def _assign_priority(self, case_id: str, payment_method: str) -> str:
        """分配优先级
        
        Args:
            case_id: 用例编号
            payment_method: 支付方式
            
        Returns:
            优先级(P0/P1/P2/P3)
        """
        # P0: 核心支付方式的基础用例 (1.1.x, 1.2.x)
        if case_id.startswith('1.1.') or case_id.startswith('1.2.'):
            if payment_method in ['WECHAT_APPLET', 'WECHAT_NATIVE', 'ALIPAY_NATIVE', 'ALIPAY_APP']:
                return 'P0'
            return 'P1'
        
        # P1: 账户模式和担保支付 (2.x, 3.x)
        if case_id.startswith('2.') or case_id.startswith('3.'):
            return 'P1'
        
        # P2: 分账支付和云闪付 (4.x, 5.x)
        if case_id.startswith('4.') or case_id.startswith('5.'):
            return 'P2'
        
        # P3: 异常场景和性能测试 (6.x, 7.x)
        if case_id.startswith('6.') or case_id.startswith('7.'):
            return 'P3'
        
        return 'P2'  # 默认P2
    
    def _generate_tags(self, test_case: TestCase) -> List[str]:
        """生成标签
        
        Args:
            test_case: 测试用例对象
            
        Returns:
            标签列表(如: ["wechat", "direct_mode", "P0"])
        """
        tags = []
        
        # 添加支付方式标签
        if test_case.payment_method and test_case.payment_method in self.PAYMENT_METHODS:
            payment_tag = self.PAYMENT_METHODS[test_case.payment_method]
            tags.append(payment_tag)
        
        # 添加支付模式标签
        if test_case.payment_mode:
            tags.append(f"{test_case.payment_mode}_mode")
        
        # 添加优先级标签
        tags.append(test_case.priority)
        
        return tags
    
    def validate(self, test_case: TestCase) -> bool:
        """验证测试用例完整性
        
        Args:
            test_case: 测试用例对象
            
        Returns:
            是否有效
        """
        # 必填字段检查
        if not test_case.case_id:
            return False
        if not test_case.case_name:
            return False
        if not test_case.test_objective:
            return False
        
        # 至少有一个测试步骤
        if not test_case.test_steps:
            return False
        
        # 至少有一个预期结果
        if not test_case.expected_results:
            return False
        
        return True
    
    def to_json(self) -> str:
        """转换为JSON格式
        
        Returns:
            JSON字符串
        """
        data = [self._test_case_to_dict(tc) for tc in self.test_cases]
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def to_yaml(self) -> str:
        """转换为YAML格式
        
        Returns:
            YAML字符串
        """
        data = [self._test_case_to_dict(tc) for tc in self.test_cases]
        return yaml.dump(data, allow_unicode=True, default_flow_style=False)
    
    def _test_case_to_dict(self, test_case: TestCase) -> Dict:
        """将TestCase对象转换为字典
        
        Args:
            test_case: TestCase对象
            
        Returns:
            字典表示
        """
        return {
            'case_id': test_case.case_id,
            'case_name': test_case.case_name,
            'test_objective': test_case.test_objective,
            'priority': test_case.priority,
            'preconditions': test_case.preconditions,
            'test_steps': [
                {
                    'step_no': step.step_no,
                    'description': step.description,
                    'parameters': step.parameters
                }
                for step in test_case.test_steps
            ],
            'expected_results': [
                {
                    'description': result.description,
                    'assertions': result.assertions,
                    'response_time_threshold': result.response_time_threshold
                }
                for result in test_case.expected_results
            ],
            'tags': test_case.tags,
            'payment_method': test_case.payment_method,
            'payment_mode': test_case.payment_mode
        }
    
    def save_parsed_data(self, output_path: str):
        """保存解析后的数据
        
        Args:
            output_path: 输出文件路径
        """
        import os
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 根据文件扩展名选择格式
        if output_path.endswith('.json'):
            content = self.to_json()
        elif output_path.endswith('.yaml') or output_path.endswith('.yml'):
            content = self.to_yaml()
        else:
            # 默认JSON格式
            content = self.to_json()
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)


class ParseError(Exception):
    """解析错误异常"""
    pass
