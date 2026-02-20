#!/usr/bin/env python3
"""
后端文本翻译功能测试脚本
测试Gemini API集成的翻译功能是否正常工作
"""

import os
import sys
import time
import json
import requests
from datetime import datetime

# 添加当前目录到路径，以便导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置
BASE_URL = "http://localhost:8000"
HEALTH_ENDPOINT = f"{BASE_URL}/api/health"
TRANSLATE_ENDPOINT = f"{BASE_URL}/api/text/check"
TEST_TEXT = "人工智能正在改变我们的生活和工作方式。"
TEST_OPERATION = "translate_us"  # 美式英语翻译

def print_status(message, status="INFO"):
    """打印状态信息，避免使用Unicode字符"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    if status == "SUCCESS":
        status_str = "[成功]"
    elif status == "FAILURE":
        status_str = "[失败]"
    elif status == "WARNING":
        status_str = "[警告]"
    else:
        status_str = "[信息]"

    print(f"{timestamp} {status_str} {message}")

def check_backend_health():
    """检查后端服务是否运行"""
    try:
        print_status(f"检查后端服务: {BASE_URL}")
        response = requests.get(HEALTH_ENDPOINT, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                print_status("后端服务运行正常", "SUCCESS")
                return True
            else:
                print_status(f"后端服务状态异常: {data}", "FAILURE")
                return False
        else:
            print_status(f"后端服务响应异常: HTTP {response.status_code}", "FAILURE")
            return False
    except requests.exceptions.ConnectionError:
        print_status("无法连接到后端服务，请确保后端正在运行", "FAILURE")
        print_status("启动命令: cd backend && python -m venv venv && venv\\Scripts\\activate && pip install -r requirements.txt && uvicorn main:app --reload --host 0.0.0.0 --port 8000", "WARNING")
        return False
    except Exception as e:
        print_status(f"检查后端服务时出错: {str(e)}", "FAILURE")
        return False

def get_gemini_api_key():
    """从环境变量或.env文件获取Gemini API密钥"""
    # 首先尝试环境变量
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        print_status("从环境变量获取到Gemini API密钥", "SUCCESS")
        return api_key

    # 尝试从.env文件读取
    try:
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip() and not line.startswith("#"):
                        if "GEMINI_API_KEY" in line:
                            parts = line.split("=", 1)
                            if len(parts) == 2:
                                api_key = parts[1].strip()
                                # 移除可能的引号
                                api_key = api_key.strip('"').strip("'")
                                print_status("从.env文件获取到Gemini API密钥", "SUCCESS")
                                return api_key
    except Exception as e:
        print_status(f"读取.env文件时出错: {str(e)}", "WARNING")

    print_status("未找到Gemini API密钥，请检查.env文件配置", "FAILURE")
    return None

def get_auth_token():
    """获取JWT认证令牌"""
    try:
        print_status("获取JWT认证令牌")

        # 从.env文件读取管理员凭据
        admin_username = "admin"
        admin_password = "admin123"

        # 尝试从.env文件读取
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if "ADMIN_USERNAME" in line:
                            parts = line.split("=", 1)
                            if len(parts) == 2:
                                admin_username = parts[1].strip().strip('"').strip("'")
                        elif "ADMIN_PASSWORD" in line:
                            parts = line.split("=", 1)
                            if len(parts) == 2:
                                admin_password = parts[1].strip().strip('"').strip("'")

        print_status(f"使用管理员账号: {admin_username}")

        # 登录端点
        login_endpoint = f"{BASE_URL}/api/login"
        payload = {
            "username": admin_username,
            "password": admin_password
        }

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(login_endpoint, json=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                print_status("获取JWT令牌成功", "SUCCESS")
                return token
            else:
                print_status("响应中未找到access_token", "FAILURE")
                return None
        else:
            print_status(f"登录失败: HTTP {response.status_code}", "FAILURE")
            if response.text:
                print_status(f"错误详情: {response.text[:200]}", "WARNING")
            return None

    except Exception as e:
        print_status(f"获取认证令牌时出错: {str(e)}", "FAILURE")
        return None

def test_translation(api_key, auth_token):
    """测试翻译功能"""
    try:
        print_status(f"测试翻译功能: {TEST_OPERATION}")
        print_status(f"测试文本: {TEST_TEXT}")

        # 构建请求数据
        payload = {
            "text": TEST_TEXT,
            "operation": TEST_OPERATION,
            "options": {
                "style": "academic",
                "tone": "neutral"
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth_token}",  # 使用JWT令牌进行认证
            "X-Gemini-Api-Key": api_key  # 传递Gemini API密钥（备用）
        }

        print_status("发送翻译请求...")
        start_time = time.time()
        response = requests.post(
            TRANSLATE_ENDPOINT,
            json=payload,
            headers=headers,
            timeout=60  # 翻译可能耗时较长
        )
        elapsed_time = time.time() - start_time

        print_status(f"请求完成，耗时: {elapsed_time:.2f}秒")

        if response.status_code == 200:
            data = response.json()
            print_status("翻译请求成功", "SUCCESS")

            # 检查响应结构
            if "success" in data:
                if data["success"]:
                    translated_text = data.get("text", "")
                    if translated_text:
                        print_status(f"翻译结果: {translated_text}", "SUCCESS")
                        print_status(f"翻译结果长度: {len(translated_text)} 字符", "INFO")
                        return True
                    else:
                        print_status("翻译结果为空", "FAILURE")
                        return False
                else:
                    error_msg = data.get("error", "未知错误")
                    print_status(f"翻译失败: {error_msg}", "FAILURE")
                    return False
            else:
                print_status(f"响应格式异常: {data}", "FAILURE")
                return False
        else:
            print_status(f"HTTP错误: {response.status_code}", "FAILURE")
            if response.text:
                print_status(f"错误详情: {response.text[:200]}", "WARNING")
            return False

    except requests.exceptions.Timeout:
        print_status("翻译请求超时（60秒）", "FAILURE")
        return False
    except Exception as e:
        print_status(f"翻译测试时出错: {str(e)}", "FAILURE")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("后端文本翻译功能测试")
    print("=" * 60)

    # 步骤1: 检查后端服务
    print_status("步骤1: 检查后端服务状态")
    if not check_backend_health():
        print_status("测试中止: 后端服务未运行", "FAILURE")
        return 1

    # 步骤2: 获取API密钥
    print_status("步骤2: 获取Gemini API密钥")
    api_key = get_gemini_api_key()
    if not api_key:
        print_status("测试中止: 缺少API密钥", "FAILURE")
        return 1

    # 安全地显示API密钥（只显示前8位）
    key_display = api_key[:8] + "..." if len(api_key) > 8 else api_key
    print_status(f"使用的API密钥: {key_display}")

    # 步骤3: 获取JWT认证令牌
    print_status("步骤3: 获取JWT认证令牌")
    auth_token = get_auth_token()
    if not auth_token:
        print_status("测试中止: 无法获取认证令牌", "FAILURE")
        return 1

    # 安全地显示令牌（只显示前8位）
    token_display = auth_token[:8] + "..." if len(auth_token) > 8 else auth_token
    print_status(f"使用的JWT令牌: {token_display}")

    # 步骤4: 测试翻译功能
    print_status("步骤4: 测试翻译功能")
    if test_translation(api_key, auth_token):
        print_status("所有测试通过", "SUCCESS")
        print_status("翻译功能正常工作", "SUCCESS")
        return 0
    else:
        print_status("测试失败", "FAILURE")
        print_status("翻译功能存在问题", "FAILURE")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_status("测试被用户中断", "WARNING")
        sys.exit(1)
    except Exception as e:
        print_status(f"测试脚本异常: {str(e)}", "FAILURE")
        sys.exit(1)