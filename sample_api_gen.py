"""
自动生成的API对象定义
生成时间: 2026-03-11 19:56:18
"""

from attrs import define, field, validators
from typing import Optional, List, Dict, Any
import attr

@define(kw_only=True)
class SamplePayRequest:
    """SamplePay请求对象"""
    
    txn_seqno: str = field(validator=validators.instance_of(str))
    mch_id: str = field(validator=validators.instance_of(str))
    total_amount: str = field(validator=validators.instance_of(str))
    sub_mchid: Optional[str] = field(default=None)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return attr.asdict(self, filter=lambda attr, value: value is not None)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SamplePayRequest':
        """从字典创建对象"""
        return cls(**{k: v for k, v in data.items() if k in attr.fields_dict(cls)})

@define(kw_only=True)
class SamplePayResponse:
    """SamplePay响应对象"""
    
    return_code: str = field()
    return_msg: str = field()
    order_id: Optional[str] = field(default=None)
    
    def is_success(self) -> bool:
        """判断是否成功"""
        return self.return_code == "0000"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return attr.asdict(self, filter=lambda attr, value: value is not None)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SamplePayResponse':
        """从字典创建对象"""
        return cls(**{k: v for k, v in data.items() if k in attr.fields_dict(cls)})
