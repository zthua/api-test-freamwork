"""
接口对象数据模型
使用attrs库进行声明式接口定义,提供完整的类型提示和参数验证
"""

from attrs import define, field, validators
from typing import Optional, List, Dict, Any
from datetime import datetime
import attr


@define(kw_only=True)
class WeChatData:
    """微信支付扩展数据"""
    openid: str = field(validator=validators.instance_of(str))
    appid: str = field(validator=validators.instance_of(str))
    wx_sub_mchid: Optional[str] = field(default=None)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return attr.asdict(self, filter=lambda attr, value: value is not None)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WeChatData':
        """从字典创建对象"""
        return cls(**{k: v for k, v in data.items() if k in attr.fields_dict(cls)})


@define(kw_only=True)
class AlipayData:
    """支付宝扩展数据"""
    openid: str = field(validator=validators.instance_of(str))
    ali_sub_mchid: str = field(validator=validators.instance_of(str))
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return attr.asdict(self, filter=lambda attr, value: value is not None)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AlipayData':
        """从字典创建对象"""
        return cls(**{k: v for k, v in data.items() if k in attr.fields_dict(cls)})


@define(kw_only=True)
class PayeeInfo:
    """收款方信息"""
    payee_uid: str = field(validator=validators.instance_of(str))
    payee_accttype: str = field(validator=validators.in_(["MCHOWN", "USEROWN", "MCHASSUREMCH"]))
    payee_type: str = field(validator=validators.in_(["MCH", "USER"]))
    payee_amount: str = field(validator=validators.instance_of(str))
    
    @payee_amount.validator
    def _validate_amount(self, attribute, value):
        """验证金额格式"""
        try:
            amount = float(value)
            if amount <= 0:
                raise ValueError("金额必须大于0")
        except ValueError as e:
            if "金额必须大于0" in str(e):
                raise
            raise ValueError(f"金额格式错误: {value}")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return attr.asdict(self, filter=lambda attr, value: value is not None)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PayeeInfo':
        """从字典创建对象"""
        return cls(**{k: v for k, v in data.items() if k in attr.fields_dict(cls)})


@define(kw_only=True)
class APIRequest:
    """创单请求对象"""
    
    # 必填参数
    txn_seqno: str = field(validator=validators.instance_of(str))
    txn_time: str = field(validator=validators.instance_of(str))
    mch_id: str = field(validator=validators.instance_of(str))
    total_amount: str = field(validator=validators.instance_of(str))
    pay_type: str = field(validator=validators.instance_of(str))
    notify_url: str = field(validator=validators.instance_of(str))
    
    # 可选参数
    sub_mchid: Optional[str] = field(default=None)
    user_id: Optional[str] = field(default=None)
    busi_type: Optional[str] = field(default="100001")
    order_info: Optional[str] = field(default=None)
    secured_flag: Optional[bool] = field(default=False)
    share_flag: Optional[str] = field(default=None)
    
    # 扩展信息
    extend_info: Optional[Dict[str, Any]] = field(default=None)
    payee_infos: Optional[List[PayeeInfo]] = field(default=None)
    
    # 签名
    sign: Optional[str] = field(default=None)
    
    @total_amount.validator
    def _validate_total_amount(self, attribute, value):
        """验证总金额格式"""
        try:
            amount = float(value)
            if amount <= 0:
                raise ValueError("总金额必须大于0")
        except ValueError as e:
            if "总金额必须大于0" in str(e):
                raise
            raise ValueError(f"总金额格式错误: {value}")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        for field_obj in attr.fields(self.__class__):
            value = getattr(self, field_obj.name)
            if value is not None:
                # 处理嵌套对象
                if field_obj.name == 'payee_infos' and isinstance(value, list):
                    result[field_obj.name] = [
                        payee.to_dict() if hasattr(payee, 'to_dict') else payee 
                        for payee in value
                    ]
                elif field_obj.name == 'extend_info' and isinstance(value, dict):
                    # 处理extend_info中的嵌套对象
                    extend_dict = {}
                    for k, v in value.items():
                        if hasattr(v, 'to_dict'):
                            extend_dict[k] = v.to_dict()
                        else:
                            extend_dict[k] = v
                    result[field_obj.name] = extend_dict
                else:
                    result[field_obj.name] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'APIRequest':
        """从字典创建对象"""
        # 处理payee_infos
        if 'payee_infos' in data and isinstance(data['payee_infos'], list):
            data['payee_infos'] = [
                PayeeInfo.from_dict(payee) if isinstance(payee, dict) else payee
                for payee in data['payee_infos']
            ]
        return cls(**{k: v for k, v in data.items() if k in attr.fields_dict(cls)})


@define(kw_only=True)
class APIResponse:
    """创单响应对象"""
    return_code: str = field()
    return_msg: str = field()
    result_code: Optional[str] = field(default=None)
    err_code: Optional[str] = field(default=None)
    err_msg: Optional[str] = field(default=None)
    txn_seqno: Optional[str] = field(default=None)
    order_id: Optional[str] = field(default=None)
    pay_info: Optional[str] = field(default=None)
    sign: Optional[str] = field(default=None)
    
    def is_success(self) -> bool:
        """判断是否成功"""
        return self.return_code == "0000"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return attr.asdict(self, filter=lambda attr, value: value is not None)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'APIResponse':
        """从字典创建对象"""
        return cls(**{k: v for k, v in data.items() if k in attr.fields_dict(cls)})



class APIObjectBuilder:
    """接口对象构建器"""
    
    def __init__(self):
        """初始化构建器"""
        self.request_class = APIRequest
        self.response_class = APIResponse
    
    def build_request(self, parameters: Dict[str, Any]) -> APIRequest:
        """构建请求对象
        
        Args:
            parameters: 参数字典
            
        Returns:
            请求对象
            
        Raises:
            ValueError: 参数验证失败
            TypeError: 参数类型错误
        """
        try:
            # 处理payee_infos - 如果是字典列表,转换为PayeeInfo对象列表
            if 'payee_infos' in parameters and isinstance(parameters['payee_infos'], list):
                payee_infos = []
                for payee in parameters['payee_infos']:
                    if isinstance(payee, dict):
                        payee_infos.append(PayeeInfo(**payee))
                    elif isinstance(payee, PayeeInfo):
                        payee_infos.append(payee)
                    else:
                        raise ValueError(f"Invalid payee_info type: {type(payee)}")
                parameters['payee_infos'] = payee_infos
            
            # 处理extend_info中的嵌套对象
            if 'extend_info' in parameters and isinstance(parameters['extend_info'], dict):
                extend_info = {}
                for key, value in parameters['extend_info'].items():
                    if key == 'wx_data' and isinstance(value, dict):
                        extend_info[key] = WeChatData(**value)
                    elif key == 'ali_data' and isinstance(value, dict):
                        extend_info[key] = AlipayData(**value)
                    else:
                        extend_info[key] = value
                parameters['extend_info'] = extend_info
            
            # 创建请求对象
            return self.request_class(**parameters)
        except TypeError as e:
            raise TypeError(f"参数类型错误: {str(e)}")
        except ValueError as e:
            raise ValueError(f"参数验证失败: {str(e)}")
    
    def build_response(self, response_data: Dict[str, Any]) -> APIResponse:
        """构建响应对象
        
        Args:
            response_data: 响应数据
            
        Returns:
            响应对象
            
        Raises:
            ValueError: 响应数据验证失败
            TypeError: 响应数据类型错误
        """
        try:
            return self.response_class.from_dict(response_data)
        except TypeError as e:
            raise TypeError(f"响应数据类型错误: {str(e)}")
        except ValueError as e:
            raise ValueError(f"响应数据验证失败: {str(e)}")

    
    def generate_request_class_code(self, class_name: str, fields: List[Dict[str, Any]]) -> str:
        """生成请求类代码
        
        Args:
            class_name: 类名
            fields: 字段列表,每个字段包含name, type, required, default, validator等信息
            
        Returns:
            Python类代码字符串
        """
        code_lines = [
            f'@define(kw_only=True)',
            f'class {class_name}:',
            f'    """自动生成的请求类"""',
            ''
        ]
        
        # 生成必填字段
        required_fields = [f for f in fields if f.get('required', False)]
        if required_fields:
            code_lines.append('    # 必填参数')
            for field_info in required_fields:
                field_name = field_info['name']
                field_type = field_info.get('type', 'str')
                validator = field_info.get('validator', '')
                
                if validator:
                    code_lines.append(f'    {field_name}: {field_type} = field(validator={validator})')
                else:
                    code_lines.append(f'    {field_name}: {field_type} = field()')
            code_lines.append('')
        
        # 生成可选字段
        optional_fields = [f for f in fields if not f.get('required', False)]
        if optional_fields:
            code_lines.append('    # 可选参数')
            for field_info in optional_fields:
                field_name = field_info['name']
                field_type = field_info.get('type', 'str')
                default = field_info.get('default', 'None')
                validator = field_info.get('validator', '')
                
                if validator:
                    code_lines.append(f'    {field_name}: Optional[{field_type}] = field(default={default}, validator={validator})')
                else:
                    code_lines.append(f'    {field_name}: Optional[{field_type}] = field(default={default})')
            code_lines.append('')
        
        # 添加to_dict方法
        code_lines.extend([
            '    def to_dict(self) -> Dict[str, Any]:',
            '        """转换为字典"""',
            '        return attr.asdict(self, filter=lambda attr, value: value is not None)',
            '',
            '    @classmethod',
            '    def from_dict(cls, data: Dict[str, Any]) -> \'{}\':'.format(class_name),
            '        """从字典创建对象"""',
            '        return cls(**{k: v for k, v in data.items() if k in attr.fields_dict(cls)})',
        ])
        
        return '\n'.join(code_lines)
    
    def generate_response_class_code(self, class_name: str, fields: List[Dict[str, Any]]) -> str:
        """生成响应类代码
        
        Args:
            class_name: 类名
            fields: 字段列表,每个字段包含name, type, required, default等信息
            
        Returns:
            Python类代码字符串
        """
        code_lines = [
            f'@define(kw_only=True)',
            f'class {class_name}:',
            f'    """自动生成的响应类"""',
            ''
        ]
        
        # 生成必填字段
        required_fields = [f for f in fields if f.get('required', False)]
        if required_fields:
            for field_info in required_fields:
                field_name = field_info['name']
                field_type = field_info.get('type', 'str')
                code_lines.append(f'    {field_name}: {field_type} = field()')
            code_lines.append('')
        
        # 生成可选字段
        optional_fields = [f for f in fields if not f.get('required', False)]
        if optional_fields:
            for field_info in optional_fields:
                field_name = field_info['name']
                field_type = field_info.get('type', 'str')
                default = field_info.get('default', 'None')
                code_lines.append(f'    {field_name}: Optional[{field_type}] = field(default={default})')
            code_lines.append('')
        
        # 添加is_success方法(如果有return_code字段)
        if any(f['name'] == 'return_code' for f in fields):
            code_lines.extend([
                '    def is_success(self) -> bool:',
                '        """判断是否成功"""',
                '        return self.return_code == "0000"',
                ''
            ])
        
        # 添加to_dict和from_dict方法
        code_lines.extend([
            '    def to_dict(self) -> Dict[str, Any]:',
            '        """转换为字典"""',
            '        return attr.asdict(self, filter=lambda attr, value: value is not None)',
            '',
            '    @classmethod',
            '    def from_dict(cls, data: Dict[str, Any]) -> \'{}\':'.format(class_name),
            '        """从字典创建对象"""',
            '        return cls(**{k: v for k, v in data.items() if k in attr.fields_dict(cls)})',
        ])
        
        return '\n'.join(code_lines)



@define(kw_only=True)
class TestResult:
    """测试结果数据类"""
    
    # 测试用例信息
    test_case_id: str = field(validator=validators.instance_of(str))
    test_case_name: str = field(validator=validators.instance_of(str))
    test_module: str = field(validator=validators.instance_of(str))
    
    # 测试执行信息
    status: str = field(validator=validators.in_(["PASSED", "FAILED", "SKIPPED", "ERROR"]))
    start_time: datetime = field(validator=validators.instance_of(datetime))
    end_time: datetime = field(validator=validators.instance_of(datetime))
    duration: float = field(validator=validators.instance_of(float))
    
    # 测试结果详情
    error_message: Optional[str] = field(default=None)
    error_traceback: Optional[str] = field(default=None)
    
    # 请求响应信息
    request_data: Optional[Dict[str, Any]] = field(default=None)
    response_data: Optional[Dict[str, Any]] = field(default=None)
    response_time: Optional[float] = field(default=None)
    
    # 断言信息
    assertions: Optional[List[Dict[str, Any]]] = field(default=None)
    
    # 标签和优先级
    tags: Optional[List[str]] = field(default=None)
    priority: Optional[str] = field(default=None)
    
    @duration.validator
    def _validate_duration(self, attribute, value):
        """验证执行时长"""
        if value < 0:
            raise ValueError("执行时长不能为负数")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        for field_obj in attr.fields(self.__class__):
            value = getattr(self, field_obj.name)
            if value is not None:
                # 处理datetime对象
                if isinstance(value, datetime):
                    result[field_obj.name] = value.isoformat()
                else:
                    result[field_obj.name] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestResult':
        """从字典创建对象"""
        # 处理datetime字段
        if 'start_time' in data and isinstance(data['start_time'], str):
            data['start_time'] = datetime.fromisoformat(data['start_time'])
        if 'end_time' in data and isinstance(data['end_time'], str):
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        
        return cls(**{k: v for k, v in data.items() if k in attr.fields_dict(cls)})
    
    def is_passed(self) -> bool:
        """判断测试是否通过"""
        return self.status == "PASSED"
    
    def is_failed(self) -> bool:
        """判断测试是否失败"""
        return self.status in ["FAILED", "ERROR"]


@define(kw_only=True)
class PerformanceMetrics:
    """性能指标数据类"""
    
    # 基本信息
    test_name: str = field(validator=validators.instance_of(str))
    start_time: datetime = field(validator=validators.instance_of(datetime))
    end_time: datetime = field(validator=validators.instance_of(datetime))
    
    # 并发信息
    total_requests: int = field(validator=validators.instance_of(int))
    concurrent_users: int = field(validator=validators.instance_of(int))
    
    # 成功失败统计
    success_count: int = field(validator=validators.instance_of(int))
    failure_count: int = field(validator=validators.instance_of(int))
    
    # 响应时间统计(毫秒)
    min_response_time: float = field(validator=validators.instance_of(float))
    max_response_time: float = field(validator=validators.instance_of(float))
    avg_response_time: float = field(validator=validators.instance_of(float))
    p50_response_time: float = field(validator=validators.instance_of(float))
    p95_response_time: float = field(validator=validators.instance_of(float))
    p99_response_time: float = field(validator=validators.instance_of(float))
    
    # 吞吐量
    tps: float = field(validator=validators.instance_of(float))
    
    # 错误信息
    error_details: Optional[List[Dict[str, Any]]] = field(default=None)
    
    @total_requests.validator
    def _validate_total_requests(self, attribute, value):
        """验证总请求数"""
        if value <= 0:
            raise ValueError("总请求数必须大于0")
    
    @concurrent_users.validator
    def _validate_concurrent_users(self, attribute, value):
        """验证并发用户数"""
        if value <= 0:
            raise ValueError("并发用户数必须大于0")
    
    @tps.validator
    def _validate_tps(self, attribute, value):
        """验证TPS"""
        if value < 0:
            raise ValueError("TPS不能为负数")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        for field_obj in attr.fields(self.__class__):
            value = getattr(self, field_obj.name)
            if value is not None:
                # 处理datetime对象
                if isinstance(value, datetime):
                    result[field_obj.name] = value.isoformat()
                else:
                    result[field_obj.name] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceMetrics':
        """从字典创建对象"""
        # 处理datetime字段
        if 'start_time' in data and isinstance(data['start_time'], str):
            data['start_time'] = datetime.fromisoformat(data['start_time'])
        if 'end_time' in data and isinstance(data['end_time'], str):
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        
        return cls(**{k: v for k, v in data.items() if k in attr.fields_dict(cls)})
    
    def get_success_rate(self) -> float:
        """计算成功率"""
        if self.total_requests == 0:
            return 0.0
        return (self.success_count / self.total_requests) * 100
    
    def get_failure_rate(self) -> float:
        """计算失败率"""
        if self.total_requests == 0:
            return 0.0
        return (self.failure_count / self.total_requests) * 100
    
    def get_duration(self) -> float:
        """获取测试持续时间(秒)"""
        return (self.end_time - self.start_time).total_seconds()


@define(kw_only=True)
class SplitRule:
    """分账规则数据类"""
    
    # 分账接收方信息
    receiver_id: str = field(validator=validators.instance_of(str))
    receiver_type: str = field(validator=validators.in_(["MCH", "USER"]))
    receiver_accttype: str = field(validator=validators.in_(["MCHOWN", "USEROWN", "MCHASSUREMCH"]))
    
    # 分账金额
    split_amount: str = field(validator=validators.instance_of(str))
    
    # 分账描述
    split_desc: Optional[str] = field(default=None)
    
    # 分账比例(可选,与split_amount二选一)
    split_ratio: Optional[str] = field(default=None)
    
    @split_amount.validator
    def _validate_split_amount(self, attribute, value):
        """验证分账金额格式"""
        try:
            amount = float(value)
            if amount <= 0:
                raise ValueError("分账金额必须大于0")
        except ValueError as e:
            if "分账金额必须大于0" in str(e):
                raise
            raise ValueError(f"分账金额格式错误: {value}")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return attr.asdict(self, filter=lambda attr, value: value is not None)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SplitRule':
        """从字典创建对象"""
        return cls(**{k: v for k, v in data.items() if k in attr.fields_dict(cls)})
    
    def get_amount_as_float(self) -> float:
        """获取分账金额的浮点数值"""
        return float(self.split_amount)
    
    def get_ratio_as_float(self) -> Optional[float]:
        """获取分账比例的浮点数值"""
        if self.split_ratio:
            return float(self.split_ratio)
        return None
