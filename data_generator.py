"""
Test Data Generator for CreatePay Test Framework.

Generates various test data:
- Transaction sequence numbers (txn_seqno)
- Timestamps and dates
- User IDs
- Order amounts
- Merchant IDs
"""
import uuid
import random
import string
from datetime import datetime
from typing import Optional
from decimal import Decimal


class DataGenerator:
    """Test data generator for payment testing."""
    
    @staticmethod
    def generate_txn_seqno(length: int = 32) -> str:
        """
        Generate unique transaction sequence number.
        
        Args:
            length: Length of sequence number (default: 32)
            
        Returns:
            32-character unique transaction sequence number
        """
        # Use timestamp + UUID to ensure uniqueness
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        unique_id = uuid.uuid4().hex
        
        # Combine and truncate to desired length
        seqno = (timestamp + unique_id)[:length]
        
        # Pad with random digits if needed
        if len(seqno) < length:
            seqno += ''.join(random.choices(string.digits, k=length - len(seqno)))
        
        return seqno
    
    @staticmethod
    def generate_timestamp(format: str = "%Y%m%d%H%M%S") -> str:
        """
        Generate timestamp string.
        
        Args:
            format: Timestamp format (default: YYYYMMDDHHmmss)
            
        Returns:
            Formatted timestamp string
        """
        return datetime.now().strftime(format)
    
    @staticmethod
    def generate_date(format: str = "%Y%m%d") -> str:
        """
        Generate date string.
        
        Args:
            format: Date format (default: YYYYMMDD)
            
        Returns:
            Formatted date string
        """
        return datetime.now().strftime(format)
    
    @staticmethod
    def generate_user_id(prefix: str = "U") -> str:
        """
        Generate unique user ID.
        
        Args:
            prefix: ID prefix (default: "U")
            
        Returns:
            Unique user ID
        """
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = ''.join(random.choices(string.digits, k=6))
        return f"{prefix}{timestamp}{random_suffix}"
    
    @staticmethod
    def generate_amount(
        min_amount: float = 0.01,
        max_amount: float = 10000.0,
        decimal_places: int = 2
    ) -> str:
        """
        Generate order amount.
        
        Args:
            min_amount: Minimum amount (default: 0.01)
            max_amount: Maximum amount (default: 10000.0)
            decimal_places: Number of decimal places (default: 2)
            
        Returns:
            Amount string with specified decimal places
        """
        amount = random.uniform(min_amount, max_amount)
        # Use Decimal for precise rounding
        amount_decimal = Decimal(str(amount)).quantize(
            Decimal(10) ** -decimal_places
        )
        return str(amount_decimal)
    
    @staticmethod
    def generate_merchant_id(prefix: str = "M") -> str:
        """
        Generate merchant ID.
        
        Args:
            prefix: ID prefix (default: "M")
            
        Returns:
            Merchant ID
        """
        # Generate 15-digit merchant ID
        digits = ''.join(random.choices(string.digits, k=15))
        return f"{prefix}{digits}"
    
    @staticmethod
    def generate_order_info(product_name: str = "测试商品") -> str:
        """
        Generate order info string.
        
        Args:
            product_name: Product name
            
        Returns:
            Order info string
        """
        return f"THIRD2|{product_name}"
    
    @staticmethod
    def generate_openid(platform: str = "wechat") -> str:
        """
        Generate openid for payment platforms.
        
        Args:
            platform: Platform name (wechat/alipay)
            
        Returns:
            Generated openid
        """
        # Generate 28-character openid
        chars = string.ascii_letters + string.digits + '-_'
        openid = ''.join(random.choices(chars, k=28))
        return openid
    
    @staticmethod
    def generate_appid(platform: str = "wechat") -> str:
        """
        Generate appid for payment platforms.
        
        Args:
            platform: Platform name (wechat/alipay)
            
        Returns:
            Generated appid
        """
        if platform.lower() == "wechat":
            # WeChat appid format: wx + 16 hex characters
            hex_chars = ''.join(random.choices(string.hexdigits.lower(), k=16))
            return f"wx{hex_chars}"
        elif platform.lower() == "alipay":
            # Alipay appid format: 16 digits
            return ''.join(random.choices(string.digits, k=16))
        else:
            return ''.join(random.choices(string.digits, k=16))
    
    @staticmethod
    def generate_phone_number() -> str:
        """
        Generate Chinese mobile phone number.
        
        Returns:
            11-digit phone number
        """
        # Chinese mobile prefixes
        prefixes = ['130', '131', '132', '133', '134', '135', '136', '137', '138', '139',
                   '150', '151', '152', '153', '155', '156', '157', '158', '159',
                   '180', '181', '182', '183', '184', '185', '186', '187', '188', '189']
        prefix = random.choice(prefixes)
        suffix = ''.join(random.choices(string.digits, k=8))
        return f"{prefix}{suffix}"
    
    @staticmethod
    def generate_email(domain: str = "test.com") -> str:
        """
        Generate email address.
        
        Args:
            domain: Email domain
            
        Returns:
            Email address
        """
        username_length = random.randint(6, 12)
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=username_length))
        return f"{username}@{domain}"
    
    @staticmethod
    def generate_ip_address() -> str:
        """
        Generate IP address.
        
        Returns:
            IP address string
        """
        return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"
    
    @staticmethod
    def generate_mac_address() -> str:
        """
        Generate MAC address for POS devices.
        
        Returns:
            MAC address string
        """
        mac = [random.randint(0x00, 0xff) for _ in range(6)]
        return ':'.join(f'{x:02x}' for x in mac)
    
    @staticmethod
    def generate_device_id() -> str:
        """
        Generate device ID.
        
        Returns:
            Device ID string
        """
        return uuid.uuid4().hex.upper()
    
    @classmethod
    def generate_test_data(
        cls,
        data_type: str,
        **kwargs
    ) -> str:
        """
        Generate test data by type.
        
        Args:
            data_type: Type of data to generate
            **kwargs: Additional parameters
            
        Returns:
            Generated data
        """
        generators = {
            'txn_seqno': cls.generate_txn_seqno,
            'timestamp': cls.generate_timestamp,
            'date': cls.generate_date,
            'user_id': cls.generate_user_id,
            'amount': cls.generate_amount,
            'merchant_id': cls.generate_merchant_id,
            'order_info': cls.generate_order_info,
            'openid': cls.generate_openid,
            'appid': cls.generate_appid,
            'phone': cls.generate_phone_number,
            'email': cls.generate_email,
            'ip': cls.generate_ip_address,
            'mac': cls.generate_mac_address,
            'device_id': cls.generate_device_id,
        }
        
        generator = generators.get(data_type)
        if generator:
            return generator(**kwargs)
        else:
            raise ValueError(f"Unknown data type: {data_type}")


# Convenience functions
def generate_txn_seqno() -> str:
    """Generate transaction sequence number."""
    return DataGenerator.generate_txn_seqno()


def generate_timestamp() -> str:
    """Generate timestamp."""
    return DataGenerator.generate_timestamp()


def generate_user_id() -> str:
    """Generate user ID."""
    return DataGenerator.generate_user_id()


def generate_amount(min_amount: float = 0.01, max_amount: float = 10000.0) -> str:
    """Generate amount."""
    return DataGenerator.generate_amount(min_amount, max_amount)
