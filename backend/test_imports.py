#!/usr/bin/env python3
"""
测试所有关键模块的导入，确保没有语法错误。
"""

print("测试关键模块导入...")
print("=" * 60)

# 测试1: 基础导入
try:
    import hashlib
    import json
    import logging

    print("[OK] 基础模块导入成功")
except ImportError as e:
    print(f"[FAIL] 基础模块导入失败: {e}")

# 测试2: 数据库相关导入
try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    print("[OK] SQLAlchemy导入成功")
except ImportError as e:
    print(f"[FAIL] SQLAlchemy导入失败: {e}")
    print("请运行: pip install sqlalchemy")

try:
    import psycopg2

    print("[OK] psycopg2导入成功")
except ImportError as e:
    print(f"[FAIL] psycopg2导入失败: {e}")
    print("请运行: pip install psycopg2-binary")

try:
    import alembic

    print("[OK] alembic导入成功")
except ImportError as e:
    print(f"[FAIL] alembic导入失败: {e}")
    print("请运行: pip install alembic")

# 测试3: 自定义模块导入
try:
    from config import settings

    print("[OK] config.settings导入成功")
except ImportError as e:
    print(f"[FAIL] config.settings导入失败: {e}")

try:
    from models.database import get_database_url

    print("[OK] models.database导入成功")
except ImportError as e:
    print(f"[FAIL] models.database导入失败: {e}")

try:
    from services.user_service import UserService

    print("[OK] services.user_service导入成功")
except ImportError as e:
    print(f"[FAIL] services.user_service导入失败: {e}")

try:
    from utils import CacheManager, RateLimiter, TextValidator

    print("[OK] utils模块导入成功")
except ImportError as e:
    print(f"[FAIL] utils模块导入失败: {e}")

try:
    from schemas import CheckTextRequest, LoginRequest

    print("[OK] schemas模块导入成功")
except ImportError as e:
    print(f"[FAIL] schemas模块导入失败: {e}")

try:
    from exceptions import APIError

    print("[OK] exceptions模块导入成功")
except ImportError as e:
    print(f"[FAIL] exceptions模块导入失败: {e}")

try:
    from prompts import build_error_check_prompt

    print("[OK] prompts模块导入成功")
except ImportError as e:
    print(f"[FAIL] prompts模块导入失败: {e}")

# 测试4: FastAPI相关
try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    print("[OK] FastAPI导入成功")
except ImportError as e:
    print(f"[FAIL] FastAPI导入失败: {e}")
    print("请运行: pip install fastapi")

print("=" * 60)
print("导入测试完成！")
