"""
支付场景编排模块

提供各种支付场景的高级封装:
- 直清模式支付
- 账户模式支付
- 担保支付
- 分账支付
"""

from typing import Dict, Any, Optional, List
from attrs import define, field

from api.generic_api import GenericAPI
from api.models import APIRequest, APIResponse, PayeeInfo, SplitRule
from utils.data_generator import DataGenerator
from utils.config_manager import ConfigManager
from utils.logger import Logger


@define
class APIScenarios:
    """
    支付场景编排类
    
    提供各种支付场景的高级封装,简化测试用例编写
    """
    
    # 必需组件
    api: GenericAPI = field()
    data_generator: DataGenerator = field(default=None)
    config: ConfigManager = field(default=None)
    logger: Logger = field(default=None)
    
    def __attrs_post_init__(self):
        """初始化后处理"""
        # 如果没有提供data_generator,创建默认data_generator
        if self.data_generator is None:
            self.data_generator = DataGenerator()
        
        # 如果没有提供config,使用api的config
        if self.config is None:
            self.config = self.api.config
        
        # 如果没有提供logger,创建默认logger
        if self.logger is None:
            self.logger = Logger(name="APIScenarios")
        
        self.logger.info("APIScenarios initialized")
    
    def direct_mode_payment(
        self,
        pay_type: str,
        total_amount: str,
        **kwargs
    ) -> APIResponse:
        """
        直清模式支付
        
        直清模式:资金直接进入商户账户,无需二次结算
        
        Args:
            pay_type: 支付方式(WECHAT_APPLET/ALIPAY_NATIVE等)
            total_amount: 订单金额
            **kwargs: 其他可选参数
            
        Returns:
            创单响应对象
        """
        self.logger.info(f"Direct mode payment: pay_type={pay_type}, amount={total_amount}")
        
        # 生成基础数据
        txn_seqno = kwargs.get('txn_seqno') or self.data_generator.generate_txn_seqno()
        txn_time = kwargs.get('txn_time') or self.data_generator.generate_timestamp()
        mch_id = kwargs.get('mch_id') or self.config.get('merchant.mch_id')
        
        # 构建请求
        request = APIRequest(
            txn_seqno=txn_seqno,
            txn_time=txn_time,
            mch_id=mch_id,
            total_amount=total_amount,
            pay_type=pay_type,
            notify_url=kwargs.get('notify_url') or self.config.get('api.notify_url'),
            busi_type=kwargs.get('busi_type', '100001'),
            **self._extract_extra_params(kwargs)
        )
        
        # 调用API
        response = self.api.call_api(request)
        
        self.logger.info(f"Direct mode payment completed: order_id={response.order_id}")
        
        return response
    
    def account_mode_payment(
        self,
        pay_type: str,
        total_amount: str,
        sub_mch_id: Optional[str] = None,
        **kwargs
    ) -> APIResponse:
        """
        账户模式支付
        
        账户模式:资金进入平台账户,需要二次结算给商户
        
        Args:
            pay_type: 支付方式
            total_amount: 订单金额
            sub_mch_id: 子商户号(可选)
            **kwargs: 其他可选参数
            
        Returns:
            创单响应对象
        """
        self.logger.info(f"Account mode payment: pay_type={pay_type}, amount={total_amount}")
        
        # 生成基础数据
        txn_seqno = kwargs.get('txn_seqno') or self.data_generator.generate_txn_seqno()
        txn_time = kwargs.get('txn_time') or self.data_generator.generate_timestamp()
        mch_id = kwargs.get('mch_id') or self.config.get('merchant.mch_id')
        
        # 如果没有提供sub_mch_id,使用配置中的默认值
        if sub_mch_id is None:
            sub_mch_id = self.config.get('merchant.sub_mch_id')
        
        # 构建请求
        request = APIRequest(
            txn_seqno=txn_seqno,
            txn_time=txn_time,
            mch_id=mch_id,
            total_amount=total_amount,
            pay_type=pay_type,
            notify_url=kwargs.get('notify_url') or self.config.get('api.notify_url'),
            busi_type=kwargs.get('busi_type', '100001'),
            sub_mchid=sub_mch_id,  # 使用sub_mchid字段
            **self._extract_extra_params(kwargs)
        )
        
        # 调用API
        response = self.api.call_api(request)
        
        self.logger.info(f"Account mode payment completed: order_id={response.order_id}")
        
        return response
    
    def guarantee_payment(
        self,
        pay_type: str,
        total_amount: str,
        guarantee_days: int = 7,
        **kwargs
    ) -> APIResponse:
        """
        担保支付
        
        担保支付:资金冻结一段时间,确认后才结算给商户
        
        Args:
            pay_type: 支付方式
            total_amount: 订单金额
            guarantee_days: 担保天数(默认7天)
            **kwargs: 其他可选参数
            
        Returns:
            创单响应对象
        """
        self.logger.info(f"Guarantee payment: pay_type={pay_type}, amount={total_amount}, days={guarantee_days}")
        
        # 生成基础数据
        txn_seqno = kwargs.get('txn_seqno') or self.data_generator.generate_txn_seqno()
        txn_time = kwargs.get('txn_time') or self.data_generator.generate_timestamp()
        mch_id = kwargs.get('mch_id') or self.config.get('merchant.mch_id')
        
        # 构建请求(担保天数通过extend_info传递)
        extend_info = kwargs.get('extend_info', {})
        extend_info['guarantee_days'] = str(guarantee_days)
        
        request = APIRequest(
            txn_seqno=txn_seqno,
            txn_time=txn_time,
            mch_id=mch_id,
            total_amount=total_amount,
            pay_type=pay_type,
            notify_url=kwargs.get('notify_url') or self.config.get('api.notify_url'),
            busi_type=kwargs.get('busi_type', '100001'),
            extend_info=extend_info,
            **self._extract_extra_params(kwargs)
        )
        
        # 调用API
        response = self.api.call_api(request)
        
        self.logger.info(f"Guarantee payment completed: order_id={response.order_id}")
        
        return response
    
    def split_payment(
        self,
        pay_type: str,
        total_amount: str,
        split_rules: List[Dict[str, Any]],
        **kwargs
    ) -> APIResponse:
        """
        分账支付
        
        分账支付:订单金额按规则分配给多个收款方
        
        Args:
            pay_type: 支付方式
            total_amount: 订单金额
            split_rules: 分账规则列表,每个规则包含:
                - receiver_id: 收款方ID
                - receiver_type: 收款方类型(MCH/USER)
                - receiver_accttype: 收款方账户类型
                - split_amount: 分账金额
                - split_ratio: 分账比例(可选)
            **kwargs: 其他可选参数
            
        Returns:
            创单响应对象
        """
        self.logger.info(f"Split payment: pay_type={pay_type}, amount={total_amount}, rules={len(split_rules)}")
        
        # 生成基础数据
        txn_seqno = kwargs.get('txn_seqno') or self.data_generator.generate_txn_seqno()
        txn_time = kwargs.get('txn_time') or self.data_generator.generate_timestamp()
        mch_id = kwargs.get('mch_id') or self.config.get('merchant.mch_id')
        
        # 构建分账规则对象
        split_rule_objects = []
        for rule in split_rules:
            split_rule = SplitRule(
                receiver_id=rule['receiver_id'],
                receiver_type=rule.get('receiver_type', 'MCH'),
                receiver_accttype=rule.get('receiver_accttype', 'MCHOWN'),
                split_amount=rule['split_amount'],
                split_ratio=rule.get('split_ratio'),
                split_desc=rule.get('split_desc')
            )
            split_rule_objects.append(split_rule)
        
        # 将分账规则放入extend_info
        extend_info = kwargs.get('extend_info', {})
        extend_info['split_rules'] = split_rule_objects
        
        # 构建请求
        request = APIRequest(
            txn_seqno=txn_seqno,
            txn_time=txn_time,
            mch_id=mch_id,
            total_amount=total_amount,
            pay_type=pay_type,
            notify_url=kwargs.get('notify_url') or self.config.get('api.notify_url'),
            busi_type=kwargs.get('busi_type', '100001'),
            extend_info=extend_info,
            **self._extract_extra_params(kwargs)
        )
        
        # 调用API
        response = self.api.call_api(request)
        
        self.logger.info(f"Split payment completed: order_id={response.order_id}")
        
        return response
    
    def _extract_extra_params(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取额外参数
        
        从kwargs中提取APIRequest支持的额外参数
        
        Args:
            kwargs: 参数字典
            
        Returns:
            额外参数字典
        """
        # 定义已知的基础参数(不需要传递给APIRequest)
        known_params = {
            'txn_seqno', 'txn_time', 'mch_id', 'total_amount', 'pay_type',
            'notify_url', 'busi_type', 'sub_mch_id', 'guarantee_days', 'split_rules',
            'goods_name', 'acct_type', 'extend_info'
        }
        
        # 提取额外参数
        extra_params = {}
        for key, value in kwargs.items():
            if key not in known_params and value is not None:
                extra_params[key] = value
        
        return extra_params
    
    def close(self) -> None:
        """关闭场景编排器,释放资源"""
        if self.api:
            self.api.close()
        self.logger.info("APIScenarios closed")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
    
    def __repr__(self) -> str:
        """返回场景编排器的字符串表示"""
        return f"APIScenarios(api={self.api})"
