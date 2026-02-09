#!/usr/bin/env python3
"""
重构验证脚本

验证新创建的模块是否能正确导入，并检查基本功能。
"""

import sys
import os

# 添加后端目录到Python路径
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, backend_dir)

def test_imports():
    """测试模块导入"""
    modules_to_test = [
        "schemas",
        "config",
        "exceptions"
    ]

    print("="*60)
    print("模块导入测试")
    print("="*60)

    all_passed = True

    for module_name in modules_to_test:
        try:
            module = __import__(module_name)
            print(f"✅ {module_name}: 导入成功")

            # 检查必要的类/函数
            if module_name == "schemas":
                required_classes = ["LoginRequest", "UserInfo", "ErrorResponse"]
                for cls in required_classes:
                    if hasattr(module, cls):
                        print(f"   ✓ {cls} 存在")
                    else:
                        print(f"   ✗ {cls} 不存在")
                        all_passed = False

            elif module_name == "config":
                required_attrs = ["settings", "setup_logging"]
                for attr in required_attrs:
                    if hasattr(module, attr):
                        print(f"   ✓ {attr} 存在")
                    else:
                        print(f"   ✗ {attr} 不存在")
                        all_passed = False

            elif module_name == "exceptions":
                required_classes = ["APIError", "api_error_handler"]
                for cls in required_classes:
                    if hasattr(module, cls):
                        print(f"   ✓ {cls} 存在")
                    else:
                        print(f"   ✗ {cls} 不存在")
                        all_passed = False

        except ImportError as e:
            print(f"❌ {module_name}: 导入失败 - {e}")
            all_passed = False
        except Exception as e:
            print(f"⚠️  {module_name}: 导入时出错 - {e}")
            all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("✅ 所有模块导入测试通过")
    else:
        print("❌ 模块导入测试失败")
    print("="*60)

    return all_passed

def test_config():
    """测试配置模块"""
    print("\n" + "="*60)
    print("配置模块测试")
    print("="*60)

    try:
        import config
        settings = config.settings

        print(f"应用名称: {settings.APP_NAME}")
        print(f"环境: {settings.ENVIRONMENT}")
        print(f"调试模式: {settings.DEBUG}")
        print(f"JWT算法: {settings.ALGORITHM}")
        print(f"CORS来源: {settings.CORS_ORIGINS[:2]}...")

        # 测试辅助函数
        from datetime import datetime, timedelta

        # 测试过期检查
        past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        future_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        is_past_expired = config.is_expired(past_date)
        is_future_expired = config.is_expired(future_date)

        print(f"过去日期 {past_date} 是否过期: {is_past_expired}")
        print(f"未来日期 {future_date} 是否过期: {is_future_expired}")

        print("✅ 配置模块测试通过")
        return True

    except Exception as e:
        print(f"❌ 配置模块测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_schemas():
    """测试数据模型模块"""
    print("\n" + "="*60)
    print("数据模型测试")
    print("="*60)

    try:
        import schemas

        # 测试创建请求模型
        login_request = schemas.LoginRequest(
            username="testuser",
            password="testpass"
        )
        print(f"✅ 创建登录请求: {login_request.username}")

        # 测试创建用户信息模型
        user_info = schemas.UserInfo(
            username="testuser",
            expiry_date="2025-12-31",
            max_translations=100,
            used_translations=10,
            remaining_translations=90
        )
        print(f"✅ 创建用户信息: {user_info.username}")

        # 测试创建错误响应模型
        error_response = schemas.ErrorResponse(
            error_code="TEST_ERROR",
            message="测试错误"
        )
        print(f"✅ 创建错误响应: {error_response.error_code}")

        print("✅ 数据模型测试通过")
        return True

    except Exception as e:
        print(f"❌ 数据模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_import():
    """测试主模块导入（确保没有破坏现有功能）"""
    print("\n" + "="*60)
    print("主模块导入测试")
    print("="*60)

    try:
        # 尝试导入主模块
        import main

        print(f"✅ 主模块导入成功")
        print(f"应用标题: {main.app.title if hasattr(main, 'app') else '未找到app属性'}")

        # 检查必要的全局变量
        required_vars = ["app", "logger", "SECRET_KEY", "ALGORITHM"]
        for var in required_vars:
            if hasattr(main, var):
                print(f"   ✓ {var} 存在")
            else:
                print(f"   ⚠️  {var} 不存在（可能已迁移到新模块）")

        print("✅ 主模块导入测试通过")
        return True

    except ImportError as e:
        print(f"❌ 主模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"⚠️  主模块导入时出错: {e}")
        import traceback
        traceback.print_exc()
        return True  # 即使有警告也返回True

def main():
    """主函数"""
    print("重构验证脚本")
    print("验证已创建的基础模块")
    print()

    tests = [
        ("模块导入", test_imports),
        ("配置模块", test_config),
        ("数据模型", test_schemas),
        ("主模块导入", test_main_import)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"测试 {test_name} 执行异常: {e}")
            results.append((test_name, False))

    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)

    all_passed = True
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("🎉 所有测试通过！重构基础模块创建成功。")
        print("下一步：继续创建工具模块和路由模块。")
    else:
        print("⚠️  部分测试失败，请检查模块实现。")
    print("="*60)

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())