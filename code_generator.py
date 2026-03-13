"""
代码生成器模块

负责从解析后的测试用例生成可执行的pytest测试代码
使用Jinja2模板引擎生成代码
"""

from jinja2 import Environment, FileSystemLoader, Template
from typing import List, Dict, Any
import os
import json
from datetime import datetime
from pathlib import Path


class CodeGenerator:
    """代码生成器
    
    使用Jinja2模板生成可执行的pytest测试代码
    """
    
    def __init__(self, template_dir: str = "templates"):
        """初始化代码生成器
        
        Args:
            template_dir: 模板目录路径(相对于项目根目录)
        """
        # 获取项目根目录
        current_file = Path(__file__)
        project_root = current_file.parent.parent
        
        # 构建模板目录的绝对路径
        self.template_dir = project_root / template_dir
        
        if not self.template_dir.exists():
            raise FileNotFoundError(f"模板目录不存在: {self.template_dir}")
        
        # 初始化Jinja2环境
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 添加自定义过滤器
        self.env.filters['slugify'] = self._slugify
        
    def _slugify(self, text: str) -> str:
        """将文本转换为slug格式(用于函数名)
        
        Args:
            text: 原始文本
            
        Returns:
            slug格式的文本
        """
        # 替换特殊字符
        text = text.replace('-', '_').replace(' ', '_').replace('/', '_')
        text = text.replace('(', '').replace(')', '')
        text = text.replace('[', '').replace(']', '')
        text = text.replace('{', '').replace('}', '')
        text = text.replace('+', '_').replace('=', '_')
        text = text.replace('*', '_').replace('&', '_')
        text = text.replace('%', '_').replace('$', '_')
        text = text.replace('#', '_').replace('@', '_')
        text = text.replace('!', '_').replace('~', '_')
        text = text.replace('`', '_').replace('^', '_')
        text = text.replace('|', '_').replace('\\', '_')
        text = text.replace('<', '_').replace('>', '_')
        text = text.replace('?', '_').replace(':', '_')
        text = text.replace(';', '_').replace(',', '_')
        text = text.replace('"', '').replace("'", '')
        text = text.replace('.', '_')
        # 移除连续的下划线
        while '__' in text:
            text = text.replace('__', '_')
        # 转换为小写
        return text.lower()
    
    def generate_test_function(self, test_case: Dict[str, Any]) -> str:
        """生成pytest测试函数代码
        
        Args:
            test_case: 测试用例字典
            
        Returns:
            测试函数代码字符串
        """
        # 使用test_case模板生成单个测试函数
        template = self.env.get_template('test_case.py.j2')
        
        # 准备模板上下文
        context = {
            'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source_file': 'test_case',
            'test_cases': [test_case]
        }
        
        # 渲染模板
        code = template.render(context)
        
        # 提取单个测试函数(去掉导入部分)
        lines = code.split('\n')
        function_start = -1
        for i, line in enumerate(lines):
            if line.startswith('@pytest.mark'):
                function_start = i
                break
        
        if function_start >= 0:
            return '\n'.join(lines[function_start:])
        
        return code
    
    def generate_request_builder(self, test_case: Dict[str, Any]) -> str:
        """生成请求构建代码
        
        Args:
            test_case: 测试用例字典
            
        Returns:
            请求构建代码字符串
        """
        lines = []
        lines.append("# 构造请求参数")
        lines.append("request_params = {")
        lines.append('    "txn_seqno": data_generator.generate_txn_seqno(),')
        lines.append('    "txn_time": data_generator.generate_timestamp(),')
        lines.append('    "mch_id": config.get("merchant.mch_id", "M123456789"),')
        lines.append('    "notify_url": config.get("api.notify_url", "https://example.com/notify"),')
        
        # 添加测试步骤中的参数
        if test_case.get('test_steps') and len(test_case['test_steps']) > 0:
            parameters = test_case['test_steps'][0].get('parameters', {})
            for key, value in parameters.items():
                if isinstance(value, str):
                    lines.append(f'    "{key}": "{value}",')
                else:
                    lines.append(f'    "{key}": {value},')
        
        lines.append("}")
        lines.append("")
        lines.append("# 构造请求对象")
        lines.append("request_body = APIRequest(**request_params)")
        
        return '\n'.join(lines)
    
    def generate_assertions(self, expected_results: List[Dict[str, Any]]) -> str:
        """生成断言代码
        
        Args:
            expected_results: 预期结果列表
            
        Returns:
            断言代码字符串
        """
        lines = []
        lines.append("# 断言验证")
        
        for expected_result in expected_results:
            assertions = expected_result.get('assertions', [])
            for assertion in assertions:
                # 转换断言字符串为Python代码
                assertion_code = self._convert_assertion(assertion)
                lines.append(f'assert {assertion_code}, "断言失败: {assertion}"')
            
            # 添加响应时间断言
            if expected_result.get('response_time_threshold'):
                threshold = expected_result['response_time_threshold']
                lines.append(f'assert response_time < {threshold}, f"响应时间超过阈值: {{response_time}}ms > {threshold}ms"')
        
        return '\n'.join(lines)
    
    def _convert_assertion(self, assertion: str) -> str:
        """转换断言字符串为Python代码
        
        Args:
            assertion: 断言字符串(如: "return_code == '0000'")
            
        Returns:
            Python断言代码
        """
        # 如果断言中包含response.,直接返回
        if 'response.' in assertion:
            return assertion
        
        # 否则添加response.前缀
        # 处理常见的断言模式
        if 'is_success()' in assertion:
            return 'response.is_success()'
        elif 'is not None' in assertion:
            field = assertion.split(' is not None')[0].strip()
            return f'response.{field} is not None'
        elif 'is None' in assertion:
            field = assertion.split(' is None')[0].strip()
            return f'response.{field} is None'
        elif '==' in assertion or '!=' in assertion or '>' in assertion or '<' in assertion:
            # 如果是比较表达式,添加response.前缀
            parts = assertion.split()
            if len(parts) >= 3 and not parts[0].startswith('response.'):
                parts[0] = f'response.{parts[0]}'
                return ' '.join(parts)
        
        return assertion
    
    def generate_test_file(self, test_cases: List[Dict[str, Any]], output_path: str):
        """生成测试文件
        
        Args:
            test_cases: 测试用例列表
            output_path: 输出文件路径
        """
        # 加载模板
        template = self.env.get_template('test_case.py.j2')
        
        # 准备模板上下文
        context = {
            'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source_file': '统一创单接口createpay测试用例.md',
            'test_cases': test_cases
        }
        
        # 渲染模板
        code = template.render(context)
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        print(f"✓ 生成测试文件: {output_path}")
        print(f"  包含 {len(test_cases)} 个测试用例")
    
    def generate_test_data_file(self, test_cases: List[Dict[str, Any]], output_path: str):
        """生成测试数据文件
        
        Args:
            test_cases: 测试用例列表
            output_path: 输出文件路径
        """
        # 加载模板
        template = self.env.get_template('test_data.py.j2')
        
        # 准备模板上下文
        context = {
            'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source_file': '统一创单接口createpay测试用例.md',
            'test_cases': test_cases
        }
        
        # 渲染模板
        code = template.render(context)
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        print(f"✓ 生成测试数据文件: {output_path}")
        print(f"  包含 {len(test_cases)} 个测试用例数据")
    
    def generate_api_object_file(self, api_name: str, output_path: str,
                                 request_fields: List[Dict] = None,
                                 response_fields: List[Dict] = None):
        """生成接口对象定义文件
        
        Args:
            api_name: 接口名称
            output_path: 输出文件路径
            request_fields: 请求字段列表
            response_fields: 响应字段列表
        """
        # 加载模板
        template = self.env.get_template('api_object.py.j2')
        
        # 准备请求类定义
        request_class = None
        if request_fields:
            request_class = {
                'name': f'{api_name}Request',
                'description': f'{api_name}请求对象',
                'fields': request_fields
            }
        
        # 准备响应类定义
        response_class = None
        if response_fields:
            has_return_code = any(f['name'] == 'return_code' for f in response_fields)
            response_class = {
                'name': f'{api_name}Response',
                'description': f'{api_name}响应对象',
                'fields': response_fields,
                'has_return_code': has_return_code
            }
        
        # 准备模板上下文
        context = {
            'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'request_class': request_class,
            'response_class': response_class
        }
        
        # 渲染模板
        code = template.render(context)
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        print(f"✓ 生成API对象文件: {output_path}")
    
    def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """渲染模板
        
        Args:
            template_name: 模板名称
            context: 模板上下文
            
        Returns:
            渲染后的代码字符串
        """
        template = self.env.get_template(template_name)
        return template.render(context)


# 便捷函数
def load_test_cases_from_json(json_path: str) -> List[Dict[str, Any]]:
    """从JSON文件加载测试用例
    
    Args:
        json_path: JSON文件路径
        
    Returns:
        测试用例列表
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 如果是字典且包含test_cases键,提取test_cases
    if isinstance(data, dict) and 'test_cases' in data:
        return data['test_cases']
    
    # 否则假设整个文件就是测试用例列表
    return data if isinstance(data, list) else [data]


def filter_test_cases_by_mode(test_cases: List[Dict[str, Any]], 
                              payment_mode: str) -> List[Dict[str, Any]]:
    """按支付模式过滤测试用例
    
    Args:
        test_cases: 测试用例列表
        payment_mode: 支付模式(direct/account/guarantee/split)
        
    Returns:
        过滤后的测试用例列表
    """
    return [tc for tc in test_cases if tc.get('payment_mode') == payment_mode]


def filter_test_cases_by_priority(test_cases: List[Dict[str, Any]], 
                                  priority: str) -> List[Dict[str, Any]]:
    """按优先级过滤测试用例
    
    Args:
        test_cases: 测试用例列表
        priority: 优先级(P0/P1/P2/P3)
        
    Returns:
        过滤后的测试用例列表
    """
    return [tc for tc in test_cases if tc.get('priority') == priority]
