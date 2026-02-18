#!/usr/bin/env python3
"""测试Gemini API密钥是否有效"""

import logging

import google.genai

logging.basicConfig(level=logging.INFO)


def test_gemini_api_key(api_key: str, model: str = "gemini-3-pro-preview"):
    """测试Gemini API密钥"""
    try:
        print(f"测试API密钥，模型: {model}")
        print(f"API密钥前缀: {api_key[:8]}...")

        client = google.genai.Client(api_key=api_key)

        # 简单测试
        response = client.models.generate_content(
            model=model, contents="Hello, say hi back in one word."
        )

        # 提取响应
        text = ""
        if hasattr(response, "text"):
            text = response.text
        elif hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "content") and candidate.content:
                if hasattr(candidate.content, "parts") and candidate.content.parts:
                    text = candidate.content.parts[0].text
                elif hasattr(candidate.content, "text"):
                    text = candidate.content.text

        print(f"成功! 响应: {text}")
        return True

    except Exception as e:
        print(f"错误: {type(e).__name__}: {str(e)}")
        return False


if __name__ == "__main__":
    api_key = "AIzaSyALdYcSfEHkBIWYBCvmuGpGtOsuuUDF9xU"

    print("测试gemini-3-pro-preview模型:")
    test_gemini_api_key(api_key, "gemini-3-pro-preview")

    print("\n测试gemini-2.5-pro模型:")
    test_gemini_api_key(api_key, "gemini-2.5-pro")
