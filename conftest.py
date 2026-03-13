"""
pytest配置文件

定义全局fixtures和pytest钩子函数
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config_manager import ConfigManager
from utils.logger import Logger
from utils.http_client import HTTPClient
from utils.rsa_signer import RSASigner
from utils.data_generator import DataGenerator
from utils.middleware_registry import MiddlewareRegistry
from utils.storage_manager import StorageManager
from api.api_registry import APIRegistry, register_builtin_apis
from api.createpay_api import CreatePayAPI
from api.api_scenarios import APIScenarios


# ============================================================================
# 全局Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def config():
    """配置管理器fixture"""
    return ConfigManager()


@pytest.fixture(scope="session")
def logger():
    """日志记录器fixture"""
    return Logger(name="pytest")


@pytest.fixture(scope="session")
def http_client(middleware_registry):
    """HTTP客户端fixture"""
    client = HTTPClient(timeout=30, max_retries=3, middleware_registry=middleware_registry)
    yield client
    client.close()


@pytest.fixture(scope="session")
def rsa_signer(config):
    """RSA签名器fixture"""
    private_key_path = config.get('security.private_key_path')
    public_key_path = config.get('security.public_key_path')
    
    if private_key_path and public_key_path:
        return RSASigner(private_key_path=private_key_path, public_key_path=public_key_path)
    return None


@pytest.fixture(scope="session")
def data_generator():
    """数据生成器fixture"""
    return DataGenerator()


@pytest.fixture(scope="session")
def middleware_registry(config):
    """中间件注册器fixture"""
    registry = MiddlewareRegistry()
    # 从配置文件加载中间件
    middleware_config_path = config.get('middleware.config_path', 'config/middleware.yaml')
    try:
        registry.load_from_config(middleware_config_path)
    except Exception as e:
        print(f"Warning: Failed to load middleware config: {e}")
    return registry


@pytest.fixture(scope="session")
def storage_manager():
    """存储管理器fixture"""
    manager = StorageManager()
    yield manager
    manager.close()


@pytest.fixture(scope="session")
def api_registry(config):
    """API注册器fixture"""
    registry = APIRegistry(config)
    # 注册内置API
    register_builtin_apis(registry)
    yield registry
    registry.close_all()


@pytest.fixture(scope="function")
def createpay_api(api_registry):
    """CreatePay API fixture（向后兼容）"""
    return api_registry.get_api('createpay')


@pytest.fixture(scope="function")
def generic_api(api_registry):
    """通用API fixture"""
    return api_registry.get_api('createpay')


@pytest.fixture(scope="function")
def api_scenarios(config, data_generator, api_registry):
    """API场景编排器fixture"""
    createpay_api = api_registry.get_api('createpay')
    return APIScenarios(api=createpay_api, data_generator=data_generator, config=config)


# ============================================================================
# pytest钩子函数
# ============================================================================

def pytest_configure(config):
    """pytest配置钩子"""
    print("\n" + "=" * 80)
    print("API测试自动化框架 - 测试会话开始")
    print("=" * 80)


def pytest_collection_modifyitems(config, items):
    """修改测试用例收集"""
    # 可以在这里添加自定义的测试用例排序或过滤逻辑
    pass


def pytest_sessionstart(session):
    """测试会话开始"""
    pass


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束"""
    print("=" * 80)
    print("API测试自动化框架 - 测试会话结束")
    print(f"退出状态: {exitstatus}")
    print("=" * 80)
