#!/usr/bin/env python3
"""
直接测试chat_with_gemini函数
"""

import os
import sys
import time
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 从.env文件获取API密钥
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"从.env文件获取的Gemini API密钥: {GEMINI_API_KEY[:10]}...")

if not GEMINI_API_KEY:
    print("错误: 未找到GEMINI_API_KEY环境变量")
    sys.exit(1)

# 尝试导入api_services
try:
    from api_services import chat_with_gemini
    print("成功导入api_services.chat_with_gemini")
except ImportError as e:
    print(f"导入错误: {e}")
    print("尝试导入完整模块...")
    import api_services
    print(f"成功导入api_services模块")
    chat_with_gemini = api_services.chat_with_gemini

# 测试消息
messages = [
    {"role": "user", "content": "你好，请介绍一下人工智能在教育领域的应用。"}
]

print(f"测试消息: {messages[0]['content']}")
print("调用chat_with_gemini函数...")

try:
    start_time = time.time()
    result = chat_with_gemini(messages=messages, api_key=GEMINI_API_KEY)
    elapsed_time = time.time() - start_time

    print(f"响应时间: {elapsed_time:.2f}秒")
    print(f"结果: {result}")

    if result.get("success"):
        print("成功!")
        text = result.get("text", "")
        model_used = result.get("model_used", "unknown")
        print(f"使用的模型: {model_used}")
        print(f"AI回复长度: {len(text)} 字符")
        print(f"AI回复预览: {text[:100]}...")
    else:
        print("失败!")
        error = result.get("error", "未知错误")
        error_type = result.get("error_type", "unknown")
        print(f"错误类型: {error_type}")
        print(f"错误信息: {error}")

except Exception as e:
    print(f"调用chat_with_gemini时发生异常: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("测试完成")