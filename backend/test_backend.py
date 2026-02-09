#!/usr/bin/env python3
"""
测试后端基本功能，包括数据库初始化和简单API调用。
"""

import sys
import os
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print("测试后端基本功能...")
print("=" * 60)

# 测试1: 初始化数据库
try:
    from models.database import init_database, get_session_local
    print("[TEST] 初始化数据库...")
    init_database()
    print("[OK] 数据库初始化成功")
except Exception as e:
    print(f"[FAIL] 数据库初始化失败: {e}")
    import traceback
    traceback.print_exc()

# 测试2: 创建UserService实例
try:
    from user_services.user_service import UserService
    print("\n[TEST] 创建UserService实例...")
    user_service = UserService()
    print("[OK] UserService创建成功")
except Exception as e:
    print(f"[FAIL] UserService创建失败: {e}")
    import traceback
    traceback.print_exc()

# 测试3: 测试数据库连接和查询
try:
    print("\n[TEST] 测试数据库连接...")
    SessionLocal = get_session_local()
    db = SessionLocal()

    # 查询用户数量
    from models.database import User
    user_count = db.query(User).count()
    print(f"[OK] 数据库连接成功，当前用户数: {user_count}")

    # 检查管理员用户
    from config import settings
    admin_user = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
    if admin_user:
        print(f"[OK] 管理员用户存在: {admin_user.username}")
    else:
        print("[WARNING] 管理员用户不存在")

    db.close()
except Exception as e:
    print(f"[FAIL] 数据库连接测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试4: 测试FastAPI应用创建
try:
    print("\n[TEST] 创建FastAPI应用...")
    from fastapi import FastAPI
    from main import app  # 导入主应用

    # 检查应用的路由
    routes = [route.path for route in app.routes]
    print(f"[OK] FastAPI应用创建成功，路由数量: {len(routes)}")
    print(f"[INFO] 主要路由: {[r for r in routes if '/api/' in r][:5]}...")
except Exception as e:
    print(f"[FAIL] FastAPI应用测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试5: 测试配置
try:
    print("\n[TEST] 测试配置...")
    from config import settings

    print(f"[OK] 应用名称: {settings.APP_NAME}")
    print(f"[OK] 环境: {settings.ENVIRONMENT}")
    print(f"[OK] 数据库类型: {settings.DATABASE_TYPE}")

    if settings.DATABASE_TYPE == "sqlite":
        print(f"[OK] SQLite路径: {settings.DATABASE_PATH}")
    else:
        print(f"[OK] PostgreSQL URL: {settings.DATABASE_URL[:30]}...")

except Exception as e:
    print(f"[FAIL] 配置测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("后端基本功能测试完成!")
print("=" * 60)