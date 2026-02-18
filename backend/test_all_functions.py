#!/usr/bin/env python3
"""
综合测试后端功能
测试智能纠错、文本翻译、AI检测、文本修改和AI对话功能
"""

import json
import sys
import time
import requests

# 配置
BASE_URL = "http://localhost:8005"
LOGIN_URL = f"{BASE_URL}/api/login"
CHECK_TEXT_URL = f"{BASE_URL}/api/text/check"
TRANSLATE_STREAM_URL = f"{BASE_URL}/api/text/translate-stream"
REFINE_STREAM_URL = f"{BASE_URL}/api/text/refine-stream"
DETECT_AI_URL = f"{BASE_URL}/api/text/detect-ai"
CHAT_URL = f"{BASE_URL}/api/chat"

# 测试用户凭证
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
        print("   请确保后端服务器正在运行")
        return None
    except Exception as e:
        print(f"   错误: {type(e).__name__}: {e}")
        return None

def test_error_check(token):
    """测试智能纠错功能"""
    print(f"\n2. 测试智能纠错: {CHECK_TEXT_URL}")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    test_text = "The quick brown fox jumps over the lazy dog. This is a test text for error checking."

    request_data = {
        "text": test_text,
        "operation": "error_check"
    }

    print(f"   测试文本: '{test_text[:50]}...'")
    print(f"   操作类型: error_check")

    try:
        start_time = time.time()
        response = requests.post(CHECK_TEXT_URL, json=request_data, headers=headers, timeout=300)
        elapsed_time = time.time() - start_time

        print(f"   响应时间: {elapsed_time:.2f}秒")
        print(f"   状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                text = data.get("text", "")
                model_used = data.get("model_used", "unknown")

                print(f"   成功！纠错结果长度: {len(text)} 字符")
                print(f"   使用的模型: {model_used}")
                print(f"   结果预览: {text[:100]}..." if text else "   结果为空")
                return True
            else:
                error_msg = data.get("error", "未知错误")
                error_type = data.get("error_type", "unknown")
                print(f"   失败！错误类型: {error_type}, 错误信息: {error_msg}")
                return False
        else:
            print(f"   错误状态码: {response.status_code}")
            print(f"   响应内容: {response.text[:200]}")
            return False

    except requests.exceptions.Timeout:
        print("   错误: 请求超时 (30秒)")
        return False
    except Exception as e:
        print(f"   错误: {type(e).__name__}: {e}")
        return False

def test_ai_detection(token):
    """测试AI检测功能"""
    print(f"\n3. 测试AI检测: {DETECT_AI_URL}")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 测试文本：混合人类写作和AI风格
    test_text = """The rapid advancement of artificial intelligence has transformed various sectors of society.
    Machine learning algorithms enable computers to learn from data and improve their performance over time.
    This technological progress raises important ethical questions about privacy, bias, and employment."""

    request_data = {
        "text": test_text
    }

    print(f"   测试文本长度: {len(test_text)} 字符")
    print(f"   文本预览: '{test_text[:80]}...'")

    try:
        start_time = time.time()
        response = requests.post(DETECT_AI_URL, json=request_data, headers=headers, timeout=300)
        elapsed_time = time.time() - start_time

        print(f"   响应时间: {elapsed_time:.2f}秒")
        print(f"   状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                ai_score = data.get("ai_score", 0)
                classification = data.get("classification", "unknown")
                details = data.get("details", {})

                print(f"   成功！AI分数: {ai_score}")
                print(f"   分类: {classification}")
                if details:
                    print(f"   详情: {details}")
                return True
            else:
                error_msg = data.get("error", "未知错误")
                print(f"   失败！错误: {error_msg}")
                return False
        else:
            print(f"   错误状态码: {response.status_code}")
            print(f"   响应内容: {response.text[:200]}")
            return False

    except requests.exceptions.Timeout:
        print("   错误: 请求超时 (30秒)")
        return False
    except Exception as e:
        print(f"   错误: {type(e).__name__}: {e}")
        return False

def parse_sse_response(response):
    """解析SSE流式响应"""
    lines = response.text.strip().split('\n')
    results = []

    for line in lines:
        if line.startswith('data: '):
            data_str = line[6:]  # 移除'data: '前缀
            if data_str:
                try:
                    data = json.loads(data_str)
                    results.append(data)
                except json.JSONDecodeError:
                    pass

    return results

def test_translation_stream(token):
    """测试流式文本翻译"""
    print(f"\n4. 测试流式文本翻译: {TRANSLATE_STREAM_URL}")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }

    test_text = "Artificial intelligence is revolutionizing education by providing personalized learning experiences."

    request_data = {
        "text": test_text,
        "operation": "translate_us",
        "version": "production"
    }

    print(f"   源文本: '{test_text}'")
    print(f"   操作类型: {request_data['operation']}")
    print(f"   版本: {request_data['version']}")

    try:
        start_time = time.time()
        response = requests.post(TRANSLATE_STREAM_URL, json=request_data, headers=headers, timeout=300, stream=True)
        elapsed_time = time.time() - start_time

        print(f"   连接时间: {elapsed_time:.2f}秒")
        print(f"   状态码: {response.status_code}")

        if response.status_code == 200:
            # 读取流式响应
            content = ""
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str:
                            try:
                                data = json.loads(data_str)
                                if data.get('type') == 'chunk' and 'text' in data:
                                    content += data['text']
                                elif data.get('type') == 'error':
                                    print(f"   流式错误: {data.get('error', '未知错误')}")
                                    return False
                                elif data.get('type') == 'complete':
                                    print(f"   翻译完成，总长度: {len(content)} 字符")
                                    print(f"   翻译预览: {content[:100]}..." if content else "   翻译结果为空")
                                    return True
                            except json.JSONDecodeError:
                                pass

            print(f"   翻译结果长度: {len(content)} 字符")
            print(f"   翻译预览: {content[:100]}..." if content else "   翻译结果为空")
            return True
        else:
            print(f"   错误状态码: {response.status_code}")
            print(f"   响应内容: {response.text[:200]}")
            return False

    except requests.exceptions.Timeout:
        print("   错误: 请求超时 (60秒)")
        return False
    except Exception as e:
        print(f"   错误: {type(e).__name__}: {e}")
        return False

def test_refine_stream(token):
    """测试流式文本修改"""
    print(f"\n5. 测试流式文本修改: {REFINE_STREAM_URL}")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }

    test_text = "The implementation of machine learning algorithms requires careful consideration of data quality and model selection."

    request_data = {
        "text": test_text,
        "directives": []
    }

    print(f"   待修改文本: '{test_text}'")
    print(f"   指令: {request_data['directives']}")

    try:
        start_time = time.time()
        response = requests.post(REFINE_STREAM_URL, json=request_data, headers=headers, timeout=300, stream=True)
        elapsed_time = time.time() - start_time

        print(f"   连接时间: {elapsed_time:.2f}秒")
        print(f"   状态码: {response.status_code}")

        if response.status_code == 200:
            # 读取流式响应
            content = ""
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str:
                            try:
                                data = json.loads(data_str)
                                if data.get('type') == 'chunk' and 'text' in data:
                                    content += data['text']
                                elif data.get('type') == 'error':
                                    print(f"   流式错误: {data.get('error', '未知错误')}")
                                    return False
                                elif data.get('type') == 'complete':
                                    print(f"   修改完成，总长度: {len(content)} 字符")
                                    print(f"   修改结果预览: {content[:100]}..." if content else "   修改结果为空")
                                    return True
                            except json.JSONDecodeError:
                                pass

            print(f"   修改结果长度: {len(content)} 字符")
            print(f"   修改结果预览: {content[:100]}..." if content else "   修改结果为空")
            return True
        else:
            print(f"   错误状态码: {response.status_code}")
            print(f"   响应内容: {response.text[:200]}")
            return False

    except requests.exceptions.Timeout:
        print("   错误: 请求超时 (60秒)")
        return False
    except Exception as e:
        print(f"   错误: {type(e).__name__}: {e}")
        return False

def test_ai_chat(token):
    """测试AI对话功能"""
    print(f"\n6. 测试AI对话: {CHAT_URL}")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    chat_request = {
        "messages": [
            {
                "role": "user",
                "content": "你好，请简单介绍一下人工智能在教育领域的应用。"
            }
        ],
        "session_id": "test_session_all_functions"
    }

    print(f"   用户消息: '{chat_request['messages'][0]['content']}'")

    try:
        start_time = time.time()
        response = requests.post(CHAT_URL, json=chat_request, headers=headers, timeout=300)
        elapsed_time = time.time() - start_time

        print(f"   响应时间: {elapsed_time:.2f}秒")
        print(f"   状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                text = data.get("text", "")
                model_used = data.get("model_used", "unknown")
                session_id = data.get("session_id", "")

                print(f"   成功！AI回复长度: {len(text)} 字符")
                print(f"   使用的模型: {model_used}")
                print(f"   会话ID: {session_id}")
                print(f"   AI回复预览: {text[:100]}...")
                return True
            else:
                error_msg = data.get("error", "未知错误")
                error_type = data.get("error_type", "unknown")
                print(f"   失败！错误类型: {error_type}, 错误信息: {error_msg}")
                return False
        else:
            print(f"   错误状态码: {response.status_code}")
            print(f"   响应内容: {response.text[:200]}")
            return False

    except requests.exceptions.Timeout:
        print("   错误: 请求超时 (30秒)")
        return False
    except Exception as e:
        print(f"   错误: {type(e).__name__}: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("后端功能综合测试")
    print("=" * 60)

    # 1. 测试登录
    token = test_login()
    if not token:
        print("\n[失败] 测试失败: 无法获取认证令牌")
        print("请检查:")
        print("  1. 后端服务器是否运行在 http://localhost:8003")
        print("  2. 默认管理员账户是否存在 (admin/admin123)")
        print("  3. 服务器日志是否有错误")
        sys.exit(1)

    results = []

    # 2. 测试智能纠错
    error_check_result = test_error_check(token)
    results.append(("智能纠错", error_check_result))

    # 3. 测试AI检测
    ai_detection_result = test_ai_detection(token)
    results.append(("AI检测", ai_detection_result))

    # 4. 测试流式文本翻译
    translation_result = test_translation_stream(token)
    results.append(("文本翻译", translation_result))

    # 5. 测试流式文本修改
    refine_result = test_refine_stream(token)
    results.append(("文本修改", refine_result))

    # 6. 测试AI对话（可能失败）
    chat_result = test_ai_chat(token)
    results.append(("AI对话", chat_result))

    # 测试总结
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

    success_count = sum(1 for _, success in results if success)
    total_count = len(results)

    print(f"\n测试结果汇总 ({success_count}/{total_count} 成功):")
    for name, success in results:
        status = "[成功]" if success else "[失败]"
        print(f"  {name}: {status}")

    if success_count == total_count:
        print("\n总结: 所有后端功能测试通过!")
        return 0
    else:
        print("\n总结: 部分后端功能测试失败")
        print("可能的原因:")
        print("  1. API密钥无效或过期")
        print("  2. 网络连接问题")
        print("  3. 服务器配置错误")
        print("  4. 速率限制或用户限制")
        return 1

if __name__ == "__main__":
    sys.exit(main())