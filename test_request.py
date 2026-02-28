#!/usr/bin/env python3
import requests
import json
import sys

# 生产环境配置
PRODUCTION_BACKEND_URL = "https://otium.onrender.com"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkb2ciLCJyb2xlIjoidXNlciJ9.-8E2fPqLg3UdeAHW1d-GNIOZD2CKwCNgWaM3fXlTkfY"

def test_chat_request():
    """测试聊天请求"""
    url = f"{PRODUCTION_BACKEND_URL}/api/chat"

    # 测试1: 普通聊天
    payload1 = {
        "messages": [{"role": "user", "content": "你好"}],
        "literature_research_mode": False,
        "generate_literature_review": False
    }

    # 测试2: 文献调研模式
    payload2 = {
        "messages": [{"role": "user", "content": "请调研人工智能在教育中的应用"}],
        "literature_research_mode": True,
        "generate_literature_review": False
    }

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    print("测试1: 普通聊天请求")
    print(f"请求URL: {url}")
    print(f"请求体: {json.dumps(payload1, ensure_ascii=False)}")

    try:
        response = requests.post(url, json=payload1, headers=headers, timeout=30)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text[:500]}")

        if response.status_code == 400:
            print("\n尝试分析错误...")
            print(f"完整响应: {response.text}")

    except Exception as e:
        print(f"请求异常: {e}")

    print("\n" + "="*80 + "\n")

    print("测试2: 文献调研模式")
    print(f"请求体: {json.dumps(payload2, ensure_ascii=False)}")

    try:
        response = requests.post(url, json=payload2, headers=headers, timeout=30)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text[:500]}")
    except Exception as e:
        print(f"请求异常: {e}")

if __name__ == "__main__":
    test_chat_request()