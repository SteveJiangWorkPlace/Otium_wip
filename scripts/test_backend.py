#!/usr/bin/env python3
"""
后端健康检查脚本

测试后端服务是否可以正常工作：
1. 检查FastAPI应用是否运行
2. 测试健康端点
3. 测试数据库连接
4. 验证基本功能

使用说明：
python scripts/test_backend.py
"""

import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("[错误] 缺少requests库，请运行: pip install requests")
    sys.exit(1)

# 基础配置
BASE_URL = "http://localhost:8000"
HEALTH_URL = f"{BASE_URL}/api/health"
LOGIN_URL = f"{BASE_URL}/api/login"

# 默认管理员账户
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# 超时设置
TIMEOUT = 30  # 秒


def safe_print(message):
    """安全打印，处理Windows编码问题"""
    try:
        print(message)
    except UnicodeEncodeError:
        # 在Windows命令行（GBK编码）下处理Unicode字符
        print(message.encode("utf-8", errors="replace").decode("gbk", errors="replace"))


def test_health_endpoint():
    """测试健康端点"""
    safe_print("\n" + "=" * 60)
    safe_print("1. 测试健康端点")
    safe_print("=" * 60)

    try:
        response = requests.get(HEALTH_URL, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()

        safe_print("[成功] 健康端点响应正常")
        safe_print(f"    状态: {data.get('status', '未知')}")
        safe_print(f"    环境: {data.get('environment', '未知')}")
        safe_print(f"    数据库: {data.get('database', '未知')}")
        safe_print(f"    版本: {data.get('version', '未知')}")

        return True
    except requests.exceptions.ConnectionError:
        safe_print("[失败] 无法连接到后端服务")
        safe_print(
            "      请确保后端正在运行: uvicorn main:app --reload --host 0.0.0.0 --port 8000"
        )
        return False
    except requests.exceptions.Timeout:
        safe_print("[失败] 连接超时")
        return False
    except requests.exceptions.RequestException as e:
        safe_print(f"[失败] 请求异常: {e}")
        return False
    except Exception as e:
        safe_print(f"[失败] 未知错误: {e}")
        return False


def test_database_connection():
    """测试数据库连接（通过登录功能间接测试）"""
    safe_print("\n" + "=" * 60)
    safe_print("2. 测试数据库连接")
    safe_print("=" * 60)

    try:
        payload = {"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        response = requests.post(LOGIN_URL, json=payload, timeout=TIMEOUT)

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                safe_print("[成功] 数据库连接正常，管理员登录成功")
                safe_print(f"    令牌长度: {len(token)} 字符")
                safe_print(f"    用户: {data.get('username', '未知')}")
                safe_print(f"    角色: {data.get('role', '未知')}")
                return True, token
            else:
                safe_print("[警告] 登录成功但没有返回令牌")
                return False, None
        elif response.status_code == 401:
            safe_print("[失败] 管理员账户认证失败")
            safe_print("      默认管理员账户: admin/admin123")
            safe_print("      请检查数据库中的管理员账户或运行:")
            safe_print(
                '      python -c "from models.database import ensure_admin_user_exists; ensure_admin_user_exists()"'
            )
            return False, None
        else:
            safe_print(f"[失败] 登录请求返回异常状态码: {response.status_code}")
            safe_print(f"      响应: {response.text[:200]}")
            return False, None
    except requests.exceptions.RequestException as e:
        safe_print(f"[失败] 数据库连接测试请求异常: {e}")
        return False, None
    except Exception as e:
        safe_print(f"[失败] 数据库连接测试未知错误: {e}")
        return False, None


def test_basic_api_functions(token):
    """测试基本API功能"""
    safe_print("\n" + "=" * 60)
    safe_print("3. 测试基本API功能")
    safe_print("=" * 60)

    if not token:
        safe_print("[跳过] 无有效令牌，跳过API功能测试")
        return False

    test_text = "这是一个测试文本，用于验证后端API是否正常工作。"
    CHECK_TEXT_URL = f"{BASE_URL}/api/text/check"

    headers = {"Authorization": f"Bearer {token}"}
    payload = {"text": test_text, "operation": "error_check", "version": "basic"}

    try:
        safe_print("[信息] 发送智能纠错测试请求...")
        start_time = time.time()
        response = requests.post(
            CHECK_TEXT_URL, json=payload, headers=headers, timeout=60
        )
        elapsed_time = time.time() - start_time

        if response.status_code == 200:
            safe_print(f"[成功] API功能正常，响应时间: {elapsed_time:.2f}秒")
            safe_print(f"    状态码: {response.status_code}")

            # 检查响应结构
            try:
                data = response.json()
                if isinstance(data, dict):
                    if "corrected_text" in data:
                        safe_print(
                            f"    返回纠正文本长度: {len(data['corrected_text'])} 字符"
                        )
                    elif "result" in data:
                        safe_print(f"    返回结果长度: {len(data['result'])} 字符")
                    else:
                        safe_print(f"    响应包含字段: {list(data.keys())}")
                else:
                    safe_print(f"    响应类型: {type(data)}")
            except:
                safe_print("    响应格式非JSON")

            return True
        else:
            safe_print(f"[失败] API返回错误状态码: {response.status_code}")
            safe_print(f"      响应: {response.text[:500]}")
            return False
    except requests.exceptions.Timeout:
        safe_print("[失败] API请求超时（60秒）")
        return False
    except requests.exceptions.RequestException as e:
        safe_print(f"[失败] API请求异常: {e}")
        return False
    except Exception as e:
        safe_print(f"[失败] API测试未知错误: {e}")
        return False


def check_backend_dependencies():
    """检查后端依赖"""
    safe_print("\n" + "=" * 60)
    safe_print("4. 检查后端依赖")
    safe_print("=" * 60)

    backend_dir = Path(__file__).parent.parent / "backend"
    requirements_file = backend_dir / "requirements.txt"

    if not requirements_file.exists():
        safe_print("[警告] 未找到requirements.txt文件")
        return False

    try:
        with open(requirements_file, "r", encoding="utf-8") as f:
            requirements = [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]

        safe_print(f"[信息] 找到 {len(requirements)} 个依赖项")

        # 检查关键依赖
        critical_deps = ["fastapi", "uvicorn", "sqlalchemy", "pydantic", "requests"]
        missing_deps = []

        for dep in critical_deps:
            if not any(dep in req.lower() for req in requirements):
                missing_deps.append(dep)

        if missing_deps:
            safe_print(f"[警告] 缺少关键依赖: {', '.join(missing_deps)}")
            safe_print("      请运行: pip install -r backend/requirements.txt")
            return False
        else:
            safe_print("[成功] 关键依赖检查通过")
            return True
    except Exception as e:
        safe_print(f"[失败] 依赖检查错误: {e}")
        return False


def main():
    """主测试函数"""
    safe_print("=" * 80)
    safe_print("后端健康检查测试")
    safe_print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    safe_print(f"后端地址: {BASE_URL}")
    safe_print("=" * 80)

    # 测试结果汇总
    test_results = []

    # 1. 测试健康端点
    health_ok = test_health_endpoint()
    test_results.append(("健康端点", health_ok))

    # 2. 测试数据库连接
    db_ok, token = test_database_connection()
    test_results.append(("数据库连接", db_ok))

    # 3. 测试基本API功能
    if db_ok and token:
        api_ok = test_basic_api_functions(token)
        test_results.append(("API功能", api_ok))
    else:
        safe_print("\n[信息] 由于数据库连接失败，跳过API功能测试")
        test_results.append(("API功能", False))

    # 4. 检查后端依赖
    deps_ok = check_backend_dependencies()
    test_results.append(("依赖检查", deps_ok))

    # 总结报告
    safe_print("\n" + "=" * 80)
    safe_print("测试总结报告")
    safe_print("=" * 80)

    total_tests = len(test_results)
    passed_tests = sum(1 for _, success in test_results if success)

    safe_print(f"\n测试总数: {total_tests}")
    safe_print(f"通过测试: {passed_tests}")
    safe_print(f"失败测试: {total_tests - passed_tests}")

    safe_print("\n详细结果:")
    for test_name, success in test_results:
        status = "[通过]" if success else "[失败]"
        safe_print(f"  {test_name}: {status}")

    if passed_tests == total_tests:
        safe_print("\n[成功] 所有测试通过！后端服务正常运行。")
        safe_print("\n启动命令:")
        safe_print("  cd backend")
        safe_print("  uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    else:
        safe_print(f"\n[警告] {total_tests - passed_tests} 个测试失败")
        safe_print("\n故障排除建议:")
        safe_print("1. 确保后端服务正在运行")
        safe_print("2. 检查端口8000是否被占用")
        safe_print("3. 验证数据库配置")
        safe_print("4. 检查API密钥和环境变量")
        sys.exit(1)


if __name__ == "__main__":
    main()
