#!/usr/bin/env python3
"""
测试AI检测功能 - 英文内容
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

# 英文测试文本（超过250字符以满足GPTZero要求）
ENGLISH_TEST_TEXT = """
In recent years, artificial intelligence technology has developed rapidly,
with algorithms such as machine learning and deep learning being widely applied
in various fields. Natural language processing, as an important branch of AI,
has made significant progress in machine translation, text generation, and
sentiment analysis. However, as AI-generated text becomes more prevalent,
distinguishing between human-written and machine-generated content has become
a challenge. Both academia and industry are researching effective detection
methods to ensure the authenticity and originality of texts.

This paper aims to explore the current state of AI text detection technologies,
analyze the advantages and disadvantages of different methods, and suggest
potential future research directions. By reviewing existing techniques, we hope
to provide valuable references for related research. Additionally, practical
application scenarios and user requirements must be considered to ensure that
detection methods are both accurate and efficient.

The rapid advancement of AI has brought many benefits but also raised concerns
about content authenticity. Researchers are developing various approaches,
including statistical analysis, linguistic feature extraction, and machine
learning models to identify AI-generated text. Each method has its strengths
and limitations, and ongoing research seeks to improve detection accuracy
while reducing false positives.
"""

def test_english_ai_detection():
    print("=" * 70)
    print("测试AI检测功能 - 英文内容")
    print("=" * 70)

    # 1. 检查文本长度
    text_length = len(ENGLISH_TEST_TEXT.strip())
    print(f"\n[1] 测试文本长度: {text_length} 字符")
    print(f"文本预览 (前150字符): {ENGLISH_TEST_TEXT.strip()[:150]}...")

    if text_length < 250:
        print(f"[WARNING] 文本长度小于250字符，GPTZero可能拒绝请求")

    # 2. 用户登录
    print("\n[2] 用户登录")
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

    # 3. 调用AI检测API
    print("\n[3] 调用AI检测API")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"text": ENGLISH_TEST_TEXT.strip()}

    try:
        response = requests.post(DETECT_AI_URL, json=payload, headers=headers, timeout=30)
        print(f"HTTP状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("\n[SUCCESS] AI检测成功!")
            print("=" * 40)

            # 格式化输出结果
            if isinstance(result, dict):
                if "ai_probability" in result:
                    ai_prob = result["ai_probability"]
                    print(f"AI生成概率: {ai_prob:.2%}")

                    # 添加解读
                    if ai_prob < 0.3:
                        interpretation = "很可能是人类撰写的"
                    elif ai_prob < 0.7:
                        interpretation = "可能混合了AI和人类撰写内容"
                    else:
                        interpretation = "很可能是AI生成的"
                    print(f"解读: {interpretation}")

                if "classification" in result:
                    classification = result["classification"]
                    print(f"分类结果: {classification}")

                if "confidence" in result:
                    confidence = result["confidence"]
                    print(f"置信度: {confidence:.2%}")

                if "details" in result and isinstance(result["details"], dict):
                    print("\n详细结果:")
                    for key, value in result["details"].items():
                        if key != "service":  # 跳过service字段
                            print(f"  {key}: {value}")

                # 显示部分原始响应
                print(f"\n原始响应摘要:")
                print(json.dumps(result, ensure_ascii=False, indent=2)[:500] + "...")
            else:
                print(f"响应格式: {type(result)}")
                print(f"完整响应: {result}")

            return True
        else:
            print(f"\n[ERROR] API返回错误状态码: {response.status_code}")
            print(f"错误响应: {response.text[:500]}")

            # 尝试解析错误信息
            try:
                error_data = json.loads(response.text)
                if "detail" in error_data and isinstance(error_data["detail"], dict):
                    detail = error_data["detail"]
                    print(f"\n错误详情:")
                    print(f"  错误代码: {detail.get('error_code', '未知')}")
                    print(f"  错误消息: {detail.get('message', '未知')}")
            except:
                pass

            return False

    except requests.exceptions.Timeout:
        print("[ERROR] 请求超时 (30秒)")
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
    print("测试GPTZero AI检测功能")
    print(f"后端地址: {BASE_URL}")
    print(f"测试文本语言: 英文")
    print(f"测试文本长度: {len(ENGLISH_TEST_TEXT.strip())} 字符")

    success = test_english_ai_detection()

    if success:
        print("\n" + "=" * 70)
        print("[SUCCESS] AI检测功能测试通过!")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("[FAIL] AI检测功能测试失败")
        print("=" * 70)
        sys.exit(1)