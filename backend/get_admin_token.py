#!/usr/bin/env python3
"""
获取管理员JWT令牌
"""

import requests
from dotenv import load_dotenv

load_dotenv()


def get_admin_token():
    """获取管理员令牌"""
    url = "http://localhost:8000/api/admin/login"

    # 默认管理员凭证
    payload = {"password": "admin123"}

    try:
        response = requests.post(url, json=payload)

        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            if token:
                print(f"管理员令牌: {token}")
                return token
            else:
                print(f"响应中没有token字段: {data}")
        else:
            print(f"登录失败: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"请求异常: {type(e).__name__}: {str(e)}")

    return None


if __name__ == "__main__":
    token = get_admin_token()
    if token:
        # 保存到临时文件供其他脚本使用
        with open("admin_token.txt", "w") as f:
            f.write(token)
        print("令牌已保存到 admin_token.txt")
