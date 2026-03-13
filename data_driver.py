"""
数据驱动引擎模块

支持从多种格式文件加载测试数据:
- CSV文件
- Excel文件
- JSON文件
- YAML文件
"""

import csv
import json
import yaml
from typing import List, Dict, Any
from pathlib import Path


class DataDriver:
    """数据驱动引擎类"""
    
    def __init__(self):
        """初始化数据驱动引擎"""
        pass
    
    def load_from_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """
        从CSV文件加载测试数据
        
        Args:
            file_path: CSV文件路径
            
        Returns:
            测试数据列表,每个元素是一个字典
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式错误
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        try:
            data = []
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 转换数据类型
                    converted_row = self._convert_types(row)
                    data.append(converted_row)
            return data
        except Exception as e:
            raise ValueError(f"Failed to load CSV file: {str(e)}")
    
    def load_from_excel(self, file_path: str, sheet_name: str = None) -> List[Dict[str, Any]]:
        """
        从Excel文件加载测试数据
        
        Args:
            file_path: Excel文件路径
            sheet_name: 工作表名称,默认为第一个工作表
            
        Returns:
            测试数据列表,每个元素是一个字典
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式错误
            ImportError: openpyxl库未安装
        """
        try:
            import openpyxl
        except ImportError:
            raise ImportError("openpyxl is required for Excel support. Install it with: pip install openpyxl")
        
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")
        
        try:
            workbook = openpyxl.load_workbook(file_path)
            if sheet_name:
                sheet = workbook[sheet_name]
            else:
                sheet = workbook.active
            
            # 获取表头
            headers = []
            for cell in sheet[1]:
                headers.append(cell.value)
            
            # 读取数据
            data = []
            for row in sheet.iter_rows(min_row=2, values_only=True):
                row_dict = {}
                for i, value in enumerate(row):
                    if i < len(headers):
                        row_dict[headers[i]] = value
                data.append(row_dict)
            
            workbook.close()
            return data
        except Exception as e:
            raise ValueError(f"Failed to load Excel file: {str(e)}")
    
    def load_from_json(self, file_path: str) -> List[Dict[str, Any]]:
        """
        从JSON文件加载测试数据
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            测试数据列表,每个元素是一个字典
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式错误
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 确保返回列表
            if isinstance(data, dict):
                # 如果是字典,尝试获取data字段
                if 'data' in data and isinstance(data['data'], list):
                    return data['data']
                # 否则包装成列表
                return [data]
            elif isinstance(data, list):
                return data
            else:
                raise ValueError("JSON data must be a list or dict")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to load JSON file: {str(e)}")
    
    def load_from_yaml(self, file_path: str) -> List[Dict[str, Any]]:
        """
        从YAML文件加载测试数据
        
        Args:
            file_path: YAML文件路径
            
        Returns:
            测试数据列表,每个元素是一个字典
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式错误
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"YAML file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # 确保返回列表
            if isinstance(data, dict):
                # 如果是字典,尝试获取data字段
                if 'data' in data and isinstance(data['data'], list):
                    return data['data']
                # 否则包装成列表
                return [data]
            elif isinstance(data, list):
                return data
            else:
                raise ValueError("YAML data must be a list or dict")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to load YAML file: {str(e)}")
    
    def load(self, file_path: str, **kwargs) -> List[Dict[str, Any]]:
        """
        自动识别文件格式并加载测试数据
        
        Args:
            file_path: 文件路径
            **kwargs: 额外参数(如Excel的sheet_name)
            
        Returns:
            测试数据列表
            
        Raises:
            ValueError: 不支持的文件格式
        """
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix == '.csv':
            return self.load_from_csv(file_path)
        elif suffix in ['.xlsx', '.xls']:
            return self.load_from_excel(file_path, **kwargs)
        elif suffix == '.json':
            return self.load_from_json(file_path)
        elif suffix in ['.yaml', '.yml']:
            return self.load_from_yaml(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
    
    def _convert_types(self, row: Dict[str, str]) -> Dict[str, Any]:
        """
        转换CSV数据类型(CSV默认都是字符串)
        
        Args:
            row: 原始行数据
            
        Returns:
            转换后的行数据
        """
        converted = {}
        for key, value in row.items():
            if value is None or value == '':
                converted[key] = None
            elif value.lower() == 'true':
                converted[key] = True
            elif value.lower() == 'false':
                converted[key] = False
            elif value.isdigit():
                converted[key] = int(value)
            else:
                try:
                    converted[key] = float(value)
                except ValueError:
                    converted[key] = value
        return converted
    
    def filter_data(self, data: List[Dict[str, Any]], **filters) -> List[Dict[str, Any]]:
        """
        过滤测试数据
        
        Args:
            data: 测试数据列表
            **filters: 过滤条件(字段名=值)
            
        Returns:
            过滤后的数据列表
        """
        if not filters:
            return data
        
        filtered = []
        for item in data:
            match = True
            for key, value in filters.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            if match:
                filtered.append(item)
        return filtered
    
    def get_parametrize_data(self, data: List[Dict[str, Any]]) -> tuple:
        """
        将数据转换为pytest参数化格式
        
        Args:
            data: 测试数据列表
            
        Returns:
            (参数名列表, 参数值列表)
        """
        if not data:
            return ([], [])
        
        # 获取所有字段名
        keys = list(data[0].keys())
        
        # 提取所有值
        values = []
        for item in data:
            row_values = tuple(item.get(key) for key in keys)
            values.append(row_values)
        
        return (keys, values)
