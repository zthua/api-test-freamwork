"""
断言引擎模块

提供丰富的断言方法用于验证测试结果,包括:
- 响应状态码断言
- 响应字段存在性断言
- 响应字段值相等断言
- 响应字段值包含断言
- 响应时间断言
- JSON Schema断言
- 自定义断言函数
"""

import json
from typing import Any, Dict, Optional, Callable
from jsonschema import validate, ValidationError


class AssertionError(Exception):
    """断言失败异常"""
    pass


class AssertionEngine:
    """断言引擎类"""
    
    def __init__(self, soft_assert: bool = False):
        """
        初始化断言引擎
        
        Args:
            soft_assert: 是否启用软断言(失败后继续执行)
        """
        self.soft_assert = soft_assert
        self.failures = []
    
    def assert_status_code(self, actual: int, expected: int, message: str = ""):
        """
        断言响应状态码
        
        Args:
            actual: 实际状态码
            expected: 期望状态码
            message: 自定义错误信息
        """
        if actual != expected:
            error_msg = f"Status code assertion failed: expected {expected}, but got {actual}"
            if message:
                error_msg = f"{message}: {error_msg}"
            self._handle_failure(error_msg)
    
    def assert_field_exists(self, data: Dict[str, Any], field_path: str, message: str = ""):
        """
        断言字段存在
        
        Args:
            data: 响应数据字典
            field_path: 字段路径,支持点号分隔的嵌套路径(如"data.order_id")
            message: 自定义错误信息
        """
        try:
            self._get_nested_value(data, field_path)
        except (KeyError, TypeError):
            error_msg = f"Field existence assertion failed: field '{field_path}' does not exist"
            if message:
                error_msg = f"{message}: {error_msg}"
            self._handle_failure(error_msg)
    
    def assert_field_equals(self, data: Dict[str, Any], field_path: str, expected: Any, message: str = ""):
        """
        断言字段值相等
        
        Args:
            data: 响应数据字典
            field_path: 字段路径,支持点号分隔的嵌套路径
            expected: 期望值
            message: 自定义错误信息
        """
        try:
            actual = self._get_nested_value(data, field_path)
            if actual != expected:
                error_msg = f"Field equality assertion failed for '{field_path}': expected {expected}, but got {actual}"
                if message:
                    error_msg = f"{message}: {error_msg}"
                self._handle_failure(error_msg)
        except (KeyError, TypeError) as e:
            error_msg = f"Field equality assertion failed: field '{field_path}' does not exist"
            if message:
                error_msg = f"{message}: {error_msg}"
            self._handle_failure(error_msg)
    
    def assert_field_contains(self, data: Dict[str, Any], field_path: str, expected: Any, message: str = ""):
        """
        断言字段值包含
        
        Args:
            data: 响应数据字典
            field_path: 字段路径,支持点号分隔的嵌套路径
            expected: 期望包含的值
            message: 自定义错误信息
        """
        try:
            actual = self._get_nested_value(data, field_path)
            if isinstance(actual, str):
                if expected not in actual:
                    error_msg = f"Field contains assertion failed for '{field_path}': expected to contain '{expected}', but got '{actual}'"
                    if message:
                        error_msg = f"{message}: {error_msg}"
                    self._handle_failure(error_msg)
            elif isinstance(actual, (list, tuple)):
                if expected not in actual:
                    error_msg = f"Field contains assertion failed for '{field_path}': expected to contain {expected}, but got {actual}"
                    if message:
                        error_msg = f"{message}: {error_msg}"
                    self._handle_failure(error_msg)
            else:
                error_msg = f"Field contains assertion failed: field '{field_path}' is not a string or list"
                if message:
                    error_msg = f"{message}: {error_msg}"
                self._handle_failure(error_msg)
        except (KeyError, TypeError):
            error_msg = f"Field contains assertion failed: field '{field_path}' does not exist"
            if message:
                error_msg = f"{message}: {error_msg}"
            self._handle_failure(error_msg)
    
    def assert_response_time(self, actual: float, max_time: float, message: str = ""):
        """
        断言响应时间
        
        Args:
            actual: 实际响应时间(秒)
            max_time: 最大允许响应时间(秒)
            message: 自定义错误信息
        """
        if actual > max_time:
            error_msg = f"Response time assertion failed: expected <= {max_time}s, but got {actual}s"
            if message:
                error_msg = f"{message}: {error_msg}"
            self._handle_failure(error_msg)
    
    def assert_json_schema(self, data: Dict[str, Any], schema: Dict[str, Any], message: str = ""):
        """
        断言JSON Schema
        
        Args:
            data: 响应数据字典
            schema: JSON Schema定义
            message: 自定义错误信息
        """
        try:
            validate(instance=data, schema=schema)
        except ValidationError as e:
            error_msg = f"JSON Schema assertion failed: {str(e)}"
            if message:
                error_msg = f"{message}: {error_msg}"
            self._handle_failure(error_msg)
    
    def assert_custom(self, condition: bool, message: str = "Custom assertion failed"):
        """
        自定义断言
        
        Args:
            condition: 断言条件
            message: 自定义错误信息
        """
        if not condition:
            self._handle_failure(message)
    
    def assert_with_function(self, func: Callable, *args, **kwargs):
        """
        使用自定义函数进行断言
        
        Args:
            func: 断言函数,返回True表示通过,False表示失败
            *args: 函数位置参数
            **kwargs: 函数关键字参数
        """
        try:
            result = func(*args, **kwargs)
            if not result:
                error_msg = f"Custom function assertion failed: {func.__name__}"
                self._handle_failure(error_msg)
        except Exception as e:
            error_msg = f"Custom function assertion error: {str(e)}"
            self._handle_failure(error_msg)
    
    def get_failures(self):
        """
        获取所有失败的断言信息(软断言模式)
        
        Returns:
            失败信息列表
        """
        return self.failures
    
    def has_failures(self):
        """
        检查是否有失败的断言(软断言模式)
        
        Returns:
            是否有失败
        """
        return len(self.failures) > 0
    
    def clear_failures(self):
        """清空失败记录"""
        self.failures = []
    
    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """
        获取嵌套字段的值
        
        Args:
            data: 数据字典
            field_path: 字段路径,支持点号分隔
            
        Returns:
            字段值
            
        Raises:
            KeyError: 字段不存在
            TypeError: 数据类型错误
        """
        keys = field_path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value[key]
            else:
                raise TypeError(f"Cannot access key '{key}' on non-dict type")
        return value
    
    def _handle_failure(self, error_msg: str):
        """
        处理断言失败
        
        Args:
            error_msg: 错误信息
        """
        if self.soft_assert:
            self.failures.append(error_msg)
        else:
            raise AssertionError(error_msg)
