"""
Configuration Manager for CreatePay Test Framework.

Supports:
- YAML/JSON configuration loading
- Multi-environment configuration (TEST/UAT/PROD)
- Environment variable override
- Nested key access with dot notation
- Configuration validation
"""
import os
import yaml
import json
from typing import Any, Dict, Optional
from pathlib import Path


class ConfigError(Exception):
    """Configuration related errors."""
    pass


class ConfigManager:
    """Configuration manager for test framework."""
    
    def __init__(self, env: str = None):
        """
        Initialize configuration manager.
        
        Args:
            env: Environment name (test/uat/prod). 
                 If None, reads from ENV environment variable or defaults to 'test'
        """
        self.env = env or os.getenv('ENV', 'test').lower()
        self.config: Dict[str, Any] = {}
        self._base_dir = Path(__file__).parent.parent
        self._config_dir = self._base_dir / 'config'
        
        # Load configurations
        self._load_configurations()
    
    def _load_configurations(self):
        """Load all configuration files."""
        # Load main config
        main_config_path = self._config_dir / 'config.yaml'
        if main_config_path.exists():
            self.config = self.load_config(str(main_config_path))
        
        # Load environment-specific config
        env_config_path = self._config_dir / 'env' / f'{self.env}.yaml'
        if env_config_path.exists():
            env_config = self.load_config(str(env_config_path))
            self._merge_config(self.config, env_config)
        
        # Override with environment variables
        self._apply_env_overrides()
        
        # Set environment in config
        self.config['environment'] = self.env
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file (YAML or JSON)
            
        Returns:
            Configuration dictionary
            
        Raises:
            ConfigError: If file cannot be loaded
        """
        try:
            path = Path(config_path)
            
            if not path.exists():
                raise ConfigError(f"Configuration file not found: {config_path}")
            
            with open(path, 'r', encoding='utf-8') as f:
                if path.suffix in ['.yaml', '.yml']:
                    return yaml.safe_load(f) or {}
                elif path.suffix == '.json':
                    return json.load(f)
                else:
                    raise ConfigError(f"Unsupported file format: {path.suffix}")
        
        except yaml.YAMLError as e:
            raise ConfigError(f"YAML parsing error: {e}")
        except json.JSONDecodeError as e:
            raise ConfigError(f"JSON parsing error: {e}")
        except Exception as e:
            raise ConfigError(f"Failed to load config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Supports dot notation for nested keys.
        Example: config.get('api.base_url')
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def validate(self) -> bool:
        """
        Validate configuration completeness.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ConfigError: If required configuration is missing
        """
        required_keys = [
            'api.base_url',
            'merchant.mch_id',
            'security.private_key_path',
            'security.public_key_path',
        ]
        
        missing_keys = []
        for key in required_keys:
            if self.get(key) is None:
                missing_keys.append(key)
        
        if missing_keys:
            raise ConfigError(
                f"Missing required configuration: {', '.join(missing_keys)}"
            )
        
        return True
    
    def _merge_config(self, base: Dict, override: Dict):
        """
        Merge override config into base config.
        
        Args:
            base: Base configuration dictionary
            override: Override configuration dictionary
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides."""
        # Support environment variable overrides with prefix CREATEPAY_
        prefix = 'CREATEPAY_'
        
        for env_key, env_value in os.environ.items():
            if env_key.startswith(prefix):
                # Convert CREATEPAY_API_BASE_URL to api.base_url
                config_key = env_key[len(prefix):].lower().replace('_', '.')
                self.set(config_key, env_value)
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration.
        
        Returns:
            Complete configuration dictionary
        """
        return self.config.copy()
    
    def reload(self):
        """Reload configuration from files."""
        self.config = {}
        self._load_configurations()
    
    def __repr__(self) -> str:
        return f"ConfigManager(env='{self.env}')"
