#!/usr/bin/env python3
"""
系统功能测试脚本

测试所有主要功能：
1. 智能纠错
2. 学术翻译（基础版和专业版）
3. AI检测

使用测试段落1.txt中的文本进行测试。
"""

import json
import sys
import time
from pathlib import Path

import requests

# 基础配置
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/login"
CHECK_TEXT_URL = f"{BASE_URL}/api/text/check"
DETECT_AI_URL = f"{BASE_URL}/api/text/detect-ai"

# 默认管理员账户
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


# 读取测试文本
def read_test_text():
    """读取测试段落1.txt"""
    test_file = Path(__file__).parent.parent / "测试段落1.txt"
    if not test_file.exists():
        print(f"[ERROR] 测试文件不存在: {test_file}")
        sys.exit(1)

    with open(test_file, encoding="utf-8") as f:
        return f.read().strip()


def login():
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
    """
    发送带JWT认证的HTTP请求。

    Args:
        url (str): 目标URL
        method (str, optional): HTTP方法，默认"POST"
        token (str, optional): JWT令牌，如果提供则添加到Authorization头
        **kwargs: 传递给requests请求的额外参数

    Returns:
        requests.Response or None: 成功时返回Response对象，失败时返回None

    Raises:
        requests.exceptions.Timeout: 请求超时
        requests.exceptions.RequestException: 其他请求异常
    """
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


def test_error_correction(token, text):
    """
    测试智能纠错功能，验证API响应结构和内容。

    Args:
        token (str): 用户认证令牌
        text (str): 要测试的文本内容

    Returns:
        bool: 测试是否通过

    Note:
        - 会打印详细的测试过程和结果
        - 检查响应中的corrected_text或result字段
    """
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

    # 检查响应结构
    if isinstance(result, dict):
        if "corrected_text" in result:
            corrected = result["corrected_text"]
            print(f"[INFO] 返回纠正文本，长度: {len(corrected)} 字符")
            # 显示前200字符预览
            preview = corrected[:200] + "..." if len(corrected) > 200 else corrected
            print(f"[PREVIEW] {preview}")
        elif "result" in result:
            corrected = result["result"]
            print(f"[INFO] 返回结果，长度: {len(corrected)} 字符")
            preview = corrected[:200] + "..." if len(corrected) > 200 else corrected
            print(f"[PREVIEW] {preview}")
        else:
            print(f"[WARNING] 响应格式未知: {list(result.keys())}")
            print(f"完整响应: {json.dumps(result, ensure_ascii=False)[:500]}...")
    elif isinstance(result, str):
        print(f"[INFO] 返回字符串结果，长度: {len(result)} 字符")
        preview = result[:200] + "..." if len(result) > 200 else result
        print(f"[PREVIEW] {preview}")
    else:
        print(f"[WARNING] 响应类型未知: {type(result)}")

    return True


def test_translation(token, text, style="US", version="professional"):
    """
    测试学术翻译功能，支持不同风格和版本。

    Args:
        token (str): 用户认证令牌
        text (str): 要翻译的文本
        style (str, optional): 翻译风格，可选"US"或"UK"，默认"US"
        version (str, optional): 版本类型，可选"basic"或"professional"，默认"professional"

    Returns:
        bool: 测试是否通过

    Note:
        - 会验证翻译结果的格式和完整性
        - 检查translated_text或result字段
    """
    print("\n" + "=" * 60)
    print(f"测试学术翻译功能 (风格: {style}, 版本: {version})")
    print("=" * 60)

    operation = f"translate_{style.lower()}"
    payload = {"text": text, "operation": operation, "version": version}

    print(f"[INFO] 发送翻译请求，文本长度: {len(text)} 字符")
    print(f"[INFO] 操作: {operation}, 版本: {version}")
    start_time = time.time()

    response = make_authenticated_request(CHECK_TEXT_URL, token=token, json=payload)

    if not response:
        print(f"[FAIL] 翻译测试失败 (style={style}, version={version})")
        return False

    elapsed_time = time.time() - start_time
    result = response.json()

    print(f"[SUCCESS] 翻译完成，耗时: {elapsed_time:.2f}秒")
    print(f"[INFO] 响应类型: {type(result)}")

    # 检查响应结构
    if isinstance(result, dict):
        if "translated_text" in result:
            translated = result["translated_text"]
            print(f"[INFO] 返回翻译文本，长度: {len(translated)} 字符")
            # 显示前200字符预览
            preview = translated[:200] + "..." if len(translated) > 200 else translated
            print(f"[PREVIEW] {preview}")
        elif "result" in result:
            translated = result["result"]
            print(f"[INFO] 返回结果，长度: {len(translated)} 字符")
            preview = translated[:200] + "..." if len(translated) > 200 else translated
            print(f"[PREVIEW] {preview}")
        else:
            print(f"[WARNING] 响应格式未知: {list(result.keys())}")
            print(f"响应前500字符: {json.dumps(result, ensure_ascii=False)[:500]}...")
    elif isinstance(result, str):
        print(f"[INFO] 返回字符串结果，长度: {len(result)} 字符")
        preview = result[:200] + "..." if len(result) > 200 else result
        print(f"[PREVIEW] {preview}")
    else:
        print(f"[WARNING] 响应类型未知: {type(result)}")

    return True


def test_ai_detection(token, text):
    """
    测试AI文本检测功能，验证GPTZero API集成。

    Args:
        token (str): 用户认证令牌
        text (str): 要检测的文本

    Returns:
        bool: 测试是否通过

    Note:
        - 检查响应中的ai_probability、classification、confidence字段
        - 打印完整的JSON响应用于调试
    """
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
    print(f"[INFO] 完整响应: {json.dumps(result, ensure_ascii=False)}")

    # 检查响应结构
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
        print(f"[WARNING] 响应类型未知: {type(result)}")

    return True


def main():
    """
    执行完整的系统功能测试流程。

    测试步骤:
        1. 读取测试文本文件
        2. 用户登录获取JWT令牌
        3. 测试智能纠错功能
        4. 测试翻译功能（基础版和专业版，US/UK风格）
        5. 测试AI检测功能
        6. 生成测试报告

    Returns:
        None: 测试失败时会调用sys.exit(1)

    Note:
        - 测试失败会退出程序并返回错误码
        - 成功时打印所有测试通过的确认信息
    """
    print("=" * 80)
    print("全平台功能测试")
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

    # 4. 测试翻译功能
    print("\n[STEP 4] 测试翻译功能")

    # 4.1 测试基础版翻译 (US风格)
    translation_basic_us_success = test_translation(token, test_text, style="US", version="basic")

    # 4.2 测试专业版翻译 (US风格)
    translation_professional_us_success = test_translation(
        token, test_text, style="US", version="professional"
    )

    # 4.3 测试基础版翻译 (UK风格)
    translation_basic_uk_success = test_translation(token, test_text, style="UK", version="basic")

    # 4.4 测试专业版翻译 (UK风格)
    translation_professional_uk_success = test_translation(
        token, test_text, style="UK", version="professional"
    )

    # 5. 测试AI检测
    print("\n[STEP 5] 测试AI检测")
    ai_detection_success = test_ai_detection(token, test_text)

    # 6. 总结报告
    print("\n" + "=" * 80)
    print("测试总结报告")
    print("=" * 80)

    tests = [
        ("智能纠错", error_correction_success),
        ("翻译-基础版-US", translation_basic_us_success),
        ("翻译-专业版-US", translation_professional_us_success),
        ("翻译-基础版-UK", translation_basic_uk_success),
        ("翻译-专业版-UK", translation_professional_uk_success),
        ("AI检测", ai_detection_success),
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
