"""
测试用例转换流程编排器

负责编排完整的测试用例转换流程:
1. 解析Markdown测试用例文档
2. 构建接口对象
3. 生成可执行的pytest测试代码
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import yaml
from datetime import datetime

from .test_parser import TestCaseParser, TestCase
from .code_generator import CodeGenerator
from .logger import Logger


class ConversionWorkflow:
    """测试用例转换流程编排器"""
    
    def __init__(
        self,
        template_dir: str = "templates",
        output_dir: str = "testcases/generated",
        logger: Optional[Logger] = None
    ):
        """初始化转换流程编排器
        
        Args:
            template_dir: 模板目录路径
            output_dir: 输出目录路径
            logger: 日志记录器实例
        """
        self.code_generator = CodeGenerator(template_dir=template_dir)
        self.output_dir = Path(output_dir)
        self.logger = logger or Logger(name="ConversionWorkflow")
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def parse_test_cases(self, markdown_file: str) -> List[TestCase]:
        """解析Markdown测试用例文档
        
        Args:
            markdown_file: Markdown文件路径
            
        Returns:
            解析后的测试用例列表
        """
        self.logger.info(f"开始解析测试用例文档: {markdown_file}")
        
        try:
            # 创建解析器实例
            parser = TestCaseParser(markdown_file)
            
            # 解析测试用例
            test_cases = parser.parse()
            
            self.logger.info(f"成功解析 {len(test_cases)} 个测试用例")
            return test_cases
            
        except Exception as e:
            self.logger.error(f"解析测试用例失败: {str(e)}")
            raise
    
    def build_api_objects(self, test_cases: List[TestCase]) -> Dict[str, Any]:
        """构建接口对象定义
        
        Args:
            test_cases: 测试用例列表
            
        Returns:
            接口对象定义字典
        """
        self.logger.info("开始构建接口对象定义")
        
        # 提取所有唯一的支付方式和支付模式
        payment_methods = set()
        payment_modes = set()
        
        for test_case in test_cases:
            if test_case.payment_method:
                payment_methods.add(test_case.payment_method)
            if test_case.payment_mode:
                payment_modes.add(test_case.payment_mode)
        
        api_objects = {
            'payment_methods': list(payment_methods),
            'payment_modes': list(payment_modes),
            'request_fields': self._extract_request_fields(test_cases),
            'response_fields': self._extract_response_fields(test_cases)
        }
        
        self.logger.info(f"接口对象定义构建完成: {len(payment_methods)} 种支付方式, {len(payment_modes)} 种支付模式")
        return api_objects
    
    def _extract_request_fields(self, test_cases: List[TestCase]) -> List[str]:
        """从测试用例中提取请求字段
        
        Args:
            test_cases: 测试用例列表
            
        Returns:
            请求字段列表
        """
        fields = set()
        
        for test_case in test_cases:
            for step in test_case.test_steps:
                fields.update(step.parameters.keys())
        
        return sorted(list(fields))
    
    def _extract_response_fields(self, test_cases: List[TestCase]) -> List[str]:
        """从测试用例中提取响应字段
        
        Args:
            test_cases: 测试用例列表
            
        Returns:
            响应字段列表
        """
        fields = set(['status_code', 'resp_code', 'resp_msg', 'txn_seqno'])
        
        for test_case in test_cases:
            for expected_result in test_case.expected_results:
                for assertion in expected_result.assertions:
                    # 从断言中提取字段名
                    # 例如: "resp_code == '0000'" -> "resp_code"
                    if '==' in assertion or 'in' in assertion:
                        field_match = assertion.split()[0]
                        fields.add(field_match)
        
        return sorted(list(fields))
    
    def generate_test_code(
        self,
        test_cases: List[TestCase],
        group_by: str = "payment_mode"
    ) -> Dict[str, str]:
        """生成测试代码
        
        Args:
            test_cases: 测试用例列表
            group_by: 分组方式 ("payment_mode" 或 "payment_method")
            
        Returns:
            文件名到代码内容的映射
        """
        self.logger.info(f"开始生成测试代码, 分组方式: {group_by}")
        
        # 按指定方式分组测试用例
        grouped_cases = self._group_test_cases(test_cases, group_by)
        
        generated_files = {}
        
        for group_name, cases in grouped_cases.items():
            self.logger.info(f"生成 {group_name} 组测试代码, 包含 {len(cases)} 个用例")
            
            # 转换为字典格式
            cases_dict = self._convert_to_dict(cases)
            
            # 生成测试文件
            file_name = f"test_{group_name}_gen.py"
            output_path = self.output_dir / file_name
            
            # 使用CodeGenerator生成文件
            self.code_generator.generate_test_file(
                test_cases=cases_dict,
                output_path=str(output_path)
            )
            
            # 读取生成的文件内容
            with open(output_path, 'r', encoding='utf-8') as f:
                code_content = f.read()
            
            generated_files[file_name] = code_content
        
        self.logger.info(f"测试代码生成完成, 共生成 {len(generated_files)} 个文件")
        return generated_files
    
    def _convert_to_dict(self, test_cases: List[TestCase]) -> List[Dict[str, Any]]:
        """将TestCase对象列表转换为字典列表
        
        Args:
            test_cases: TestCase对象列表
            
        Returns:
            字典列表
        """
        result = []
        for tc in test_cases:
            tc_dict = {
                'case_id': tc.case_id,
                'case_name': tc.case_name,
                'test_objective': tc.test_objective,
                'priority': tc.priority,
                'preconditions': tc.preconditions,
                'test_steps': [
                    {
                        'step_no': step.step_no,
                        'description': step.description,
                        'parameters': step.parameters
                    }
                    for step in tc.test_steps
                ],
                'expected_results': [
                    {
                        'description': result.description,
                        'assertions': result.assertions,
                        'response_time_threshold': result.response_time_threshold
                    }
                    for result in tc.expected_results
                ],
                'tags': tc.tags,
                'payment_method': tc.payment_method,
                'payment_mode': tc.payment_mode
            }
            result.append(tc_dict)
        return result
    
    def _group_test_cases(
        self,
        test_cases: List[TestCase],
        group_by: str
    ) -> Dict[str, List[TestCase]]:
        """按指定方式分组测试用例
        
        Args:
            test_cases: 测试用例列表
            group_by: 分组方式
            
        Returns:
            分组后的测试用例字典
        """
        grouped = {}
        
        for test_case in test_cases:
            if group_by == "payment_mode":
                group_key = test_case.payment_mode or "unknown"
            elif group_by == "payment_method":
                group_key = test_case.payment_method or "unknown"
            else:
                group_key = "all"
            
            if group_key not in grouped:
                grouped[group_key] = []
            
            grouped[group_key].append(test_case)
        
        return grouped
    
    def save_generated_files(self, generated_files: Dict[str, str]) -> List[str]:
        """保存生成的文件(文件已经在generate_test_code中保存,这里只返回路径列表)
        
        Args:
            generated_files: 文件名到代码内容的映射
            
        Returns:
            保存的文件路径列表
        """
        self.logger.info(f"生成的文件已保存到: {self.output_dir}")
        
        saved_files = []
        for file_name in generated_files.keys():
            file_path = self.output_dir / file_name
            saved_files.append(str(file_path))
            self.logger.info(f"文件: {file_path}")
        
        self.logger.info(f"共 {len(saved_files)} 个文件")
        return saved_files
    
    def save_parsed_data(
        self,
        test_cases: List[TestCase],
        output_format: str = "json"
    ) -> str:
        """保存解析后的测试用例数据
        
        Args:
            test_cases: 测试用例列表
            output_format: 输出格式 ("json" 或 "yaml")
            
        Returns:
            保存的文件路径
        """
        self.logger.info(f"保存解析数据, 格式: {output_format}")
        
        # 转换为字典列表
        data = []
        for tc in test_cases:
            tc_dict = {
                'case_id': tc.case_id,
                'case_name': tc.case_name,
                'test_objective': tc.test_objective,
                'priority': tc.priority,
                'preconditions': tc.preconditions,
                'test_steps': [
                    {
                        'step_no': step.step_no,
                        'description': step.description,
                        'parameters': step.parameters
                    }
                    for step in tc.test_steps
                ],
                'expected_results': [
                    {
                        'description': result.description,
                        'assertions': result.assertions,
                        'response_time_threshold': result.response_time_threshold
                    }
                    for result in tc.expected_results
                ],
                'tags': tc.tags,
                'payment_method': tc.payment_method,
                'payment_mode': tc.payment_mode
            }
            data.append(tc_dict)
        
        # 确定输出文件路径
        parsed_dir = Path("testdata/parsed")
        parsed_dir.mkdir(parents=True, exist_ok=True)
        
        if output_format == "json":
            output_file = parsed_dir / "test_cases.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        elif output_format == "yaml":
            output_file = parsed_dir / "test_cases.yaml"
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        else:
            raise ValueError(f"不支持的输出格式: {output_format}")
        
        self.logger.info(f"解析数据保存成功: {output_file}")
        return str(output_file)
    
    def run_full_conversion(
        self,
        markdown_file: str,
        group_by: str = "payment_mode",
        save_parsed: bool = True
    ) -> Dict[str, Any]:
        """执行完整的转换流程
        
        Args:
            markdown_file: Markdown测试用例文件路径
            group_by: 测试用例分组方式
            save_parsed: 是否保存解析后的数据
            
        Returns:
            转换结果字典,包含生成的文件列表和统计信息
        """
        self.logger.info("=" * 60)
        self.logger.info("开始执行完整测试用例转换流程")
        self.logger.info("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # 步骤1: 解析测试用例
            test_cases = self.parse_test_cases(markdown_file)
            
            # 步骤2: 构建接口对象
            api_objects = self.build_api_objects(test_cases)
            
            # 步骤3: 生成测试代码
            generated_files = self.generate_test_code(test_cases, group_by=group_by)
            
            # 步骤4: 保存生成的文件
            saved_files = self.save_generated_files(generated_files)
            
            # 步骤5: 保存解析数据(可选)
            parsed_file = None
            if save_parsed:
                parsed_file = self.save_parsed_data(test_cases, output_format="json")
            
            # 计算耗时
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            # 构建结果
            result = {
                'success': True,
                'test_cases_count': len(test_cases),
                'generated_files': saved_files,
                'parsed_data_file': parsed_file,
                'api_objects': api_objects,
                'elapsed_time': elapsed_time,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info("=" * 60)
            self.logger.info("测试用例转换流程执行成功")
            self.logger.info(f"- 解析用例数: {len(test_cases)}")
            self.logger.info(f"- 生成文件数: {len(saved_files)}")
            self.logger.info(f"- 耗时: {elapsed_time:.2f}秒")
            self.logger.info("=" * 60)
            
            return result
            
        except Exception as e:
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.error("=" * 60)
            self.logger.error(f"测试用例转换流程执行失败: {str(e)}")
            self.logger.error(f"耗时: {elapsed_time:.2f}秒")
            self.logger.error("=" * 60)
            
            return {
                'success': False,
                'error': str(e),
                'elapsed_time': elapsed_time,
                'timestamp': datetime.now().isoformat()
            }
