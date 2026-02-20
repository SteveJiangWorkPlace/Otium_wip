#!/usr/bin/env python3
"""
测试所有后端功能：
1. 智能纠错
2. 流式翻译
3. 文本修改（非流式）
4. 文本修改（流式）
5. AI检测
6. AI聊天
"""

import json
import sys
import time
import requests
from typing import List, Dict, Any

BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/login"
CHECK_TEXT_URL = f"{BASE_URL}/api/text/check"
TRANSLATE_STREAM_URL = f"{BASE_URL}/api/text/translate-stream"
REFINE_URL = f"{BASE_URL}/api/text/refine"
REFINE_STREAM_URL = f"{BASE_URL}/api/text/refine-stream"
DETECT_AI_URL = f"{BASE_URL}/api/text/detect-ai"
CHAT_URL = f"{BASE_URL}/api/chat"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def read_test_text() -> str:
    """读取测试文本"""
    import pathlib
    test_file = pathlib.Path(__file__).parent / "测试段落1.txt"
    if not test_file.exists():
        # 备用测试文本
        return "近年来，人工智能技术飞速发展，机器学习、深度学习等算法在各个领域得到广泛应用。自然语言处理作为人工智能的重要分支，在机器翻译、文本生成、情感分析等方面取得了显著进展。"
    with open(test_file, encoding="utf-8") as f:
        return f.read().strip()

def login() -> str:
    """用户登录，获取JWT令牌"""
    print(f"[INFO] 正在登录用户: {ADMIN_USERNAME}")
    payload = {"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
    try:
        response = requests.post(LOGIN_URL, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        token = data.get("access_token")
        if not token:
            print(f"[ERROR] 登录响应中没有access_token: {data}")
            sys.exit(1)
        print(f"[SUCCESS] 登录成功，token长度: {len(token)}")
        return token
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] 登录请求失败: {e}")
        if hasattr(e, "response") and e.response:
            print(f"响应内容: {e.response.text}")
        sys.exit(1)

def make_authenticated_request(url, method="POST", token=None, **kwargs):
    """发送认证请求"""
    headers = kwargs.get("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    kwargs["headers"] = headers
    try:
        if method.upper() == "POST":
            response = requests.post(url, **kwargs, timeout=180)
        else:
            response = requests.get(url, **kwargs, timeout=180)
        response.raise_for_status()
        return response
    except requests.exceptions.Timeout:
        print(f"[ERROR] 请求超时: {url}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] 请求失败: {url}")
        if hasattr(e, "response") and e.response:
            print(f"状态码: {e.response.status_code}")
            print(f"响应内容: {e.response.text[:500]}")
        return None

def test_error_correction(token: str, text: str) -> bool:
    """测试智能纠错功能"""
    print("\n" + "=" * 60)
    print("测试智能纠错功能")
    print("=" * 60)
    payload = {"text": text, "operation": "error_check", "version": "professional"}
    print(f"[INFO] 发送纠错请求，文本长度: {len(text)} 字符")
    start_time = time.time()
    response = make_authenticated_request(CHECK_TEXT_URL, token=token, json=payload)
    if not response:
        print("[FAIL] 智能纠错测试失败")
        return False
    elapsed_time = time.time() - start_time
    result = response.json()
    print(f"[SUCCESS] 纠错完成，耗时: {elapsed_time:.2f}秒")
    print(f"[INFO] 响应类型: {type(result)}")
    if isinstance(result, dict) and "text" in result:
        corrected = result["text"]
        print(f"[INFO] 返回纠正文本，长度: {len(corrected)} 字符")
        preview = corrected[:200] + "..." if len(corrected) > 200 else corrected
        print(f"[PREVIEW] {preview}")
    else:
        print(f"[WARNING] 响应格式未知: {result}")
    return True

def test_streaming_translation(token: str, text: str) -> bool:
    """测试流式翻译功能"""
    print("\n" + "=" * 60)
    print("测试流式翻译功能 (US风格，专业版)")
    print("=" * 60)
    payload = {
        "text": text,
        "operation": "translate_us",
        "version": "professional"
    }
    headers = {"Authorization": f"Bearer {token}"}
    print(f"[INFO] 发送流式翻译请求，文本长度: {len(text)} 字符")
    start_time = time.time()
    try:
        response = requests.post(TRANSLATE_STREAM_URL, json=payload, headers=headers, stream=True, timeout=60)
        response.raise_for_status()
        # 处理SSE流
        collected_chunks = []
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith("data: "):
                    data_str = line_str[6:]  # 移除"data: "前缀
                    if data_str:
                        try:
                            chunk = json.loads(data_str)
                            collected_chunks.append(chunk)
                            if chunk.get("type") == "chunk" and "text" in chunk:
                                # 打印前几个字符以显示进度
                                if len(collected_chunks) <= 3:
                                    print(f"[CHUNK {len(collected_chunks)}] {chunk['text'][:50]}...")
                        except json.JSONDecodeError:
                            print(f"[WARNING] 无法解析JSON: {data_str[:100]}")
        elapsed_time = time.time() - start_time
        print(f"[SUCCESS] 流式翻译完成，耗时: {elapsed_time:.2f}秒")
        print(f"[INFO] 收到 {len(collected_chunks)} 个数据块")
        # 组合所有文本块
        full_text = "".join(chunk.get("text", "") for chunk in collected_chunks if chunk.get("type") == "chunk")
        if full_text:
            print(f"[INFO] 完整翻译文本长度: {len(full_text)} 字符")
            preview = full_text[:200] + "..." if len(full_text) > 200 else full_text
            print(f"[PREVIEW] {preview}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] 流式翻译请求失败: {e}")
        return False

def test_text_refine(token: str, text: str) -> bool:
    """测试文本修改功能（非流式）"""
    print("\n" + "=" * 60)
    print("测试文本修改功能（非流式）")
    print("=" * 60)
    # 使用一些快捷指令
    directives = ["humanize", "remove_ai_terms"]
    payload = {
        "text": text,
        "directives": directives
    }
    print(f"[INFO] 发送文本修改请求，文本长度: {len(text)} 字符")
    print(f"[INFO] 使用指令: {directives}")
    start_time = time.time()
    response = make_authenticated_request(REFINE_URL, token=token, json=payload)
    if not response:
        print("[FAIL] 文本修改测试失败")
        return False
    elapsed_time = time.time() - start_time
    result = response.json()
    print(f"[SUCCESS] 文本修改完成，耗时: {elapsed_time:.2f}秒")
    if isinstance(result, dict) and "text" in result:
        refined = result["text"]
        print(f"[INFO] 返回修改文本，长度: {len(refined)} 字符")
        preview = refined[:200] + "..." if len(refined) > 200 else refined
        print(f"[PREVIEW] {preview}")
    else:
        print(f"[WARNING] 响应格式未知: {result}")
    return True

def test_streaming_refine(token: str, text: str) -> bool:
    """测试流式文本修改功能"""
    print("\n" + "=" * 60)
    print("测试流式文本修改功能")
    print("=" * 60)
    directives = ["humanize", "remove_ai_terms"]
    payload = {
        "text": text,
        "directives": directives
    }
    headers = {"Authorization": f"Bearer {token}"}
    print(f"[INFO] 发送流式文本修改请求，文本长度: {len(text)} 字符")
    print(f"[INFO] 使用指令: {directives}")
    start_time = time.time()
    try:
        response = requests.post(REFINE_STREAM_URL, json=payload, headers=headers, stream=True, timeout=60)
        response.raise_for_status()
        collected_chunks = []
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith("data: "):
                    data_str = line_str[6:]
                    if data_str:
                        try:
                            chunk = json.loads(data_str)
                            collected_chunks.append(chunk)
                            if chunk.get("type") == "chunk" and "text" in chunk:
                                if len(collected_chunks) <= 3:
                                    print(f"[CHUNK {len(collected_chunks)}] {chunk['text'][:50]}...")
                        except json.JSONDecodeError:
                            print(f"[WARNING] 无法解析JSON: {data_str[:100]}")
        elapsed_time = time.time() - start_time
        print(f"[SUCCESS] 流式文本修改完成，耗时: {elapsed_time:.2f}秒")
        print(f"[INFO] 收到 {len(collected_chunks)} 个数据块")
        full_text = "".join(chunk.get("text", "") for chunk in collected_chunks if chunk.get("type") == "chunk")
        if full_text:
            print(f"[INFO] 完整修改文本长度: {len(full_text)} 字符")
            preview = full_text[:200] + "..." if len(full_text) > 200 else full_text
            print(f"[PREVIEW] {preview}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] 流式文本修改请求失败: {e}")
        return False

def test_ai_detection(token: str, text: str) -> bool:
    """测试AI检测功能"""
    print("\n" + "=" * 60)
    print("测试AI检测功能")
    print("=" * 60)
    payload = {"text": text}
    print(f"[INFO] 发送AI检测请求，文本长度: {len(text)} 字符")
    start_time = time.time()
    response = make_authenticated_request(DETECT_AI_URL, token=token, json=payload)
    if not response:
        print("[FAIL] AI检测测试失败")
        return False
    elapsed_time = time.time() - start_time
    result = response.json()
    print(f"[SUCCESS] AI检测完成，耗时: {elapsed_time:.2f}秒")
    if isinstance(result, dict):
        if "ai_probability" in result:
            ai_prob = result["ai_probability"]
            print(f"[RESULT] AI生成概率: {ai_prob:.2%}")
        if "classification" in result:
            classification = result["classification"]
            print(f"[RESULT] 分类结果: {classification}")
        if "confidence" in result:
            confidence = result["confidence"]
            print(f"[RESULT] 置信度: {confidence:.2%}")
    else:
        print(f"[WARNING] 响应格式未知: {result}")
    return True

def test_ai_chat(token: str) -> bool:
    """测试AI聊天功能"""
    print("\n" + "=" * 60)
    print("测试AI聊天功能")
    print("=" * 60)
    messages = [
        {"role": "user", "content": "请用中文简要介绍人工智能的主要应用领域。"}
    ]
    payload = {
        "messages": messages,
        "session_id": "test_session_123"
    }
    print(f"[INFO] 发送AI聊天请求，消息数量: {len(messages)}")
    start_time = time.time()
    response = make_authenticated_request(CHAT_URL, token=token, json=payload)
    if not response:
        print("[FAIL] AI聊天测试失败")
        return False
    elapsed_time = time.time() - start_time
    result = response.json()
    print(f"[SUCCESS] AI聊天完成，耗时: {elapsed_time:.2f}秒")
    if isinstance(result, dict) and "text" in result:
        chat_response = result["text"]
        print(f"[INFO] 返回聊天回复，长度: {len(chat_response)} 字符")
        preview = chat_response[:300] + "..." if len(chat_response) > 300 else chat_response
        print(f"[PREVIEW] {preview}")
    else:
        print(f"[WARNING] 响应格式未知: {result}")
    return True

def main():
    print("=" * 80)
    print("全平台功能测试 (扩展版)")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # 1. 读取测试文本
    print("\n[STEP 1] 读取测试文本")
    test_text = read_test_text()
    print(f"[INFO] 测试文本长度: {len(test_text)} 字符")
    print(f"[PREVIEW] 前200字符: {test_text[:200]}...")

    # 2. 用户登录
    print("\n[STEP 2] 用户登录")
    token = login()

    # 3. 测试智能纠错
    print("\n[STEP 3] 测试智能纠错")
    error_correction_success = test_error_correction(token, test_text)

    # 4. 测试流式翻译
    print("\n[STEP 4] 测试流式翻译")
    streaming_translation_success = test_streaming_translation(token, test_text)

    # 5. 测试文本修改（非流式）
    print("\n[STEP 5] 测试文本修改（非流式）")
    text_refine_success = test_text_refine(token, test_text)

    # 6. 测试文本修改（流式）
    print("\n[STEP 6] 测试文本修改（流式）")
    streaming_refine_success = test_streaming_refine(token, test_text)

    # 7. 测试AI检测
    print("\n[STEP 7] 测试AI检测")
    ai_detection_success = test_ai_detection(token, test_text)

    # 8. 测试AI聊天
    print("\n[STEP 8] 测试AI聊天")
    ai_chat_success = test_ai_chat(token)

    # 9. 总结报告
    print("\n" + "=" * 80)
    print("测试总结报告")
    print("=" * 80)

    tests = [
        ("智能纠错", error_correction_success),
        ("流式翻译", streaming_translation_success),
        ("文本修改（非流式）", text_refine_success),
        ("文本修改（流式）", streaming_refine_success),
        ("AI检测", ai_detection_success),
        ("AI聊天", ai_chat_success),
    ]

    total_tests = len(tests)
    passed_tests = sum(1 for _, success in tests if success)

    print(f"\n测试总数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {total_tests - passed_tests}")

    print("\n详细结果:")
    for test_name, success in tests:
        status = "[PASS] 通过" if success else "[FAIL] 失败"
        print(f"  {test_name}: {status}")

    if passed_tests == total_tests:
        print("\n[SUCCESS] 所有测试通过！系统功能正常。")
    else:
        print(f"\n[WARNING] {total_tests - passed_tests} 个测试失败，请检查相关功能。")
        sys.exit(1)

if __name__ == "__main__":
    main()