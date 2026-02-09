#!/usr/bin/env python3
"""
数据库初始化脚本
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # 导入数据库模块
    from models.database import init_database, ensure_admin_user_exists

    print("正在初始化数据库...")
    init_database()
    print("数据库表创建完成")

    print("确保管理员用户存在...")
    ensure_admin_user_exists()
    print("管理员用户已创建/更新")

    print("数据库初始化成功完成")
except Exception as e:
    print(f"数据库初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)