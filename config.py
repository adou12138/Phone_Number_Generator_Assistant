# -*- coding: utf-8 -*-
"""
配置文件读取模块

本模块负责从config.yaml文件中加载应用配置，
提供统一的配置访问接口，支持默认配置值。

功能说明：
- 加载config.yaml配置文件
- 提供配置项的默认值
- 支持环境变量覆盖配置
- 配置验证和类型转换

作者：Phone Number Generator
版本：1.0.0
"""

import os
import yaml
from typing import Any, Dict, List, Optional
from pathlib import Path


class Config:
    """
    配置管理类
    
    负责加载和管理应用的配置信息，
    支持从YAML文件读取配置，提供配置项的访问接口。
    
    属性：
        app: 应用配置（host, port, debug, secret_key）
        login: 登录配置（enabled, users）
        generator: 生成器配置（max_count, batch_size, file_size_limit）
        database: 数据库配置（path, csv_path）
        download: 下载配置（dir, expire_hours）
        logging: 日志配置（level, file）
    """
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        初始化配置管理类
        
        参数：
            config_path: 配置文件路径，默认为'config.yaml'
        
        加载流程：
            1. 检查配置文件是否存在
            2. 加载YAML文件内容
            3. 合并默认配置
            4. 应用环境变量覆盖（如果有）
        """
        self._config: Dict[str, Any] = {}
        self._config_path = config_path
        self._load_config()
        # 计算项目根目录：config.py所在目录的父目录
        self.base_dir = Path(__file__).parent
    
    def _load_config(self) -> None:
        """
        加载配置文件
        
        私有方法，用于从YAML文件加载配置信息。
        如果配置文件不存在或加载失败，使用默认配置。
        """
        default_config = self._get_default_config()
        
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f) or {}
                # 合并用户配置和默认配置
                self._config = self._merge_config(default_config, user_config)
            except Exception as e:
                print(f"警告：加载配置文件失败，使用默认配置。错误：{e}")
                self._config = default_config
        else:
            print(f"警告：配置文件 {self._config_path} 不存在，使用默认配置。")
            self._config = default_config
        
        # 应用环境变量覆盖
        self._apply_env_overrides()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置
        
        返回应用的默认配置字典。
        
        返回：
            Dict[str, Any]: 默认配置字典
        """
        return {
            'app': {
                'host': '0.0.0.0',
                'port': 5000,
                'debug': False,
                'secret_key': 'phone-generator-secret-key-change-in-production'
            },
            'login': {
                'enabled': False,
                'users': [
                    {
                        'username': 'admin',
                        'password': 'admin123'
                    }
                ]
            },
            'generator': {
                'max_count': 10000000,
                'batch_size': 500,
                'file_size_limit': 20
            },
            'database': {
                'path': 'data/phone_location.db',
                'csv_path': 'data/phone_location.csv'
            },
            'download': {
                'dir': 'downloads',
                'expire_hours': 24
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/app.log'
            }
        }
    
    def _merge_config(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """
        递归合并配置
        
        将用户配置递归合并到默认配置中，
        用户配置会覆盖默认配置的值。
        
        参数：
            default: 默认配置字典
            user: 用户配置字典
        
        返回：
            Dict[str, Any]: 合并后的配置字典
        """
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result
    
    def _apply_env_overrides(self) -> None:
        """
        应用环境变量覆盖
        
        检查环境变量是否设置了覆盖值，
        目前支持以下环境变量：
        - APP_PORT: 应用端口
        - LOGIN_ENABLED: 是否启用登录
        - DEBUG_MODE: 调试模式
        """
        # 应用端口覆盖
        app_port = os.environ.get('APP_PORT')
        if app_port:
            try:
                self._config['app']['port'] = int(app_port)
            except ValueError:
                print(f"警告：环境变量APP_PORT值无效，使用默认端口。")
        
        # 登录开关覆盖
        login_enabled = os.environ.get('LOGIN_ENABLED')
        if login_enabled:
            self._config['login']['enabled'] = login_enabled.lower() in ('true', '1', 'yes')
        
        # 调试模式覆盖
        debug_mode = os.environ.get('DEBUG_MODE')
        if debug_mode:
            self._config['app']['debug'] = debug_mode.lower() in ('true', '1', 'yes')
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        通过点分隔的路径获取配置项的值。
        
        参数：
            key: 配置项路径，如'app.port'
            default: 默认值，当配置项不存在时返回
        
        返回：
            Any: 配置项的值，不存在时返回默认值
        
        示例：
            >>> config.get('app.port')
            5000
            >>> config.get('login.enabled')
            False
        """
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    @property
    def app(self) -> Dict[str, Any]:
        """
        应用配置属性
        
        返回：
            Dict[str, Any]: 应用配置字典
        """
        return self._config.get('app', {})
    
    @property
    def login(self) -> Dict[str, Any]:
        """
        登录配置属性
        
        返回：
            Dict[str, Any]: 登录配置字典
        """
        return self._config.get('login', {})
    
    @property
    def generator(self) -> Dict[str, Any]:
        """
        生成器配置属性
        
        返回：
            Dict[str, Any]: 生成器配置字典
        """
        return self._config.get('generator', {})
    
    @property
    def database(self) -> Dict[str, Any]:
        """
        数据库配置属性
        
        返回：
            Dict[str, Any]: 数据库配置字典
        """
        return self._config.get('database', {})
    
    @property
    def download(self) -> Dict[str, Any]:
        """
        下载配置属性
        
        返回：
            Dict[str, Any]: 下载配置字典
        """
        return self._config.get('download', {})
    
    @property
    def logging(self) -> Dict[str, Any]:
        """
        日志配置属性
        
        返回：
            Dict[str, Any]: 日志配置字典
        """
        return self._config.get('logging', {})
    
    def get_app_config(self) -> Dict[str, Any]:
        """
        获取完整的应用配置
        
        用于传递给Flask应用的配置。
        
        返回：
            Dict[str, Any]: Flask应用配置字典
        """
        return {
            'DEBUG': self.app.get('debug', False),
            'SECRET_KEY': self.app.get('secret_key', 'default-secret-key'),
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Lax'
        }
    
    def validate_login(self, username: str, password: str) -> bool:
        """
        验证登录凭证
        
        检查提供的用户名和密码是否有效。
        
        参数：
            username: 用户名
            password: 密码
        
        返回：
            bool: 凭证有效返回True，否则返回False
        """
        users = self.login.get('users', [])
        for user in users:
            if user.get('username') == username and user.get('password') == password:
                return True
        return False
    
    def get_users(self) -> List[Dict[str, str]]:
        """
        获取用户列表
        
        返回配置中的所有用户信息。
        
        返回：
            List[Dict[str, str]]: 用户信息列表，每个用户包含username和password
        """
        return self.login.get('users', [])
    
    def is_login_enabled(self) -> bool:
        """
        检查是否启用登录
        
        返回：
            bool: 启用登录返回True，否则返回False
        """
        return self.login.get('enabled', False)
    
    def get_database_path(self) -> str:
        """
        获取数据库文件路径
        
        返回：
            str: 数据库文件的绝对路径，根据操作系统自动转换路径格式
        """
        base_dir = self.base_dir
        db_path = self.database.get('path', 'data/phone_location.db')
        return str(base_dir / db_path)
    
    def get_csv_path(self) -> str:
        """
        获取CSV文件路径
        
        返回：
            str: CSV文件的绝对路径，根据操作系统自动转换路径格式
        """
        base_dir = self.base_dir
        csv_path = self.database.get('csv_path', 'data/phone_location.csv')
        return str(base_dir / csv_path)
    
    def get_download_dir(self) -> str:
        """
        获取下载目录路径
        返回：str: 下载目录的绝对路径，根据配置文件 vercel_tmp 设置决定
        """
        base_dir = self.base_dir

        # 根据配置决定是否使用 /tmp 目录
        if self.is_vercel_tmp_enabled():
            base_dir = Path('/tmp')

        download_dir = self.download.get('dir', 'downloads')
        download_path = base_dir / download_dir

        # 确保下载目录存在（非 /tmp 目录）
        if not download_path.exists():
            download_path.mkdir(parents=True, exist_ok=True)
            return str(download_path)
         #  /tmp 目录直接返回
        return str(download_path)
    
    def get_log_file(self) -> str:
        """
        获取日志文件路径
        
        返回：
            str: 日志文件的绝对路径，根据配置文件 vercel_tmp 设置决定
        """
        base_dir = self.base_dir

        # 根据配置决定是否使用 /tmp 目录
        if self.is_vercel_tmp_enabled():
            base_dir = Path('/tmp')

        log_file = self.logging.get('file', 'logs/app.log')
        log_path = base_dir / log_file

        # 确保日志目录存在
        log_dir = log_path.parent
        if not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)
        return str(log_path)
        
    def is_vercel_tmp_enabled(self) -> bool:
        """
        检查是否启用 /tmp 目录
        
        读取配置文件中的 vercel_tmp 设置
        返回：
            bool: 启用返回 True，否则返回 False
        """
        return self.logging.get('vercel_tmp', False)

# 全局配置实例
# 在应用中使用此单例访问配置
config = Config()

if __name__ == '__main__':
    """
    配置模块测试代码
    
    直接运行此模块时，输出当前配置信息。
    """
    print("=" * 60)
    print("手机号码生成查询系统 - 配置信息")
    print("=" * 60)
    print(f"\n应用配置：")
    print(f"  主机地址: {config.app.get('host')}")
    print(f"  端口: {config.app.get('port')}")
    print(f"  调试模式: {config.app.get('debug')}")
    
    print(f"\n登录配置：")
    print(f"  启用登录: {config.is_login_enabled()}")
    print(f"  用户数量: {len(config.get_users())}")
    
    print(f"\n生成器配置：")
    print(f"  最大生成数量: {config.generator.get('max_count')}")
    print(f"  批次大小: {config.generator.get('batch_size')}")
    print(f"  文件大小限制: {config.generator.get('file_size_limit')} MB")
    
    print(f"\n数据库配置：")
    print(f"  数据库路径: {config.get_database_path()}")
    print(f"  CSV路径: {config.get_csv_path()}")
    
    print(f"\n下载配置：")
    print(f"  下载目录: {config.get_download_dir()}")
    print(f"  文件过期时间: {config.download.get('expire_hours')} 小时")
    
    print(f"\n日志配置：")
    print(f"  日志级别: {config.logging.get('level')}")
    print(f"  日志文件: {config.get_log_file()}")
    
    print("\n" + "=" * 60)
