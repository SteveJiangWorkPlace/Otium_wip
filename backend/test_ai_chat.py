#!/usr/bin/env python3
"""
AI对话模块功能测试脚本
测试后端API的AI聊天功能是否正常工作
"""

import json
import sys
import time

try:
    import requests
except ImportError:
    print("错误: 需要安装requests库")
    print("运行: pip install requests")
    sys.exit(1)

# 配置
BASE_URL = "http://localhost:8006"
LOGIN_URL = f"{BASE_URL}/api/login"
CHAT_URL = f"{BASE_URL}/api/chat"

# 测试用户凭证（使用默认管理员账户）
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

def test_login():
    """测试登录获取JWT令牌"""
    print(f"1. 测试登录: {LOGIN_URL}")

    login_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }

    try:
        response = requests.post(LOGIN_URL, json=login_data, timeout=10)
        response.raise_for_status()

        data = response.json()
        if data.get("success") and "access_token" in data:
            token = data["access_token"]
            print(f"   成功！获取到JWT令牌: {token[:20]}...")
            return token
        else:
            print(f"   失败！响应: {data}")
            return None

    except requests.exceptions.ConnectionError:
        print(f"   错误: 无法连接到服务器 {BASE_URL}")
        print("   请确保后端服务器正在运行: uvicorn main:app --reload --port 8002")
        return None
    except Exception as e:
        print(f"   错误: {type(e).__name__}: {e}")
        return None

def test_ai_chat(token):
    """测试AI对话功能"""
    print(f"\n2. 测试AI对话: {CHAT_URL}")

    # 构建请求头
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 构建聊天请求
    chat_request = {
        "messages": [
            {
                "role": "user",
                "content": "你好，请介绍一下人工智能在教育领域的应用。"
            }
        ],
        "session_id": "test_session_123"  # 可选会话ID
    }

    print(f"   发送消息: '{chat_request['messages'][0]['content']}'")
    print(f"   请求头: Authorization: Bearer {token[:20]}...")

    try:
        start_time = time.time()
        response = requests.post(CHAT_URL, json=chat_request, headers=headers, timeout=300)
        elapsed_time = time.time() - start_time

        print(f"   响应时间: {elapsed_time:.2f}秒")
        print(f"   状态码: {response.status_code}")

        # 尝试解析响应
        try:
            data = response.json()

            if response.status_code == 200:
                if data.get("success"):
                    text = data.get("text", "")
                    model_used = data.get("model_used", "unknown")
                    session_id = data.get("session_id", "")

                    print(f"   成功！AI回复长度: {len(text)} 字符")
                    print(f"   使用的模型: {model_used}")
                    print(f"   会话ID: {session_id}")
                    print(f"   AI回复预览: {text[:100]}...")

                    # 检查回复质量
                    if len(text) > 10:
                        print("   [OK] AI回复内容有效")
                        return True
                    else:
                        print("   [警告] AI回复内容可能过短")
                        return False
                else:
                    error_msg = data.get("error", "未知错误")
                    print(f"   失败！错误: {error_msg}")
                    print(f"   完整响应: {data}")
                    return False
            else:
                print(f"   错误状态码: {response.status_code}")
                print(f"   响应内容: {response.text[:200]}")
                return False

        except json.JSONDecodeError:
            print(f"   错误: 响应不是有效的JSON")
            print(f"   原始响应: {response.text[:200]}")
            return False

    except requests.exceptions.Timeout:
        print("   错误: 请求超时 (30秒)")
        return False
    except requests.exceptions.ConnectionError:
        print("   错误: 连接中断")
        return False
    except Exception as e:
        print(f"   错误: {type(e).__name__}: {e}")
        return False

def test_rate_limiting(token):
    """测试速率限制（可选）"""
    print(f"\n3. 测试速率限制（发送3个快速请求）")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    for i in range(3):
        chat_request = {
            "messages": [
                {
                    "role": "user",
                    "content": f"测试消息 {i+1}: 什么是机器学习？"
                }
            ]
        }

        try:
            response = requests.post(CHAT_URL, json=chat_request, headers=headers, timeout=300)
            print(f"   请求 {i+1}: 状态码 {response.status_code}")

            if response.status_code == 429:
                print("   [OK] 速率限制正常工作 (收到429状态码)")
                return True

        except Exception as e:
            print(f"   请求 {i+1} 错误: {e}")

    print("   注: 未触发速率限制（可能需要更多请求或调整限制配置）")
    return True

def main():
    """主测试函数"""
    print("=" * 60)
    print("AI对话模块功能测试")
    print("=" * 60)

    # 1. 测试登录
    token = test_login()
    if not token:
        print("\n[失败] 测试失败: 无法获取认证令牌")
        print("请检查:")
        print("  1. 后端服务器是否运行在 http://localhost:8002")
        print("  2. 默认管理员账户是否存在 (admin/admin123)")
        print("  3. 服务器日志是否有错误")
        sys.exit(1)

    # 2. 测试AI对话
    chat_success = test_ai_chat(token)

    if chat_success:
        print("\n[成功] AI对话模块测试成功!")
    else:
        print("\n[失败] AI对话模块测试失败!")

    # 3. 可选: 测试速率限制
    # test_rate_limiting(token)

    # 4. 测试总结
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

    if chat_success:
        print("总结: AI对话模块功能正常")
        print("  - 认证系统正常工作")
        print("  - Gemini API连接正常")
        print("  - AI对话响应符合预期")
        return 0
    else:
        print("总结: AI对话模块存在问题")
        print("可能的原因:")
        print("  1. Gemini API密钥无效或过期")
        print("  2. 网络连接问题")
        print("  3. 服务器配置错误")
        print("  4. 速率限制或用户限制")
        return 1

if __name__ == "__main__":
    sys.exit(main())