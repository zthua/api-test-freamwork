"""
存储管理器模块

使用SQLite数据库统一管理配置、缓存、Schema、测试用例和测试结果。
"""
import sqlite3
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from utils.logger import Logger


class StorageManager:
    """
    存储管理器
    
    使用SQLite数据库管理框架的各类数据,包括:
    - 配置数据
    - 缓存数据
    - JSON Schema
    - 测试用例
    - 测试结果
    """
    
    def __init__(self, db_path: str = "storage/framework.db"):
        """
        初始化存储管理器
        
        Args:
            db_path: 数据库文件路径,默认为storage/framework.db
        """
        self.logger = Logger()
        self.db_path = Path(db_path)
        
        # 确保存储目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        self._init_database()
        
        self.logger.info(f"StorageManager initialized with database: {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        获取数据库连接
        
        Returns:
            数据库连接对象
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # 使查询结果可以通过列名访问
        return conn
    
    def _init_database(self) -> None:
        """
        初始化数据库表结构
        
        创建以下表:
        - config: 配置数据表
        - cache: 缓存数据表
        - schema: JSON Schema表
        - test_cases: 测试用例表
        - test_results: 测试结果表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 配置表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 缓存表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    expire_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Schema表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    schema_json TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 测试用例表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id TEXT UNIQUE NOT NULL,
                    case_name TEXT NOT NULL,
                    payment_mode TEXT,
                    payment_method TEXT,
                    priority TEXT,
                    tags TEXT,
                    test_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 测试结果表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id TEXT NOT NULL,
                    test_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    duration REAL,
                    error_message TEXT,
                    request_data TEXT,
                    response_data TEXT,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_config_key ON config(key)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_key ON cache(key)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_schema_name ON schema(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_test_cases_case_id ON test_cases(case_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_test_cases_payment_mode ON test_cases(payment_mode)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_test_results_case_id ON test_results(case_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_test_results_status ON test_results(status)")
            
            conn.commit()
            self.logger.info("Database tables initialized successfully")
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to initialize database: {str(e)}")
            raise
        finally:
            conn.close()
    
    def close(self) -> None:
        """关闭数据库连接(SQLite会自动管理连接,此方法用于兼容性)"""
        self.logger.info("StorageManager closed")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
    
    def __repr__(self) -> str:
        """返回存储管理器的字符串表示"""
        return f"StorageManager(db_path='{self.db_path}')"

    # ==================== 配置存储功能 ====================
    
    def save_config(self, key: str, value: Any, description: str = None) -> bool:
        """
        保存配置
        
        Args:
            key: 配置键
            value: 配置值(会自动转换为JSON字符串)
            description: 配置描述
            
        Returns:
            是否保存成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 将值转换为JSON字符串
            value_json = json.dumps(value, ensure_ascii=False)
            
            # 使用REPLACE实现插入或更新
            cursor.execute("""
                INSERT OR REPLACE INTO config (key, value, description, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (key, value_json, description))
            
            conn.commit()
            self.logger.debug(f"Config saved: {key}")
            return True
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to save config '{key}': {str(e)}")
            return False
        finally:
            conn.close()
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置
        
        Args:
            key: 配置键
            default: 默认值(当配置不存在时返回)
            
        Returns:
            配置值(自动从JSON字符串解析)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
            row = cursor.fetchone()
            
            if row:
                return json.loads(row['value'])
            else:
                return default
                
        except Exception as e:
            self.logger.error(f"Failed to get config '{key}': {str(e)}")
            return default
        finally:
            conn.close()
    
    def delete_config(self, key: str) -> bool:
        """
        删除配置
        
        Args:
            key: 配置键
            
        Returns:
            是否删除成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM config WHERE key = ?", (key,))
            conn.commit()
            
            deleted = cursor.rowcount > 0
            if deleted:
                self.logger.debug(f"Config deleted: {key}")
            return deleted
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to delete config '{key}': {str(e)}")
            return False
        finally:
            conn.close()
    
    def list_configs(self) -> List[Dict[str, Any]]:
        """
        列出所有配置
        
        Returns:
            配置列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT key, value, description, created_at, updated_at FROM config")
            rows = cursor.fetchall()
            
            configs = []
            for row in rows:
                configs.append({
                    'key': row['key'],
                    'value': json.loads(row['value']),
                    'description': row['description'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })
            
            return configs
            
        except Exception as e:
            self.logger.error(f"Failed to list configs: {str(e)}")
            return []
        finally:
            conn.close()

    # ==================== Schema存储功能 ====================
    
    def save_schema(self, name: str, schema: Dict[str, Any], description: str = None) -> bool:
        """
        保存JSON Schema
        
        Args:
            name: Schema名称
            schema: JSON Schema字典
            description: Schema描述
            
        Returns:
            是否保存成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 将Schema转换为JSON字符串
            schema_json = json.dumps(schema, ensure_ascii=False, indent=2)
            
            # 使用REPLACE实现插入或更新
            cursor.execute("""
                INSERT OR REPLACE INTO schema (name, schema_json, description, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (name, schema_json, description))
            
            conn.commit()
            self.logger.debug(f"Schema saved: {name}")
            return True
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to save schema '{name}': {str(e)}")
            return False
        finally:
            conn.close()
    
    def get_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取JSON Schema
        
        Args:
            name: Schema名称
            
        Returns:
            JSON Schema字典,不存在时返回None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT schema_json FROM schema WHERE name = ?", (name,))
            row = cursor.fetchone()
            
            if row:
                return json.loads(row['schema_json'])
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get schema '{name}': {str(e)}")
            return None
        finally:
            conn.close()
    
    def delete_schema(self, name: str) -> bool:
        """
        删除JSON Schema
        
        Args:
            name: Schema名称
            
        Returns:
            是否删除成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM schema WHERE name = ?", (name,))
            conn.commit()
            
            deleted = cursor.rowcount > 0
            if deleted:
                self.logger.debug(f"Schema deleted: {name}")
            return deleted
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to delete schema '{name}': {str(e)}")
            return False
        finally:
            conn.close()
    
    def list_schemas(self) -> List[Dict[str, Any]]:
        """
        列出所有Schema
        
        Returns:
            Schema列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT name, description, created_at, updated_at FROM schema")
            rows = cursor.fetchall()
            
            schemas = []
            for row in rows:
                schemas.append({
                    'name': row['name'],
                    'description': row['description'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })
            
            return schemas
            
        except Exception as e:
            self.logger.error(f"Failed to list schemas: {str(e)}")
            return []
        finally:
            conn.close()

    # ==================== 测试用例存储功能 ====================
    
    def save_test_case(self, case_id: str, case_name: str, test_data: Dict[str, Any],
                       payment_mode: str = None, payment_method: str = None,
                       priority: str = None, tags: List[str] = None) -> bool:
        """
        保存测试用例
        
        Args:
            case_id: 用例ID
            case_name: 用例名称
            test_data: 测试数据字典
            payment_mode: 支付模式(直清/账户/担保/分账)
            payment_method: 支付方式(微信/支付宝等)
            priority: 优先级(P0/P1/P2/P3)
            tags: 标签列表
            
        Returns:
            是否保存成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 将测试数据和标签转换为JSON字符串
            test_data_json = json.dumps(test_data, ensure_ascii=False)
            tags_json = json.dumps(tags or [], ensure_ascii=False)
            
            # 使用REPLACE实现插入或更新
            cursor.execute("""
                INSERT OR REPLACE INTO test_cases 
                (case_id, case_name, payment_mode, payment_method, priority, tags, test_data, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (case_id, case_name, payment_mode, payment_method, priority, tags_json, test_data_json))
            
            conn.commit()
            self.logger.debug(f"Test case saved: {case_id}")
            return True
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to save test case '{case_id}': {str(e)}")
            return False
        finally:
            conn.close()
    
    def get_test_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        获取测试用例
        
        Args:
            case_id: 用例ID
            
        Returns:
            测试用例字典,不存在时返回None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT case_id, case_name, payment_mode, payment_method, priority, tags, test_data, 
                       created_at, updated_at
                FROM test_cases WHERE case_id = ?
            """, (case_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'case_id': row['case_id'],
                    'case_name': row['case_name'],
                    'payment_mode': row['payment_mode'],
                    'payment_method': row['payment_method'],
                    'priority': row['priority'],
                    'tags': json.loads(row['tags']),
                    'test_data': json.loads(row['test_data']),
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get test case '{case_id}': {str(e)}")
            return None
        finally:
            conn.close()
    
    def get_test_cases(self, payment_mode: str = None, payment_method: str = None,
                       priority: str = None, tag: str = None) -> List[Dict[str, Any]]:
        """
        查询测试用例(支持按条件过滤)
        
        Args:
            payment_mode: 支付模式过滤
            payment_method: 支付方式过滤
            priority: 优先级过滤
            tag: 标签过滤
            
        Returns:
            测试用例列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 构建查询条件
            query = """
                SELECT case_id, case_name, payment_mode, payment_method, priority, tags, test_data,
                       created_at, updated_at
                FROM test_cases WHERE 1=1
            """
            params = []
            
            if payment_mode:
                query += " AND payment_mode = ?"
                params.append(payment_mode)
            
            if payment_method:
                query += " AND payment_method = ?"
                params.append(payment_method)
            
            if priority:
                query += " AND priority = ?"
                params.append(priority)
            
            if tag:
                query += " AND tags LIKE ?"
                params.append(f'%"{tag}"%')
            
            query += " ORDER BY case_id"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            test_cases = []
            for row in rows:
                test_cases.append({
                    'case_id': row['case_id'],
                    'case_name': row['case_name'],
                    'payment_mode': row['payment_mode'],
                    'payment_method': row['payment_method'],
                    'priority': row['priority'],
                    'tags': json.loads(row['tags']),
                    'test_data': json.loads(row['test_data']),
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })
            
            return test_cases
            
        except Exception as e:
            self.logger.error(f"Failed to get test cases: {str(e)}")
            return []
        finally:
            conn.close()
    
    def delete_test_case(self, case_id: str) -> bool:
        """
        删除测试用例
        
        Args:
            case_id: 用例ID
            
        Returns:
            是否删除成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM test_cases WHERE case_id = ?", (case_id,))
            conn.commit()
            
            deleted = cursor.rowcount > 0
            if deleted:
                self.logger.debug(f"Test case deleted: {case_id}")
            return deleted
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to delete test case '{case_id}': {str(e)}")
            return False
        finally:
            conn.close()

    # ==================== 测试结果存储功能 ====================
    
    def save_test_result(self, case_id: str, test_name: str, status: str,
                        duration: float = None, error_message: str = None,
                        request_data: Dict[str, Any] = None,
                        response_data: Dict[str, Any] = None) -> bool:
        """
        保存测试结果
        
        Args:
            case_id: 用例ID
            test_name: 测试名称
            status: 测试状态(passed/failed/skipped/error)
            duration: 执行时长(秒)
            error_message: 错误信息
            request_data: 请求数据
            response_data: 响应数据
            
        Returns:
            是否保存成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 将请求和响应数据转换为JSON字符串
            request_json = json.dumps(request_data or {}, ensure_ascii=False)
            response_json = json.dumps(response_data or {}, ensure_ascii=False)
            
            cursor.execute("""
                INSERT INTO test_results 
                (case_id, test_name, status, duration, error_message, request_data, response_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (case_id, test_name, status, duration, error_message, request_json, response_json))
            
            conn.commit()
            self.logger.debug(f"Test result saved: {case_id} - {status}")
            return True
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to save test result for '{case_id}': {str(e)}")
            return False
        finally:
            conn.close()
    
    def get_test_results(self, case_id: str = None, status: str = None,
                        start_date: str = None, end_date: str = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """
        查询测试结果
        
        Args:
            case_id: 用例ID过滤
            status: 状态过滤(passed/failed/skipped/error)
            start_date: 开始日期(YYYY-MM-DD)
            end_date: 结束日期(YYYY-MM-DD)
            limit: 返回结果数量限制
            
        Returns:
            测试结果列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 构建查询条件
            query = """
                SELECT id, case_id, test_name, status, duration, error_message,
                       request_data, response_data, executed_at
                FROM test_results WHERE 1=1
            """
            params = []
            
            if case_id:
                query += " AND case_id = ?"
                params.append(case_id)
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            if start_date:
                query += " AND DATE(executed_at) >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND DATE(executed_at) <= ?"
                params.append(end_date)
            
            query += " ORDER BY executed_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'id': row['id'],
                    'case_id': row['case_id'],
                    'test_name': row['test_name'],
                    'status': row['status'],
                    'duration': row['duration'],
                    'error_message': row['error_message'],
                    'request_data': json.loads(row['request_data']),
                    'response_data': json.loads(row['response_data']),
                    'executed_at': row['executed_at']
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to get test results: {str(e)}")
            return []
        finally:
            conn.close()
    
    def get_test_statistics(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        获取测试统计信息
        
        Args:
            start_date: 开始日期(YYYY-MM-DD)
            end_date: 结束日期(YYYY-MM-DD)
            
        Returns:
            统计信息字典,包含:
                - total: 总测试数
                - passed: 通过数
                - failed: 失败数
                - skipped: 跳过数
                - error: 错误数
                - pass_rate: 通过率
                - avg_duration: 平均执行时长
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 构建查询条件
            query = """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END) as passed,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skipped,
                    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error,
                    AVG(duration) as avg_duration
                FROM test_results WHERE 1=1
            """
            params = []
            
            if start_date:
                query += " AND DATE(executed_at) >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND DATE(executed_at) <= ?"
                params.append(end_date)
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            total = row['total'] or 0
            passed = row['passed'] or 0
            failed = row['failed'] or 0
            skipped = row['skipped'] or 0
            error = row['error'] or 0
            avg_duration = row['avg_duration'] or 0
            
            pass_rate = (passed / total * 100) if total > 0 else 0
            
            return {
                'total': total,
                'passed': passed,
                'failed': failed,
                'skipped': skipped,
                'error': error,
                'pass_rate': round(pass_rate, 2),
                'avg_duration': round(avg_duration, 3) if avg_duration else 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get test statistics: {str(e)}")
            return {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'error': 0,
                'pass_rate': 0,
                'avg_duration': 0
            }
        finally:
            conn.close()
    
    def delete_test_results(self, case_id: str = None, before_date: str = None) -> int:
        """
        删除测试结果
        
        Args:
            case_id: 用例ID(删除指定用例的所有结果)
            before_date: 删除指定日期之前的结果(YYYY-MM-DD)
            
        Returns:
            删除的记录数
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            query = "DELETE FROM test_results WHERE 1=1"
            params = []
            
            if case_id:
                query += " AND case_id = ?"
                params.append(case_id)
            
            if before_date:
                query += " AND DATE(executed_at) < ?"
                params.append(before_date)
            
            cursor.execute(query, params)
            conn.commit()
            
            deleted_count = cursor.rowcount
            if deleted_count > 0:
                self.logger.info(f"Deleted {deleted_count} test results")
            return deleted_count
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to delete test results: {str(e)}")
            return 0
        finally:
            conn.close()
