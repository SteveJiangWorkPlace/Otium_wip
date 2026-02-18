#!/usr/bin/env python3
"""
测试api_services.py中的完整流程
"""

import os
import logging
import time
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(level=logging.INFO)

# 加载环境变量
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("错误: 未找到GEMINI_API_KEY环境变量")
    exit(1)

print(f"使用API密钥: {GEMINI_API_KEY[:8]}...")
print()

# 模拟api_services.py中的设置
print("1. 模拟api_services.py中的代理设置...")
os.environ['NO_PROXY'] = '*'
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['ALL_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['all_proxy'] = ''
print("   已禁用代理设置")

# 安全设置
print("\n2. 准备安全设置...")
safety_settings = [
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]
print(f"   安全设置: {safety_settings}")

# 测试不同模型
test_models = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-3-pro-preview"
]

prompt = "Hello, say something short."

for model_name in test_models:
    print(f"\n{'='*60}")
    print(f"测试模型: {model_name}")
    print(f"{'='*60}")

    try:
        print(f"尝试导入google.genai库...")
        import google.genai
        print(f"成功导入google.genai")

        print(f"创建客户端...")
        start_time = time.time()
        try:
            client = google.genai.Client(api_key=GEMINI_API_KEY)
            print(f"客户端创建成功，耗时: {time.time()-start_time:.2f}秒")

            # 准备配置
            config = {"safety_settings": safety_settings}

            # 生成内容
            print(f"调用generate_content...")
            start_time = time.time()
            try:
                response = client.models.generate_content(
                    model=model_name, contents=prompt, config=config
                )
                elapsed_time = time.time() - start_time
                print(f"生成内容成功，耗时: {elapsed_time:.2f}秒")

                # 提取响应文本
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

                print(f"响应长度: {len(text)} 字符")
                print(f"响应预览: {text[:100]}...")

            except Exception as e:
                elapsed_time = time.time() - start_time
                print(f"generate_content失败: {type(e).__name__}: {e}")
                print(f"失败时间: {elapsed_time:.2f}秒")

        except Exception as e:
            print(f"客户端创建失败: {type(e).__name__}: {e}")

    except ImportError as e:
        print(f"导入google.genai失败: {e}")
        break
    except Exception as e:
        print(f"测试失败: {type(e).__name__}: {e}")

print("\n测试完成")