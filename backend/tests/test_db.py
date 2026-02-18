#!/usr/bin/env python3
"""
测试数据库连接
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text

from models.database import get_engine, get_session_local

try:
    engine = get_engine()
    print(f"数据库引擎: {engine}")

    # 测试连接
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(f"连接测试成功: {result.fetchone()}")

    # 测试会话
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        print("数据库会话创建成功")
    finally:
        db.close()

    print("数据库连接测试成功")
except Exception as e:
    print(f"数据库连接测试失败: {e}")
    import traceback

    traceback.print_exc()
