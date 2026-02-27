#!/usr/bin/env python3
"""
模块名称：get_admin_token.py
功能描述：获取管理员JWT令牌的实用工具
创建时间：2026-02-27
作者：项目团队
版本：1.0.0

此工具通过调用后端管理员登录API获取JWT令牌，用于测试和管理脚本。
令牌可保存到临时文件供其他脚本使用，简化自动化测试和系统管理流程。

主要功能：
1. 调用管理员登录API获取JWT令牌
2. 处理网络异常和API错误
3. 将令牌保存到文件供后续使用
4. 提供简单的命令行接口

使用场景：
- 自动化测试脚本的身份验证
- 系统管理工具的令牌获取
- 开发环境快速获取管理员权限

注意事项：
- 依赖后端服务运行在默认端口（localhost:8000）
- 使用默认管理员密码（admin123），生产环境应修改
- 令牌保存在admin_token.txt文件中，注意安全清理
"""

import requests
from dotenv import load_dotenv

load_dotenv()


def get_admin_token():
    """
    获取管理员JWT令牌

    调用后端管理员登录API，使用默认管理员密码获取JWT访问令牌。
    令牌用于后续API调用的身份验证，支持测试和管理功能。

    Args:
        无: 函数使用默认配置，不接受参数

    Returns:
        str | None: 成功时返回JWT令牌字符串，失败时返回None

    Raises:
        无: 函数内部捕获所有异常，确保总是返回有效结果

    Examples:
        >>> token = get_admin_token()
        >>> if token:
        >>>     print(f"获取到令牌: {token[:20]}...")
        >>> else:
        >>>     print("获取令牌失败")

        # 在脚本中使用
        >>> import requests
        >>> token = get_admin_token()
        >>> headers = {"Authorization": f"Bearer {token}"}
        >>> response = requests.get("http://localhost:8000/api/admin/users", headers=headers)

    Notes:
        - API端点: POST http://localhost:8000/api/admin/login
        - 请求体: {"password": "admin123"}（默认管理员密码）
        - 成功响应: 200状态码，JSON包含token字段
        - 错误处理: 网络异常和API错误都会返回None并打印错误信息
        - 输出: 成功时打印令牌，失败时打印错误原因
        - 文件保存: 当作为主程序运行时，令牌保存到admin_token.txt
    """
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
