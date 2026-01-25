# -*- coding: utf-8 -*-
"""
CSV数据导入SQLite数据库脚本

本脚本用于将phone_location.csv文件中的电话号码归属地数据
导入到SQLite数据库中。

功能说明：
- 支持自动检测文件编码（UTF-8、GBK、GB18030等）
- 自动检测是否需要导入（数据库已存在且有数据则跳过）
- 批量插入数据库，提高导入效率
- 创建索引优化查询性能
- 提供便捷函数 import_csv_to_database() 供其他模块调用

使用方法（命令行）：
    python final_import.py              # 自动模式（检测是否需要导入）
    python final_import.py --force      # 强制重新导入
    python final_import.py --check      # 仅检查数据状态

使用方法（代码中）：
    from final_import import import_csv_to_database
    import_csv_to_database()            # 导入CSV数据到数据库

作者：Phone Number Generator
版本：2.0.0
"""

import csv
import sqlite3
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any


def detect_encoding(file_path: str) -> str:
    """
    检测文件的文本编码
    
    通过读取文件前几个字节来检测文件的实际编码格式。
    支持UTF-8、GBK、GB2312、GB18030等常见中文编码。
    
    参数：
        file_path: 文件路径
    
    返回：
        str: 检测到的编码名称
    """
    import chardet
    
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)
        
        result = chardet.detect(raw_data)
        encoding = result.get('encoding', 'utf-8')
        confidence = result.get('confidence', 0)
        
        if confidence < 0.5 or encoding is None:
            for enc in ['utf-8', 'gbk', 'gb18030']:
                try:
                    raw_data.decode(enc)
                    return enc
                except UnicodeDecodeError:
                    continue
            return 'latin-1'
        
        return encoding if encoding else 'utf-8'
        
    except Exception as e:
        print(f"  警告：编码检测失败，使用默认编码。错误：{e}")
        return 'utf-8'


class DataImporter:
    """
    数据导入类
    
    负责将CSV文件中的电话号码归属地数据导入SQLite数据库。
    
    属性：
        csv_file: CSV文件路径
        db_file: 数据库文件路径
        conn: 数据库连接
        cursor: 数据库游标
    """
    
    def __init__(self, csv_file: str = 'phone_location.csv', db_file: str = 'phone_location.db'):
        """
        初始化数据导入类
        
        参数：
            csv_file: CSV文件路径
            db_file: 数据库文件路径
        """
        self.csv_file = csv_file
        self.db_file = db_file
        
        script_dir = Path(__file__).parent
        print(f"脚本所在目录：{script_dir}")
        self.project_root = script_dir
        print(f"项目根目录：{self.project_root}")
        
        # 确保data目录存在
        data_dir = self.project_root / 'data'
        data_dir.mkdir(exist_ok=True)
        
        # 将CSV和数据库文件放在data目录下
        self.csv_path = data_dir / csv_file
        self.db_path = data_dir / db_file
        
        self.conn = None
        self.cursor = None
    
    def get_csv_path(self) -> str:
        """获取CSV文件的完整路径"""
        return str(self.csv_path)
    
    def get_db_path(self) -> str:
        """获取数据库文件的完整路径"""
        return str(self.db_path)
    
    def check_csv_exists(self) -> bool:
        """检查CSV文件是否存在"""
        return self.csv_path.exists()
    
    def check_db_exists(self) -> bool:
        """检查数据库文件是否存在"""
        return self.db_path.exists()
    
    def get_db_record_count(self) -> int:
        """获取数据库中的记录数量"""
        if not self.check_db_exists():
            return 0
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM phone_location')
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception:
            return 0
    
    def connect_database(self) -> bool:
        """连接SQLite数据库"""
        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self.cursor = self.conn.cursor()
            print(f"✓ 成功连接数据库：{self.db_path}")
            return True
        except Exception as e:
            print(f"✗ 数据库连接失败：{e}")
            return False
    
    def close_database(self) -> None:
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            print("✓ 数据库连接已关闭")
    
    def create_table(self) -> bool:
        """创建数据库表结构"""
        create_table_sql = '''
        CREATE TABLE IF NOT EXISTS phone_location (
            prefix TEXT NOT NULL,
            suffix TEXT NOT NULL,
            province TEXT NOT NULL,
            city TEXT NOT NULL,
            operator INTEGER NOT NULL
        )
        '''
        
        try:
            self.cursor.execute(create_table_sql)
            print("✓ 数据库表结构创建成功")
            return True
        except Exception as e:
            print(f"✗ 创建表结构失败：{e}")
            return False
    
    def create_indexes(self) -> bool:
        """创建数据库索引"""
        try:
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_prefix ON phone_location(prefix)')
            print("✓ 成功创建索引：idx_prefix（号段前缀）")
            
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_province_city ON phone_location(province, city)')
            print("✓ 成功创建索引：idx_province_city（省份+城市）")
            
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_operator ON phone_location(operator)')
            print("✓ 成功创建索引：idx_operator（运营商类型）")
            
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_prefix_province_city ON phone_location(prefix, province, city)')
            print("✓ 成功创建索引：idx_prefix_province_city（组合查询）")
            
            return True
        except Exception as e:
            print(f"✗ 创建索引失败：{e}")
            return False
    
    def import_data(self, force: bool = False) -> bool:
        """
        导入CSV数据到数据库
        
        参数：
            force: 是否强制重新导入，默认为False
        
        返回：
            bool: 导入成功返回True，失败返回False
        """
        if not self.check_csv_exists():
            print(f"✗ 错误：CSV文件 {self.get_csv_path()} 不存在")
            return False
        
        print(f"✓ 找到CSV文件：{self.get_csv_path()}")
        
        if not force and self.check_db_exists():
            record_count = self.get_db_record_count()
            if record_count > 0:
                print(f"✓ 数据库已存在，包含 {record_count} 条记录，跳过导入")
                print("  如需重新导入，请使用 --force 参数")
                return True
        
        if not self.connect_database():
            return False
        
        if not self.create_table():
            self.close_database()
            return False
        
        if force and self.check_db_exists():
            try:
                self.cursor.execute('DELETE FROM phone_location')
                self.conn.commit()
                print("✓ 已清空现有数据")
            except Exception as e:
                print(f"✗ 清空数据失败：{e}")
        
        if not self.create_indexes():
            self.close_database()
            return False
        
        return self._read_and_import_csv()
    
    def _read_and_import_csv(self) -> bool:
        """读取CSV文件并导入数据"""
        insert_count = 0
        skipped_count = 0
        
        try:
            encoding = detect_encoding(self.csv_path)
            print(f"✓ 检测到文件编码：{encoding}")
            
            with open(self.csv_path, 'r', encoding=encoding) as f:
                reader = csv.reader(f)
                
                try:
                    header = next(reader)
                    print(f"✓ 跳过标题行：{header}")
                except StopIteration:
                    print("✗ CSV文件为空")
                    return False
                
                data_batch = []
                batch_size = 1000
                
                for line_num, row in enumerate(reader, start=2):
                    if len(row) == 5:
                        data_batch.append(row)
                        insert_count += 1
                        
                        if len(data_batch) >= batch_size:
                            self._batch_insert(data_batch)
                            data_batch = []
                            print(f"  已导入 {insert_count} 条数据")
                    else:
                        skipped_count += 1
                
                if data_batch:
                    self._batch_insert(data_batch)
                    print(f"  已导入 {insert_count} 条数据")
            
            self.conn.commit()
            print(f"\n✓ 数据导入完成：共导入 {insert_count} 条，跳过 {skipped_count} 条")
            
            final_count = self.get_db_record_count()
            print(f"✓ 数据库中总共有 {final_count} 条记录")
            
            self.close_database()
            return True
            
        except Exception as e:
            print(f"✗ 数据导入失败：{e}")
            if self.conn:
                self.conn.rollback()
            self.close_database()
            return False
    
    def _batch_insert(self, data_batch: list) -> None:
        """批量插入数据"""
        insert_sql = '''
        INSERT INTO phone_location (prefix, suffix, province, city, operator) 
        VALUES (?, ?, ?, ?, ?)
        '''
        self.cursor.executemany(insert_sql, data_batch)
    
    def check_status(self) -> Dict[str, Any]:
        """检查数据状态"""
        return {
            'csv_exists': self.check_csv_exists(),
            'db_exists': self.check_db_exists(),
            'db_record_count': self.get_db_record_count(),
            'csv_path': self.get_csv_path(),
            'db_path': self.get_db_path()
        }


def import_csv_to_database(csv_file_path: str = None, db_file_path: str = None, force: bool = False) -> bool:
    """
    导入CSV数据到数据库的便捷函数
    
    该函数封装了DataImporter类的功能，提供简单的导入接口。
    
    参数：
        csv_file_path: CSV文件路径，默认为 'phone_location.csv'
        db_file_path: 数据库文件路径，默认为 'phone_location.db'
        force: 是否强制重新导入，默认为False
    
    返回：
        bool: 导入成功返回True，失败返回False
    
    使用示例：
        from final_import import import_csv_to_database
        
        # 自动模式（检测是否需要导入）
        result = import_csv_to_database()
        
        # 强制重新导入
        result = import_csv_to_database(force=True)
        
        # 指定文件路径
        result = import_csv_to_database(
            csv_file_path='data/phone_location.csv',
            db_file_path='data/phone_location.db',
            force=True
        )
    """
    importer = DataImporter(csv_file_path or 'phone_location.csv', db_file_path or 'phone_location.db')
    return importer.import_data(force=force)


def main():
    """
    主函数
    
    解析命令行参数，执行相应的导入操作。
    """
    parser = argparse.ArgumentParser(
        description='将CSV数据导入SQLite数据库',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
    python final_import.py              # 自动模式
    python final_import.py --force      # 强制重新导入
    python final_import.py --check      # 仅检查状态

说明：
    - 自动模式下，如果数据库已存在且有数据，则跳过导入
    - 使用 --force 参数可以强制重新导入所有数据
        """
    )
    
    parser.add_argument('--force', action='store_true', help='强制重新导入数据')
    parser.add_argument('--check', action='store_true', help='仅检查当前数据状态')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("手机号码归属地数据导入工具")
    print("=" * 60)
    
    importer = DataImporter()
    
    if args.check:
        status = importer.check_status()
        print("=" * 60)
        print("数据状态检查")
        print("=" * 60)
        print(f"\nCSV文件：")
        print(f"  路径：{status['csv_path']}")
        print(f"  存在：{'是' if status['csv_exists'] else '否'}")
        print(f"\n数据库文件：")
        print(f"  路径：{status['db_path']}")
        print(f"  存在：{'是' if status['db_exists'] else '否'}")
        print(f"  记录数：{status['db_record_count']} 条")
        print("=" * 60)
        return 0
    
    print(f"\n开始导入数据...")
    print(f"CSV文件：{importer.get_csv_path()}")
    print(f"数据库：{importer.get_db_path()}")
    print("-" * 60)
    print(f"模式：{'强制重新导入' if args.force else '自动（检测是否需要导入）'}")
    print("-" * 60)
    
    success = importer.import_data(force=args.force)
    
    print("\n" + "=" * 60)
    if success:
        print("导入执行完成！")
    else:
        print("导入执行失败，请检查错误信息。")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == '__main__':
    # sys.exit(main())
    import_csv_to_database()
