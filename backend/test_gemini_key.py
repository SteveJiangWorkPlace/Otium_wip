#!/usr/bin/env python3
"""
测试Gemini API密钥是否有效
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

    # 尝试列出模型
    print("尝试列出可用模型...")
    models = client.models.list()

    # 检查是否有模型
    model_names = [model.name for model in models]
    print(f"找到 {len(model_names)} 个模型")

    # 检查是否包含我们需要的模型
    target_models = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", "gemini-2.0-pro"]
    found_models = [name for name in model_names if any(target in name for target in target_models)]

    if found_models:
        print(f"找到目标模型: {found_models}")
        print("✅ Gemini API密钥有效!")
    else:
        print("⚠ 警告: 未找到目标模型，但API密钥可能仍有效")
        print(f"可用模型示例: {model_names[:5]}...")

except google.genai.errors.PermissionDeniedError:
    print("❌ 错误: API密钥无效或被拒绝访问")
    sys.exit(1)
except google.genai.errors.UnauthenticatedError:
    print("❌ 错误: 认证失败 - API密钥无效")
    sys.exit(1)
except google.genai.errors.GoogleAPIError as e:
    print(f"❌ Google API错误: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 其他错误: {type(e).__name__}: {e}")
    sys.exit(1)

print("测试完成")