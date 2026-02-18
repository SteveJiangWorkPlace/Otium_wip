#!/usr/bin/env python3
"""
测试Gemini不同模型
"""

import os
import sys
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置日志级别为DEBUG
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 从.env文件获取API密钥
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"从.env文件获取的Gemini API密钥: {GEMINI_API_KEY[:10]}...")

if not GEMINI_API_KEY:
    print("错误: 未找到GEMINI_API_KEY环境变量")
    sys.exit(1)

# 导入api_services
try:
    from api_services import generate_gemini_content_with_fallback
    print("成功导入api_services.generate_gemini_content_with_fallback")
except ImportError as e:
    print(f"导入错误: {e}")
    sys.exit(1)

# 测试不同的模型
test_models = [
    "gemini-2.5-flash",  # 已知有效的模型
    "gemini-2.5-pro",    # 备用模型
    "gemini-3-pro-preview",  # chat_with_gemini使用的模型
]

test_prompt = "Hello, say something short."

for model in test_models:
    print(f"\n{'='*60}")
    print(f"测试模型: {model}")
    print(f"{'='*60}")

    try:
        print(f"调用generate_gemini_content_with_fallback...")
        result = generate_gemini_content_with_fallback(
            prompt=test_prompt,
            api_key=GEMINI_API_KEY,
            primary_model=model,
            fallback_model="gemini-2.5-flash"
        )

        print(f"结果: success={result.get('success')}")
        print(f"使用的模型: {result.get('model_used', 'unknown')}")
        print(f"错误类型: {result.get('error_type', 'none')}")
        print(f"错误信息: {result.get('error', 'none')}")

        if result.get("success"):
            text = result.get("text", "")
            print(f"响应长度: {len(text)} 字符")
            print(f"响应预览: {text[:100]}")
        else:
            print("失败!")

    except Exception as e:
        print(f"异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

print("\n测试完成")