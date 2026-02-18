#!/usr/bin/env python3
"""
测试用户认证流程，模拟API调用。
"""

import os
import sys
from datetime import datetime

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient

from main import app

# 创建测试客户端
client = TestClient(app)

print("测试用户认证流程...")
print("=" * 60)

# 测试1: 获取健康检查
print("\n[TEST] 健康检查端点")
try:
    response = client.get("/api/health")
    print(f"  状态码: {response.status_code}")
    print(f"  响应: {response.json()}")
    if response.status_code == 200:
        print("  [OK] 健康检查通过")
    else:
        print("  [FAIL] 健康检查失败")
except Exception as e:
    print(f"  [FAIL] 健康检查异常: {e}")

# 测试2: 管理员登录
print("\n[TEST] 管理员登录")
try:
    from config import settings

    login_data = {"username": "admin", "password": settings.ADMIN_PASSWORD}  # 从配置读取密码
    response = client.post("/api/login", json=login_data)
    print(f"  状态码: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        admin_token = result.get("token")
        print("  [OK] 管理员登录成功")
        print(f"  令牌: {admin_token[:20]}...")

        # 保存令牌供后续测试使用
        if admin_token:
            # 测试3: 使用令牌获取用户信息
            print("\n[TEST] 获取管理员用户信息")
            headers = {"Authorization": f"Bearer {admin_token}"}
            response = client.get("/api/user/info", headers=headers)
            print(f"  状态码: {response.status_code}")

            if response.status_code == 200:
                user_info = response.json()
                print("  [OK] 获取用户信息成功")
                print(f"  用户名: {user_info.get('username')}")
                print(f"  角色: {user_info.get('role')}")
                print(f"  剩余翻译次数: {user_info.get('remaining_translations')}")
            else:
                print(f"  [FAIL] 获取用户信息失败: {response.json()}")
    else:
        print(f"  [FAIL] 管理员登录失败: {response.json()}")
except Exception as e:
    print(f"  [FAIL] 管理员登录测试异常: {e}")

# 测试4: 测试添加用户（需要管理员权限）
print("\n[TEST] 添加新用户（需要管理员令牌）")
try:
    # 首先需要获取管理员令牌（简化测试，使用环境变量）
    from config import settings

    # 创建测试用户数据
    test_user_data = {
        "username": f"test_user_{datetime.now().strftime('%H%M%S')}",
        "password": "test123",
        "expiry_date": "2026-12-31",
        "max_translations": 100,
    }

    print(f"  测试用户: {test_user_data['username']}")

    # 注意：实际API需要管理员认证，这里我们只是测试UserService
    from user_services.user_service import UserService

    user_service = UserService()

    success, message = user_service.add_user(
        test_user_data["username"],
        test_user_data["password"],
        test_user_data["expiry_date"],
        test_user_data["max_translations"],
    )

    if success:
        print(f"  [OK] 添加用户成功: {message}")

        # 测试5: 验证新用户
        print("\n[TEST] 验证新用户登录")
        allowed, auth_message = user_service.authenticate_user(
            test_user_data["username"], test_user_data["password"]
        )

        if allowed:
            print(f"  [OK] 用户验证成功: {auth_message}")

            # 测试6: 获取新用户信息
            user_info = user_service.get_user_info(test_user_data["username"])
            if user_info:
                print("  [OK] 获取用户信息成功")
                print(f"  过期日期: {user_info.get('expiry_date')}")
                print(f"  最大翻译次数: {user_info.get('max_translations')}")
                print(f"  剩余翻译次数: {user_info.get('remaining_translations')}")
            else:
                print("  [FAIL] 获取用户信息失败")
        else:
            print(f"  [FAIL] 用户验证失败: {auth_message}")
    else:
        print(f"  [FAIL] 添加用户失败: {message}")

except Exception as e:
    print(f"  [FAIL] 添加用户测试异常: {e}")
    import traceback

    traceback.print_exc()

# 测试7: 测试错误密码
print("\n[TEST] 测试错误密码验证")
try:
    from user_services.user_service import UserService

    user_service = UserService()

    allowed, message = user_service.authenticate_user("admin", "wrong_password")

    if not allowed:
        print(f"  [OK] 错误密码验证失败（预期行为）: {message}")
    else:
        print("  [FAIL] 错误密码验证不应该成功")

except Exception as e:
    print(f"  [FAIL] 错误密码测试异常: {e}")

# 测试8: 测试不存在的用户
print("\n[TEST] 测试不存在的用户")
try:
    from user_services.user_service import UserService

    user_service = UserService()

    allowed, message = user_service.authenticate_user("non_existent_user_12345", "password")

    if not allowed:
        print(f"  [OK] 不存在的用户验证失败（预期行为）: {message}")
    else:
        print("  [FAIL] 不存在的用户验证不应该成功")

except Exception as e:
    print(f"  [FAIL] 不存在的用户测试异常: {e}")

print("\n" + "=" * 60)
print("用户认证流程测试完成!")
print("=" * 60)
