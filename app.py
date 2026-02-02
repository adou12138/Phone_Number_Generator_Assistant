# -*- coding: utf-8 -*-
"""
手机号码生成查询系统 - Flask主应用

本应用提供一个Web界面，允许用户根据筛选条件生成手机号码，
并将结果导出为.txt文件下载。

功能模块：
- 用户认证：支持配置开关的登录功能
- 号码生成：根据条件生成符合要求的手机号码
- 文件导出：支持单个文件和分批下载
- 数据库查询：高效的SQLite查询

使用方法：
    python app.py              # 启动应用（默认端口5000）
    python app.py --port 8080  # 指定端口启动

作者：Phone Number Generator
版本：1.0.0
"""

import os
import sys
import sqlite3
import logging
import uuid
import time
import json
from datetime import datetime
from pathlib import Path
from functools import wraps
from multiprocessing import Pool, cpu_count
from typing import List, Dict, Any, Optional, Tuple

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, Response

# 导入配置模块
from config import config


# ===========================================
# Flask应用初始化
# ===========================================

def create_app() -> Flask:
    """
    创建并配置Flask应用
    
    这是应用工厂函数，负责创建Flask实例并加载所有配置。
    
    返回：
        Flask: 配置完成的Flask应用实例
    """
    # 创建Flask应用实例
    app = Flask(__name__)
    
    # 加载配置
    app_config = config.get_app_config()
    for key, value in app_config.items():
        app.config[key] = value
    
    # 配置会话密钥
    app.secret_key = config.app.get('secret_key', 'default-secret-key')
    
    # 配置上传文件夹和下载文件夹
    download_dir = config.get_download_dir()
    app.config['DOWNLOAD_FOLDER'] = download_dir
    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 最大500MB
    
    # 确保下载目录存在
    os.makedirs(download_dir, exist_ok=True)
    
    # 配置日志
    log_file = config.get_log_file()
    from logging.handlers import TimedRotatingFileHandler
    
    # 按天分割日志，只保存2天
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when='midnight',  # 每天午夜分割
        interval=1,       # 每1天分割一次
        backupCount=2,    # 只保存2天的日志
        encoding='utf-8'
    )
    
    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # 配置日志
    logging.basicConfig(
        level=getattr(logging, config.logging.get('level', 'INFO')),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            file_handler,
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Flask应用初始化完成")
    
    return app


# 创建Flask应用实例
app = create_app()


# ===========================================
# 数据库操作模块
# ===========================================

class DatabaseManager:
    """
    数据库管理器
    
    负责管理与SQLite数据库的连接和查询操作。
    
    功能：
    - 数据库连接管理
    - 执行查询操作
    - 获取省份和城市列表
    """
    
    def __init__(self):
        """
        初始化数据库管理器
        """
        self.db_path = config.get_database_path()
    
    def get_connection(self) -> sqlite3.Connection:
        """
        获取数据库连接
        
        返回：
            sqlite3.Connection: 数据库连接对象
        """
        print(f"数据库路径: {self.db_path}")
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使用列名访问数据
        return conn
    
    def execute_query(self, query: str, params: Tuple = None) -> List[sqlite3.Row]:
        """
        执行查询语句
        
        参数：
            query: SQL查询语句
            params: 查询参数（元组）
        
        返回：
            List[sqlite3.Row]: 查询结果列表
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            results = cursor.fetchall()
            return [dict(row) for row in results]
        finally:
            conn.close()
    
    def query_phone_locations(self, prefix: str, province: str, city: str, 
                              operators: List[int] = None) -> List[Dict[str, Any]]:
        """
        查询符合条件的电话号码归属地信息
        
        参数：
            prefix: 手机号前3位号段
            province: 省份
            city: 城市
            operators: 运营商列表
        
        返回：
            List[Dict]: 符合条件的归属地记录列表
        """
        # 构建查询条件
        conditions = ["prefix = ?", "province = ?", "city = ?"]
        params = [prefix, province, city]
        
        # 添加运营商筛选条件
        if operators and len(operators) > 0:
            placeholders = ','.join(['?'] * len(operators))
            conditions.append(f"operator IN ({placeholders})")
            params.extend(operators)
        
        # 组合查询条件
        where_clause = ' AND '.join(conditions)
        query = f"SELECT prefix, suffix, province, city, operator FROM phone_location WHERE {where_clause}"
        
        return self.execute_query(query, tuple(params))
    
    def get_provinces(self) -> List[str]:
        """
        获取所有省份列表
        返回： List[str]: 省份名称列表
        """
        print(f"数据库路径: {self.db_path}")
        query = "SELECT DISTINCT province FROM phone_location ORDER BY province"
        results = self.execute_query(query)

        return [row['province'] for row in results]
    
    def get_cities(self, province: str) -> List[str]:
        """
        获取指定省份的城市列表
        参数： province: 省份名称
        返回：List[str]: 城市名称列表
        """
        print(f"数据库路径: {self.db_path}")
        print(f"查询省份: {province}")
        logging.info(f"数据库路径: {self.db_path}")
        logging.info(f"查询省份: {province}")
        query = "SELECT DISTINCT city FROM phone_location WHERE province = ? ORDER BY city"
        results = self.execute_query(query, (province,))
        return [row['city'] for row in results]


# 创建数据库管理器实例
db_manager = DatabaseManager()


# ===========================================
# 号码生成模块
# ===========================================

class NumberGenerator:
    """
    号码生成器
    
    负责根据条件生成手机号码，支持多进程并行生成。
    
    生成逻辑：
    1. 从数据库查询符合条件的号段信息
    2. 组合完整的11位手机号码
    3. 支持多进程并行生成提高效率
    4. 分批次写入文件，避免内存溢出
    """
    
    def __init__(self):
        """
        初始化号码生成器
        """
        self.batch_size = config.generator.get('batch_size', 500)
        self.max_count = config.generator.get('max_count', 10000000)
        self.file_size_limit = config.generator.get('file_size_limit', 20)  # MB
    
    def generate_numbers(self, prefix: str, suffix: str = None, 
                         suffix_3: str = None, province: str = None,
                         city: str = None, operators: List[int] = None) -> List[str]:
        """
        生成符合条件的手机号码列表
        
        参数：
            prefix: 手机号前3位号段
            suffix: 手机号最后4位（精确匹配）
            suffix_3: 手机号最后3位（精确匹配）
            province: 省份
            city: 城市
            operators: 运营商列表
        
        返回：
            List[str]: 生成的手机号码列表
        """
        # 查询符合条件的号段信息
        locations = db_manager.query_phone_locations(prefix, province, city, operators)
        
        if not locations:
            return []
        
        # 生成所有号码
        all_numbers = []
        for location in locations:
            numbers = self._generate_numbers_for_location(
                prefix, location['suffix'], suffix, suffix_3
            )
            all_numbers.extend(numbers)
        
        # 去重并排序
        all_numbers = list(set(all_numbers))
        all_numbers.sort()
        
        return all_numbers
    
    def _generate_numbers_for_location(self, prefix: str, suffix: str, 
                                        suffix_4: str = None, 
                                        suffix_3: str = None) -> List[str]:
        """
        为单个归属地生成手机号码
        
        参数：
            prefix: 号段（前3位）
            suffix: 区域码（4位）
            suffix_4: 后4位（精确匹配）
            suffix_3: 后3位（精确匹配）
        
        返回：
            List[str]: 生成的手机号码列表
        """
        numbers = []
        
        if suffix_4:
            # 精确匹配后4位
            full_number = prefix + suffix + suffix_4
            numbers.append(full_number)
        elif suffix_3:
            # 精确匹配后3位
            # 后4位的第一位可以是0-9
            for first_digit in '0123456789':
                full_number = prefix + suffix + first_digit + suffix_3
                numbers.append(full_number)
        else:
            # 生成所有可能的号码
            # 中间4位（suffix）+ 最后4位（0000-9999）
            for last_four in range(10000):
                last_four_str = str(last_four).zfill(4)
                full_number = prefix + suffix + last_four_str
                numbers.append(full_number)
        
        return numbers
    
    def generate_to_file(self, numbers: List[str], filename: str) -> Tuple[str, int, str]:
        """
        将号码列表写入文件
        
        参数：
            numbers: 手机号码列表
            filename: 文件名
        
        返回：
            Tuple[str, int, str]: (文件名, 文件大小字节, 文件大小显示)
        """
        filepath = os.path.join(config.get_download_dir(), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for number in numbers:
                f.write(number + '\n')
        
        # 获取文件大小
        file_size = os.path.getsize(filepath)
        file_size_str = self._format_file_size(file_size)
        
        return filename, file_size, file_size_str
    
    def _format_file_size(self, size: int) -> str:
        """
        格式化文件大小显示
        
        参数：
            size: 文件大小（字节）
        
        返回：
            str: 格式化后的大小字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"


# 创建号码生成器实例
number_generator = NumberGenerator()


# ===========================================
# 文件管理模块
# ===========================================

class FileManager:
    """
    文件管理器
    
    负责管理生成的文件，包括分批处理和清理过期文件。
    """
    
    def __init__(self):
        """
        初始化文件管理器
        """
        self.download_dir = config.get_download_dir()
        self.expire_hours = config.download.get('expire_hours', 24)
    
    def cleanup_expired_files(self) -> int:
        """
        清理过期文件
        
        删除超过过期时间的临时文件。
        
        返回：
            int: 删除的文件数量
        """
        if not os.path.exists(self.download_dir):
            return 0
        
        current_time = time.time()
        expire_seconds = self.expire_hours * 3600
        deleted_count = 0
        
        for filename in os.listdir(self.download_dir):
            filepath = os.path.join(self.download_dir, filename)
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > expire_seconds:
                    try:
                        os.remove(filepath)
                        deleted_count += 1
                    except Exception:
                        pass
        
        return deleted_count
    
    def split_file_for_download(self, filename: str, max_size_mb: int = 20) -> List[Dict[str, str]]:
        """
        拆分大文件为多个小文件
        
        参数：
            filename: 原始文件名
            max_size_mb: 每个小文件的最大大小（MB）
        
        返回：
            List[Dict]: 拆分后的文件信息列表
        """
        filepath = os.path.join(self.download_dir, filename)
        if not os.path.exists(filepath):
            return []
        
        # 获取文件大小
        file_size = os.path.getsize(filepath)
        if file_size <= max_size_mb * 1024 * 1024:
            # 文件小于限制，不需要拆分
            file_size_str = number_generator._format_file_size(file_size)
            return [{
                'name': filename,
                'size': file_size_str,
                'url': f"/download/{filename}"
            }]
        
        # 拆分文件
        max_size = max_size_mb * 1024 * 1024
        part_files = []
        part_number = 1
        
        with open(filepath, 'r', encoding='utf-8') as f:
            while True:
                lines = []
                current_size = 0
                
                # 读取一批数据
                for _ in range(500000):  # 约50万条
                    line = f.readline()
                    if not line:
                        break
                    lines.append(line)
                    current_size += len(line.encode('utf-8'))
                    
                    if current_size >= max_size:
                        break
                
                if not lines:
                    break
                
                # 写入分片文件
                part_filename = f"part_{part_number}_{filename}"
                part_filepath = os.path.join(self.download_dir, part_filename)
                
                with open(part_filepath, 'w', encoding='utf-8') as part_file:
                    part_file.writelines(lines)
                
                # 获取文件大小
                part_size = os.path.getsize(part_filepath)
                part_size_str = number_generator._format_file_size(part_size)
                
                part_files.append({
                    'name': part_filename,
                    'size': part_size_str,
                    'url': f"/download/{part_filename}"
                })
                
                part_number += 1
        
        return part_files


# 创建文件管理器实例
file_manager = FileManager()


# ===========================================
# 辅助函数
# ===========================================

def login_required(f):
    """
    登录验证装饰器
    
    用于保护需要登录才能访问的路由。
    如果登录功能未启用，则跳过验证。
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 如果登录功能未启用，直接执行函数
        if not config.is_login_enabled():
            return f(*args, **kwargs)
        
        # 检查是否已登录
        if not session.get('logged_in'):
            return redirect(url_for('login_page'))
        
        return f(*args, **kwargs)
    return decorated_function


def validate_input(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    验证用户输入
    
    参数：
        data: 用户提交的数据字典
    
    返回：
        Tuple[bool, str]: (验证是否通过, 错误信息)
    """
    # 验证必填字段
    prefix = str(data.get('prefix', '')).strip()
    if not prefix:
        return False, "请输入手机号前3位号段"
    
    if len(prefix) != 3 or not prefix.isdigit():
        return False, "号段必须为3位数字"
    
    # 验证省份和城市（必填）
    province = str(data.get('province', '')).strip()
    if not province:
        return False, "请选择省份"
    
    city = str(data.get('city', '')).strip()
    if not city:
        return False, "请选择城市"
    
    # 验证后3/4位（互斥）
    suffix_4 = data.get('suffix_4')
    suffix_3 = data.get('suffix_3')
    
    # 处理null值
    suffix_4 = suffix_4.strip() if suffix_4 and isinstance(suffix_4, str) else ''
    suffix_3 = suffix_3.strip() if suffix_3 and isinstance(suffix_3, str) else ''
    
    if suffix_4 and suffix_3:
        return False, "后3位和后4位只能填写其一"
    
    if suffix_4:
        if len(suffix_4) != 4 or not suffix_4.isdigit():
            return False, "后4位必须为4位数字"
    
    if suffix_3:
        if len(suffix_3) != 3 or not suffix_3.isdigit():
            return False, "后3位必须为3位数字"
    
    # 验证运营商
    operators = data.get('operators', [])
    if operators:
        valid_operators = [1, 2, 3, 4, 5]
        for op in operators:
            if op not in valid_operators:
                return False, f"无效的运营商类型：{op}"
    
    return True, ""


def generate_filename(prefix: str, province: str, city: str, 
                      suffix: str, extension: str = 'txt') -> str:
    """
        生成文件名
        
        命名格式：{前3位}_{省份}_{城市}_{后缀}_{时间戳}.{扩展名}
        
        参数：
            prefix: 号段
            province: 省份
            city: 城市
            suffix: 后缀（后3/4位）
            extension: 文件扩展名
        
        返回：
            str: 生成的文件名
        """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 清理特殊字符
    province = province.replace('/', '_').replace('\\', '_')
    city = city.replace('/', '_').replace('\\', '_')
    
    filename = f"{prefix}_{province}_{city}_{suffix}_{timestamp}.{extension}"
    return filename


# ===========================================
# 路由定义
# ===========================================

@app.route('/')
@login_required
def index_page():
    """
    首页/查询页面
    
    渲染查询表单页面。
    如果登录功能启用且用户未登录，则重定向到登录页。
    """
    # 获取省份列表
    provinces = db_manager.get_provinces()
    return render_template('index.html', provinces=provinces)


@app.route('/login')
def login_page():
    """
    登录页面
    
    渲染登录表单页面。
    如果登录功能未启用，重定向到首页。
    """
    # 如果登录功能未启用，重定向到首页
    if not config.is_login_enabled():
        return redirect(url_for('index_page'))
    
    # 如果已登录，重定向到首页
    if session.get('logged_in'):
        return redirect(url_for('index_page'))
    
    return render_template('login.html')


@app.route('/api/login', methods=['POST'])
def api_login():
    """
    登录API
    
    处理用户登录请求。
    
    请求参数：
        username: 用户名
        password: 密码
    
    返回：
        JSON: 登录结果
    """
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    # 验证登录凭证
    if config.validate_login(username, password):
        session['logged_in'] = True
        session['username'] = username
        return jsonify({
            'code': 200,
            'message': '登录成功',
            'redirect_url': url_for('index_page')
        })
    else:
        return jsonify({
            'code': 401,
            'message': '用户名或密码错误'
        }), 401


@app.route('/api/logout')
def api_logout():
    """
    退出登录API
    
    处理用户退出登录请求。
    """
    session.clear()
    return redirect(url_for('login_page'))


@app.route('/api/provinces')
@login_required
def api_provinces():
    """
    获取省份列表API
    
    返回所有可用的省份列表。
    
    返回：
        JSON: 省份列表
    """
    provinces = db_manager.get_provinces()
    return jsonify({
        'code': 200,
        'data': provinces
    })


@app.route('/api/cities/<province>')
@login_required
def api_cities(province: str):
    """
    获取城市列表API
    返回指定省份的城市列表
    参数：province: 省份名称
    返回：JSON: 城市列表
    """
    cities = db_manager.get_cities(province)
    return jsonify({
        'code': 200,
        'data': cities
    })


@app.route('/api/generate', methods=['POST'])
@login_required
def api_generate():
    """
    生成号码API
    
    根据用户输入的条件生成手机号码，并返回下载链接。
    
    请求参数：
        prefix: 手机号前3位号段（必填）
        suffix_4: 手机号最后4位（选填）
        suffix_3: 手机号最后3位（选填）
        province: 省份（必填）
        city: 城市（必填）
        operators: 运营商列表（选填）
    
    返回：
        JSON: 生成结果和下载链接
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        # 验证输入
        valid, error_msg = validate_input(data)
        if not valid:
            return jsonify({
                'code': 400,
                'message': error_msg
            }), 400
        
        # 提取参数
        prefix = str(data.get('prefix', '')).strip()
        # 修复：先检查是否为 None，再转换为字符串
        suffix_4_raw = data.get('suffix_4')
        suffix_3_raw = data.get('suffix_3')
        suffix_4 = str(suffix_4_raw).strip() if suffix_4_raw and str(suffix_4_raw).strip() else ''
        suffix_3 = str(suffix_3_raw).strip() if suffix_3_raw and str(suffix_3_raw).strip() else ''
        province = str(data.get('province', '')).strip()
        city = str(data.get('city', '')).strip()
        operators = data.get('operators', [])
        
        # 生成号码
        numbers = number_generator.generate_numbers(
            prefix=prefix,
            suffix=suffix_4 or None,
            suffix_3=suffix_3 or None,
            province=province,
            city=city,
            operators=operators if operators else None
        )
        
        if not numbers:
            return jsonify({
                'code': 404,
                'message': '未找到符合条件的号码'
            }), 404
        
        # 检查是否超过最大生成数量
        if len(numbers) > number_generator.max_count:
            return jsonify({
                'code': 400,
                'message': f'查询结果超过限制（最多{number_generator.max_count}条），请缩小查询范围'
            }), 400
        
        # 确定后缀
        suffix = suffix_4 or suffix_3 or 'ALL'
        
        # 生成文件名
        filename = generate_filename(prefix, province, city, suffix)
        
        # 写入文件
        actual_filename, file_size, file_size_str = number_generator.generate_to_file(numbers, filename)
        
        # 检查是否需要分批
        file_path = os.path.join(config.get_download_dir(), actual_filename)
        file_size_bytes = os.path.getsize(file_path)
        
        if file_size_bytes > number_generator.file_size_limit * 1024 * 1024:
            # 需要分批
            files = file_manager.split_file_for_download(actual_filename)
        else:
            files = [{
                'name': actual_filename,
                'size': file_size_str,
                'url': f"/download/{actual_filename}"
            }]
        
        return jsonify({
            'code': 200,
            'message': '生成成功',
            'data': {
                'count': len(numbers),
                'files': files
            }
        })
        
    except Exception as e:
        logging.error(f"生成号码时发生错误：{str(e)}")
        return jsonify({
            'code': 500,
            'message': f'生成失败：{str(e)}'
        }), 500


@app.route('/download/<filename>')
@login_required
def download_file(filename: str):
    """
    下载文件API
    
    提供文件下载功能。
    
    参数：
        filename: 文件名
    
    返回：
        文件下载响应
    """
    filepath = os.path.join(config.get_download_dir(), filename)
    
    if not os.path.exists(filepath):
        return jsonify({
            'code': 404,
            'message': '文件不存在或已过期'
        }), 404
    
    # 生成下载响应
    return send_file(
        filepath,
        as_attachment=True,
        download_name=filename,
        mimetype='text/plain'
    )


@app.route('/api/cleanup', methods=['POST'])
@login_required
def api_cleanup():
    """
    清理过期文件API
    
    手动触发清理过期文件。
    
    返回：
        JSON: 清理结果
    """
    try:
        deleted_count = file_manager.cleanup_expired_files()
        return jsonify({
            'code': 200,
            'message': f'已清理 {deleted_count} 个过期文件'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'清理失败：{str(e)}'
        }), 500


# ===========================================
# 错误处理
# ===========================================

@app.errorhandler(400)
def bad_request(error):
    """
    400错误处理
    """
    return jsonify({
        'code': 400,
        'message': '请求无效'
    }), 400


@app.errorhandler(404)
def not_found(error):
    """
    404错误处理
    """
    return jsonify({
        'code': 404,
        'message': '页面不存在'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """
    500错误处理
    """
    logging.error(f"服务器内部错误：{str(error)}")
    return jsonify({
        'code': 500,
        'message': '服务器内部错误'
    }), 500


# ===========================================
# 主程序入口
# ===========================================

def init_database():
    """
    初始化数据库
    
    在应用启动时检查并初始化数据库。
    """
    try:
        from final_import import DataImporter
        importer = DataImporter()
        
        # 检查数据状态
        status = importer.check_status()
        
        if not status['csv_exists']:
            logging.warning(f"CSV文件不存在：{status['csv_path']}")
            logging.warning("请确保phone_location.csv文件存在于data目录中")
            return
        
        # 无论数据库是否存在或表是否完整，都尝试导入数据
        # 这样可以确保表结构正确创建
        logging.info("开始初始化数据库...")
        importer.import_data()
        
    except Exception as e:
        logging.error(f"初始化数据库失败：{str(e)}")


def main():
    """
    主函数
    
    启动Flask应用。
    """
    # 初始化数据库
    init_database()
    
    # 获取配置
    host = config.app.get('host', '0.0.0.0')
    port = config.app.get('port', 5000)
    debug = config.app.get('debug', False)
    
    print("=" * 60)
    print("手机号码生成查询系统")
    print("=" * 60)
    print(f"\n启动参数：")
    print(f"  地址: {host}")
    print(f"  端口: {port}")
    print(f"  调试模式: {'开启' if debug else '关闭'}")
    print(f"\n登录功能: {'启用' if config.is_login_enabled() else '禁用'}")
    print(f"数据库: {config.get_database_path()}")
    print(f"下载目录: {config.get_download_dir()}")
    print("\n" + "-" * 60)
    print("启动服务中...")
    
    # 启动应用
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()
