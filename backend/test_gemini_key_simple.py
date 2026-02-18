#!/usr/bin/env python3
"""
测试Gemini API密钥是否有效 - 简单版本
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从.env文件获取API密钥
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"从.env文件获取的Gemini API密钥: {GEMINI_API_KEY[:10]}...")

if not GEMINI_API_KEY:
    print("错误: 未找到GEMINI_API_KEY环境变量")
    sys.exit(1)

# 尝试导入google.genai
try:
    import google.genai
    import google.genai.errors
    print("成功导入google.genai库")
except ImportError:
    print("错误: 需要安装google-genai库")
    print("运行: pip install google-genai")
    sys.exit(1)

# 测试API密钥
try:
    print("测试Gemini API密钥...")

    # 初始化客户端
    client = google.genai.Client(api_key=GEMINI_API_KEY)

    # 尝试简单的生成内容
    print("尝试生成简单内容...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Hello, say something short."
    )

    if response.text:
        print("成功收到响应!")
        print(f"响应预览: {response.text[:100]}")
        print("API密钥有效!")
    else:
        print("警告: 响应为空，但API调用成功")

except Exception as e:
    error_type = type(e).__name__
    error_msg = str(e)
    print(f"错误: {error_type}: {error_msg}")

    # 检查常见错误类型
    if "401" in error_msg or "unauthorized" in error_msg.lower() or "authentication" in error_msg.lower():
        print("API密钥无效或认证失败")
    elif "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
        print("超过配额或速率限制")
    elif "404" in error_msg or "not found" in error_msg.lower():
        print("模型未找到，但API密钥可能有效")
    else:
        print("其他API错误")

    sys.exit(1)

print("测试完成")