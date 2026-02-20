#!/usr/bin/env python3
"""
直接测试GPTZero API功能
"""
import sys
import json
import requests

# 修复Windows控制台编码问题
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/login"
DETECT_AI_URL = f"{BASE_URL}/api/text/detect-ai"

def test_gptzero():
    print("=" * 60)
    print("直接测试GPTZero API功能")
    print("=" * 60)

    # 1. 登录获取token
    print("\n[1] 用户登录")
    login_data = {"username": "admin", "password": "admin123"}
    try:
        login_resp = requests.post(LOGIN_URL, json=login_data, timeout=10)
        login_resp.raise_for_status()
        login_result = login_resp.json()
        token = login_result.get("access_token")
        if not token:
            print("[ERROR] 登录响应中没有access_token")
            return False
        print(f"[SUCCESS] 登录成功，token长度: {len(token)}")
    except Exception as e:
        print(f"[ERROR] 登录失败: {e}")
        return False

    # 2. 测试文本
    test_text = "近年来，人工智能技术飞速发展，机器学习、深度学习等算法在各个领域得到广泛应用。自然语言处理作为人工智能的重要分支，在机器翻译、文本生成、情感分析等方面取得了显著进展。然而，随着AI生成文本的普及，如何区分人工撰写和机器生成的内容成为一个挑战。学术界和工业界都在研究有效的检测方法，以确保文本的真实性和原创性。本文旨在探讨当前AI文本检测技术的现状，分析不同方法的优缺点，并提出未来可能的研究方向。我们希望通过对现有技术的梳理，为相关研究提供参考。除此之外，还需要考虑技术的实际应用场景和用户需求，确保检测方法既准确又高效。"
    print(f"\n[2] 测试文本长度: {len(test_text)} 字符")
    print(f"预览: {test_text[:100]}...")

    # 3. 调用AI检测
    print("\n[3] 调用AI检测API")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"text": test_text}

    try:
        response = requests.post(DETECT_AI_URL, json=payload, headers=headers, timeout=30)
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"[SUCCESS] AI检测成功!")
            print(f"完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")

            if isinstance(result, dict):
                if "ai_probability" in result:
                    ai_prob = result["ai_probability"]
                    print(f"\nAI生成概率: {ai_prob:.2%}")

                if "classification" in result:
                    classification = result["classification"]
                    print(f"分类结果: {classification}")

                if "confidence" in result:
                    confidence = result["confidence"]
                    print(f"置信度: {confidence:.2%}")
            return True
        else:
            print(f"[ERROR] API返回错误状态码: {response.status_code}")
            print(f"响应内容: {response.text[:500]}")
            return False

    except requests.exceptions.Timeout:
        print("[ERROR] 请求超时")
        return False
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] 请求失败: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"响应内容: {e.response.text[:500]}")
        return False
    except Exception as e:
        print(f"[ERROR] 未知错误: {e}")
        return False

if __name__ == "__main__":
    success = test_gptzero()
    if success:
        print("\n" + "=" * 60)
        print("[SUCCESS] GPTZero API测试通过!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("[FAIL] GPTZero API测试失败")
        print("=" * 60)
        sys.exit(1)