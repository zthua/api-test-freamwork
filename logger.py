"""
Logger module for CreatePay Test Framework.

Features:
- Five log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Console and file dual output
- Log file rotation by date and size
- Sensitive information masking
- Colored console output
"""
import logging
import os
import re
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import List, Optional
from datetime import datetime


class SensitiveDataFilter(logging.Filter):
    """Filter to mask sensitive data in log messages."""
    
    SENSITIVE_PATTERNS = [
        (r'("sign"\s*:\s*")[^"]*(")', r'\1***MASKED***\2'),
        (r'("password"\s*:\s*")[^"]*(")', r'\1***MASKED***\2'),
        (r'("private_key"\s*:\s*")[^"]*(")', r'\1***MASKED***\2'),
        (r'("openid"\s*:\s*")[^"]{10,}(")', r'\1***MASKED***\2'),
        (r'(sign=)[^&\s]*', r'\1***MASKED***'),
        (r'(password=)[^&\s]*', r'\1***MASKED***'),
    ]
    
    def filter(self, record):
        """Filter log record to mask sensitive data."""
        record.msg = self.mask_sensitive_data(str(record.msg))
        return True
    
    @staticmethod
    def mask_sensitive_data(text: str) -> str:
        """
        Mask sensitive data in text.
        
        Args:
            text: Text to mask
            
        Returns:
            Masked text
        """
        for pattern, replacement in SensitiveDataFilter.SENSITIVE_PATTERNS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text


class Logger:
    """Logger wrapper for test framework."""
    
    _instances = {}
    
    def __init__(
        self,
        name: str = "createpay_test",
        level: str = "INFO",
        log_dir: str = "logs",
        console_output: bool = True,
        file_output: bool = True,
        max_bytes: int = 104857600,  # 100MB
        backup_count: int = 10,
    ):
        """
        Initialize logger.
        
        Args:
            name: Logger name
            level: Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
            log_dir: Directory for log files
            console_output: Enable console output
            file_output: Enable file output
            max_bytes: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
        """
        self.name = name
        self.level = getattr(logging, level.upper(), logging.INFO)
        self.log_dir = Path(log_dir)
        self.console_output = console_output
        self.file_output = file_output
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        
        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.level)
        self.logger.handlers.clear()
        
        # Add sensitive data filter
        self.logger.addFilter(SensitiveDataFilter())
        
        # Setup handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup log handlers."""
        # Console handler
        if self.console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.level)
            console_formatter = self._get_colored_formatter()
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        # File handler with rotation
        if self.file_output:
            # Main log file with size rotation
            log_file = self.log_dir / f"{self.name}.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(self.level)
            file_formatter = self._get_file_formatter()
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            
            # Daily log file with date rotation
            daily_log_file = self.log_dir / f"{self.name}_daily.log"
            daily_handler = TimedRotatingFileHandler(
                daily_log_file,
                when='midnight',
                interval=1,
                backupCount=30,
                encoding='utf-8'
            )
            daily_handler.setLevel(self.level)
            daily_handler.setFormatter(file_formatter)
            self.logger.addHandler(daily_handler)
    
    def _get_colored_formatter(self) -> logging.Formatter:
        """Get colored formatter for console output."""
        try:
            import colorlog
            formatter = colorlog.ColoredFormatter(
                '%(log_color)s%(asctime)s - %(name)s - %(levelname)-8s%(reset)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
        except ImportError:
            # Fallback to standard formatter if colorlog not available
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)-8s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        return formatter
    
    def _get_file_formatter(self) -> logging.Formatter:
        """Get formatter for file output."""
        return logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)-8s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message."""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message."""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message."""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message."""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message."""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, *args, **kwargs)
    
    @classmethod
    def get_logger(
        cls,
        name: str = "createpay_test",
        **kwargs
    ) -> 'Logger':
        """
        Get or create logger instance (singleton per name).
        
        Args:
            name: Logger name
            **kwargs: Additional logger configuration
            
        Returns:
            Logger instance
        """
        if name not in cls._instances:
            cls._instances[name] = cls(name=name, **kwargs)
        return cls._instances[name]
    
    @staticmethod
    def mask_sensitive_data(text: str) -> str:
        """
        Mask sensitive data in text.
        
        Args:
            text: Text to mask
            
        Returns:
            Masked text
        """
        return SensitiveDataFilter.mask_sensitive_data(text)


# Global logger instance
_default_logger = None


def get_logger(name: str = "createpay_test", **kwargs) -> Logger:
    """
    Get logger instance.
    
    Args:
        name: Logger name
        **kwargs: Additional logger configuration
        
    Returns:
        Logger instance
    """
    return Logger.get_logger(name=name, **kwargs)


def setup_logger_from_config(config_manager) -> Logger:
    """
    Setup logger from configuration manager.
    
    Args:
        config_manager: ConfigManager instance
        
    Returns:
        Configured Logger instance
    """
    log_config = {
        'level': config_manager.get('logging.level', 'INFO'),
        'console_output': config_manager.get('logging.console_output', True),
        'file_output': config_manager.get('logging.file_output', True),
        'max_bytes': config_manager.get('logging.file_max_bytes', 104857600),
        'backup_count': config_manager.get('logging.backup_count', 10),
    }
    
    return get_logger(**log_config)
