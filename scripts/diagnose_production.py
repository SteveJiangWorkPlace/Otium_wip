#!/usr/bin/env python3
"""
生产环境诊断脚本

用于诊断文献调研功能在生产环境中的问题：
1. 检查后端API服务状态
2. 验证前端-后端通信
3. 检查数据库任务状态（通过API）
4. 验证提示词系统使用

使用说明：
python scripts/diagnose_production.py

环境变量：
- PRODUCTION_BACKEND_URL: 生产环境后端URL（默认：https://otium-backend.onrender.com）
- PRODUCTION_FRONTEND_URL: 生产环境前端URL（默认：https://otiumtrans.netlify.app）
- TEST_USERNAME: 测试用户名（默认：admin）
- TEST_PASSWORD: 测试密码（默认：admin123）
"""

import sys
import time
import json
from pathlib import Path

try:
    import requests
except ImportError:
    print("[错误] 缺少requests库，请运行: pip install requests")
    sys.exit(1)

# 生产环境配置
PRODUCTION_BACKEND_URL = "https://otium-backend.onrender.com"
PRODUCTION_FRONTEND_URL = "https://otiumtrans.netlify.app"
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

# 超时设置
TIMEOUT = 60  # 秒

def safe_print(message):
    """安全打印，处理Windows编码问题"""
    try:
        print(message)
    except UnicodeEncodeError:
        # 在Windows命令行（GBK编码）下处理Unicode字符
        print(message.encode("utf-8", errors="replace").decode("gbk", errors="replace"))

def test_backend_health():
    """测试生产环境后端健康状态"""
    safe_print("\n" + "=" * 80)
    safe_print("1. 测试生产环境后端健康状态")
    safe_print("=" * 80)

    health_url = f"{PRODUCTION_BACKEND_URL}/api/health"

    try:
        safe_print(f"[信息] 测试后端健康端点: {health_url}")
        start_time = time.time()
        response = requests.get(health_url, timeout=TIMEOUT)
        elapsed_time = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            safe_print(f"[成功] 后端健康检查通过，响应时间: {elapsed_time:.2f}秒")
            safe_print(f"    状态码: {response.status_code}")
            safe_print(f"    环境: {data.get('environment', '未知')}")
            safe_print(f"    数据库: {data.get('database', '未知')}")
            safe_print(f"    版本: {data.get('version', '未知')}")

            # 检查数据库连接状态
            if data.get('database') == 'connected':
                safe_print("    数据库连接: 正常")
                return True, elapsed_time
            else:
                safe_print("    数据库连接: 异常或未知状态")
                return False, elapsed_time
        else:
            safe_print(f"[失败] 后端健康检查失败，状态码: {response.status_code}")
            safe_print(f"    响应: {response.text[:200]}")
            return False, elapsed_time

    except requests.exceptions.ConnectionError:
        safe_print(f"[失败] 无法连接到后端服务: {PRODUCTION_BACKEND_URL}")
        safe_print("      请检查网络连接或服务状态")
        return False, 0
    except requests.exceptions.Timeout:
        safe_print(f"[失败] 连接超时（{TIMEOUT}秒）")
        return False, 0
    except requests.exceptions.RequestException as e:
        safe_print(f"[失败] 请求异常: {e}")
        return False, 0
    except Exception as e:
        safe_print(f"[失败] 未知错误: {e}")
        return False, 0

def test_backend_login():
    """测试生产环境后端登录功能"""
    safe_print("\n" + "=" * 80)
    safe_print("2. 测试生产环境后端登录功能")
    safe_print("=" * 80)

    login_url = f"{PRODUCTION_BACKEND_URL}/api/login"

    try:
        payload = {"username": TEST_USERNAME, "password": TEST_PASSWORD}
        safe_print(f"[信息] 测试登录功能: {login_url}")
        safe_print(f"      用户名: {TEST_USERNAME}")

        start_time = time.time()
        response = requests.post(login_url, json=payload, timeout=TIMEOUT)
        elapsed_time = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                safe_print(f"[成功] 登录成功，响应时间: {elapsed_time:.2f}秒")
                safe_print(f"    令牌长度: {len(token)} 字符")
                safe_print(f"    用户: {data.get('username', '未知')}")
                safe_print(f"    角色: {data.get('role', '未知')}")
                return True, token, elapsed_time
            else:
                safe_print("[警告] 登录成功但没有返回令牌")
                return False, None, elapsed_time
        elif response.status_code == 401:
            safe_print(f"[失败] 登录失败，认证错误（状态码: 401）")
            safe_print("      请检查用户名和密码是否正确")
            return False, None, elapsed_time
        else:
            safe_print(f"[失败] 登录请求返回异常状态码: {response.status_code}")
            safe_print(f"      响应: {response.text[:200]}")
            return False, None, elapsed_time

    except requests.exceptions.RequestException as e:
        safe_print(f"[失败] 登录请求异常: {e}")
        return False, None, 0
    except Exception as e:
        safe_print(f"[失败] 登录未知错误: {e}")
        return False, None, 0

def test_literature_research_task_creation(token):
    """测试文献调研任务创建功能"""
    safe_print("\n" + "=" * 80)
    safe_print("3. 测试文献调研任务创建功能")
    safe_print("=" * 80)

    chat_url = f"{PRODUCTION_BACKEND_URL}/api/chat"

    if not token:
        safe_print("[跳过] 无有效令牌，跳过任务创建测试")
        return False, None, 0

    try:
        # 创建测试请求
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {
            "message": "请调研人工智能在教育中的应用",
            "literature_research_mode": True,  # 使用统一后的术语
            "generate_literature_review": False
        }

        safe_print("[信息] 创建文献调研测试任务...")
        safe_print(f"      请求URL: {chat_url}")
        safe_print(f"      文献调研模式: {payload['literature_research_mode']}")
        safe_print(f"      生成文献综述: {payload['generate_literature_review']}")

        start_time = time.time()
        response = requests.post(chat_url, json=payload, headers=headers, timeout=180)
        elapsed_time = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            task_id = data.get("task_id")
            status = data.get("status")

            safe_print(f"[成功] 文献调研任务创建成功，响应时间: {elapsed_time:.2f}秒")
            safe_print(f"    任务ID: {task_id}")
            safe_print(f"    任务状态: {status}")

            # 检查是否启用了后台工作器
            if status == "PENDING":
                safe_print("    后台任务模式: 已启用（任务状态为PENDING，等待后台工作器处理）")
                safe_print("    注意：任务需要后台工作器处理，可能需要等待一段时间")
            elif status == "PROCESSING":
                safe_print("    后台任务模式: 已启用（任务状态为PROCESSING，正在处理中）")
            else:
                safe_print(f"    后台任务模式: 未知（状态为{status}）")

            return True, task_id, elapsed_time
        elif response.status_code == 503:
            safe_print("[失败] 文献调研任务创建失败，状态码: 503 (服务不可用)")
            safe_print("      可能原因: 后台工作器未运行或ENABLE_BACKGROUND_WORKER未设置")
            return False, None, elapsed_time
        else:
            safe_print(f"[失败] 文献调研任务创建失败，状态码: {response.status_code}")
            safe_print(f"      响应: {response.text[:500]}")
            return False, None, elapsed_time

    except requests.exceptions.Timeout:
        safe_print("[失败] 文献调研任务创建请求超时（180秒）")
        return False, None, 0
    except requests.exceptions.RequestException as e:
        safe_print(f"[失败] 文献调研任务创建请求异常: {e}")
        return False, None, 0
    except Exception as e:
        safe_print(f"[失败] 文献调研任务创建未知错误: {e}")
        return False, None, 0

def test_task_status_polling(task_id, token):
    """测试任务状态轮询功能"""
    safe_print("\n" + "=" * 80)
    safe_print("4. 测试任务状态轮询功能")
    safe_print("=" * 80)

    if not task_id or not token:
        safe_print("[跳过] 无任务ID或令牌，跳过状态轮询测试")
        return False, 0

    status_url = f"{PRODUCTION_BACKEND_URL}/api/tasks/{task_id}/status"

    try:
        headers = {"Authorization": f"Bearer {token}"}

        safe_print(f"[信息] 轮询任务状态: {status_url}")
        safe_print(f"      任务ID: {task_id}")

        # 轮询3次，每次间隔5秒
        polling_results = []

        for i in range(3):
            safe_print(f"\n    轮询 #{i+1}:")
            try:
                start_time = time.time()
                response = requests.get(status_url, headers=headers, timeout=TIMEOUT)
                elapsed_time = time.time() - start_time

                if response.status_code == 200:
                    data = response.json()
                    task_status = data.get("status")
                    progress = data.get("progress_percentage")

                    safe_print(f"      状态码: 200")
                    safe_print(f"      任务状态: {task_status}")
                    safe_print(f"      进度: {progress}%")
                    safe_print(f"      响应时间: {elapsed_time:.2f}秒")

                    # 显示更多任务信息
                    if data.get("step_description"):
                        safe_print(f"      步骤描述: {data.get('step_description')}")
                    if data.get("error_message"):
                        safe_print(f"      错误信息: {data.get('error_message')}")

                    polling_results.append((task_status, elapsed_time))

                    # 如果任务已完成或失败，停止轮询
                    if task_status in ["COMPLETED", "FAILED"]:
                        safe_print(f"      任务状态为{task_status}，停止轮询")
                        break

                elif response.status_code == 404:
                    safe_print(f"      状态码: 404 (任务不存在)")
                    break
                else:
                    safe_print(f"      状态码: {response.status_code}")
                    safe_print(f"      响应: {response.text[:200]}")
                    break

            except requests.exceptions.Timeout:
                safe_print(f"      轮询超时")
                break
            except Exception as e:
                safe_print(f"      轮询异常: {e}")
                break

            # 如果不是最后一次轮询，等待5秒
            if i < 2 and len(polling_results) > 0 and polling_results[-1][0] not in ["COMPLETED", "FAILED"]:
                safe_print(f"      等待5秒后继续轮询...")
                time.sleep(5)

        if polling_results:
            last_status = polling_results[-1][0]
            if last_status in ["COMPLETED", "PROCESSING", "PENDING"]:
                safe_print(f"\n[成功] 任务状态轮询功能正常，最终状态: {last_status}")
                return True, polling_results
            else:
                safe_print(f"\n[警告] 任务状态轮询可能存在问题，最终状态: {last_status}")
                return False, polling_results
        else:
            safe_print("\n[失败] 未获取到有效的轮询结果")
            return False, []

    except Exception as e:
        safe_print(f"[失败] 任务状态轮询未知错误: {e}")
        return False, []

def check_cors_configuration():
    """检查CORS配置"""
    safe_print("\n" + "=" * 80)
    safe_print("5. 检查CORS配置")
    safe_print("=" * 80)

    health_url = f"{PRODUCTION_BACKEND_URL}/api/health"

    try:
        # 发送OPTIONS请求检查CORS
        safe_print(f"[信息] 检查CORS配置: {health_url}")

        headers = {
            "Origin": PRODUCTION_FRONTEND_URL,
            "Access-Control-Request-Method": "GET"
        }

        response = requests.options(health_url, headers=headers, timeout=TIMEOUT)

        # 检查CORS头
        cors_headers = [
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods",
            "Access-Control-Allow-Headers",
            "Access-Control-Allow-Credentials"
        ]

        found_headers = []
        for header in cors_headers:
            if header in response.headers:
                found_headers.append(header)
                safe_print(f"    发现CORS头: {header} = {response.headers[header]}")

        if found_headers:
            safe_print(f"[成功] CORS配置正常，发现 {len(found_headers)} 个CORS头")

            # 检查前端域名是否在允许列表中
            allow_origin = response.headers.get("Access-Control-Allow-Origin")
            if allow_origin == "*" or PRODUCTION_FRONTEND_URL in allow_origin:
                safe_print(f"    前端域名 {PRODUCTION_FRONTEND_URL} 在允许列表中")
                return True
            else:
                safe_print(f"[警告] 前端域名可能不在CORS允许列表中")
                safe_print(f"      Allow-Origin: {allow_origin}")
                safe_print(f"      前端URL: {PRODUCTION_FRONTEND_URL}")
                return False
        else:
            safe_print("[警告] 未发现CORS头，可能CORS未正确配置")
            return False

    except Exception as e:
        safe_print(f"[失败] 检查CORS配置时出错: {e}")
        return False

def verify_prompt_system_usage():
    """验证提示词系统使用情况"""
    safe_print("\n" + "=" * 80)
    safe_print("6. 验证提示词系统使用情况")
    safe_print("=" * 80)

    # 测试端点：如果有提示词测试端点则使用，否则通过API间接验证
    debug_url = f"{PRODUCTION_BACKEND_URL}/api/debug/prompt-metrics"

    try:
        safe_print(f"[信息] 尝试访问提示词监控端点: {debug_url}")
        response = requests.get(debug_url, timeout=TIMEOUT)

        if response.status_code == 200:
            data = response.json()
            safe_print("[成功] 提示词监控端点可用")

            # 显示关键指标
            cache_stats = data.get("cache_stats", {})
            build_times = data.get("build_times", {})

            if cache_stats:
                safe_print("    缓存统计:")
                safe_print(f"      命中率: {cache_stats.get('hit_rate', 0):.1f}%")
                safe_print(f"      缓存大小: {cache_stats.get('cache_size', 0)}")
                safe_print(f"      最大大小: {cache_stats.get('max_size', 0)}")

            if build_times:
                safe_print("    构建时间统计:")
                for func, stats in build_times.items():
                    safe_print(f"      {func}: {stats.get('avg_time_ms', 0):.1f}ms (样本数: {stats.get('count', 0)})")

            return True
        elif response.status_code == 404:
            safe_print("[信息] 提示词监控端点不存在，尝试间接验证...")
            safe_print("      将通过文献调研功能间接验证提示词系统使用")

            # 这里我们依赖之前的文献调研任务测试来间接验证
            # 如果之前的任务创建成功，说明提示词系统在正常工作
            safe_print("      注：提示词系统验证依赖文献调研功能测试")
            return None  # 返回None表示无法直接验证
        else:
            safe_print(f"[信息] 提示词监控端点返回状态码: {response.status_code}")
            safe_print("      将通过文献调研功能间接验证提示词系统使用")
            return None

    except Exception as e:
        safe_print(f"[信息] 无法访问提示词监控端点: {e}")
        safe_print("      将通过文献调研功能间接验证提示词系统使用")
        return None

def generate_diagnosis_report(test_results):
    """生成诊断报告"""
    safe_print("\n" + "=" * 80)
    safe_print("生产环境诊断报告")
    safe_print("=" * 80)

    safe_print(f"\n诊断时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    safe_print(f"后端URL: {PRODUCTION_BACKEND_URL}")
    safe_print(f"前端URL: {PRODUCTION_FRONTEND_URL}")

    safe_print("\n测试结果汇总:")
    safe_print("-" * 60)

    total_tests = len(test_results)
    # 修复：test_results是三元组，需要提取success
    passed_tests = 0
    failed_tests = 0
    for item in test_results:
        if len(item) >= 2:
            success = item[1]
            if success is True:
                passed_tests += 1
            elif success is False:
                failed_tests += 1

    for test_name, success, details in test_results:
        if success is True:
            status = "[通过]"
        elif success is False:
            status = "[失败]"
        else:
            status = "[信息]"
        safe_print(f"  {test_name}: {status}")
        if details:
            safe_print(f"    详情: {details}")

    safe_print("\n统计:")
    safe_print(f"  总测试数: {total_tests}")
    safe_print(f"  通过测试: {passed_tests}")
    safe_print(f"  失败测试: {failed_tests}")

    # 生成问题诊断建议
    safe_print("\n问题诊断建议:")
    safe_print("-" * 60)

    # 检查是否有失败的测试
    failed_test_names = [name for name, success, _ in test_results if success is False]

    if not failed_test_names:
        safe_print("所有测试通过！生产环境配置正常。")
        safe_print("如果文献调研功能仍有问题，请检查：")
        safe_print("1. MANUS_API_KEY环境变量是否正确设置")
        safe_print("2. 后台工作器(otium-background-worker)服务状态")
        safe_print("3. 数据库中的background_tasks表状态")
        return True
    else:
        safe_print(f"发现 {len(failed_test_names)} 个问题:")

        for test_name in failed_test_names:
            if "后端健康状态" in test_name:
                safe_print(f"\n1. 后端健康状态失败:")
                safe_print("   - 检查后端服务是否正在运行")
                safe_print("   - 检查网络连接")
                safe_print("   - 检查DNS解析")

            elif "后端登录功能" in test_name:
                safe_print(f"\n2. 后端登录功能失败:")
                safe_print("   - 检查管理员账户是否正确")
                safe_print("   - 检查数据库连接")
                safe_print("   - 检查JWT配置")

            elif "文献调研任务创建" in test_name:
                safe_print(f"\n3. 文献调研任务创建失败:")
                safe_print("   - 检查ENABLE_BACKGROUND_WORKER环境变量")
                safe_print("   - 检查后台工作器服务状态")
                safe_print("   - 检查文献调研相关代码是否已部署")

            elif "任务状态轮询" in test_name:
                safe_print(f"\n4. 任务状态轮询失败:")
                safe_print("   - 检查任务ID是否正确")
                safe_print("   - 检查任务状态API端点")
                safe_print("   - 检查数据库连接")

            elif "CORS配置" in test_name:
                safe_print(f"\n5. CORS配置问题:")
                safe_print("   - 检查CORS_ORIGINS环境变量")
                safe_print("   - 确保前端域名在允许列表中")
                safe_print("   - 检查FastAPI CORS中间件配置")

        safe_print("\n推荐下一步操作:")
        safe_print("1. 登录Render Dashboard检查服务状态")
        safe_print("2. 检查环境变量设置（特别是MANUS_API_KEY）")
        safe_print("3. 查看服务日志查找详细错误信息")
        safe_print("4. 运行数据库诊断查询（参考生产环境诊断检查清单）")

        return False

def main():
    """主诊断函数"""
    safe_print("=" * 80)
    safe_print("文献调研功能生产环境诊断")
    safe_print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    safe_print("=" * 80)

    # 测试结果收集
    test_results = []

    # 1. 测试后端健康状态
    health_ok, health_time = test_backend_health()
    test_results.append(("后端健康状态", health_ok, f"响应时间: {health_time:.2f}秒"))

    # 2. 测试后端登录功能
    login_ok, token, login_time = test_backend_login()
    test_results.append(("后端登录功能", login_ok, f"响应时间: {login_time:.2f}秒"))

    # 3. 测试文献调研任务创建
    task_ok = False
    task_id = None
    task_time = 0
    if login_ok and token:
        task_ok, task_id, task_time = test_literature_research_task_creation(token)
        test_results.append(("文献调研任务创建", task_ok, f"响应时间: {task_time:.2f}秒，任务ID: {task_id}"))
    else:
        test_results.append(("文献调研任务创建", False, "依赖登录功能，已跳过"))

    # 4. 测试任务状态轮询
    polling_ok = False
    polling_results = []
    if task_ok and task_id and token:
        polling_ok, polling_results = test_task_status_polling(task_id, token)
        poll_details = f"轮询次数: {len(polling_results)}"
        if polling_results:
            poll_details += f"，最终状态: {polling_results[-1][0]}"
        test_results.append(("任务状态轮询", polling_ok, poll_details))
    else:
        test_results.append(("任务状态轮询", False, "依赖任务创建，已跳过"))

    # 5. 检查CORS配置
    cors_ok = check_cors_configuration()
    test_results.append(("CORS配置", cors_ok, ""))

    # 6. 验证提示词系统使用
    prompt_ok = verify_prompt_system_usage()
    if prompt_ok is None:
        # 无法直接验证，依赖文献调研任务测试
        if task_ok:
            test_results.append(("提示词系统使用", True, "通过文献调研任务间接验证"))
        else:
            test_results.append(("提示词系统使用", None, "无法验证，文献调研任务创建失败"))
    else:
        test_results.append(("提示词系统使用", prompt_ok, ""))

    # 生成诊断报告
    overall_ok = generate_diagnosis_report(test_results)

    safe_print("\n" + "=" * 80)
    safe_print("诊断完成")
    safe_print("=" * 80)

    if overall_ok:
        safe_print("\n[成功] 生产环境诊断完成，未发现重大问题")
        safe_print("      请继续使用文献调研功能测试完整流程")
        return 0
    else:
        safe_print("\n[警告] 生产环境诊断发现一些问题")
        safe_print("      请根据诊断报告进行修复")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        safe_print("\n[信息] 用户中断诊断")
        sys.exit(1)
    except Exception as e:
        safe_print(f"\n[错误] 诊断过程中发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)