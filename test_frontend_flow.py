#!/usr/bin/env python3
"""
测试前端流程：模拟前端获取任务结果的完整流程
"""
import requests
import json
import time

# 生产环境配置
PRODUCTION_BACKEND_URL = "https://otium.onrender.com"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkb2ciLCJyb2xlIjoidXNlciJ9.-8E2fPqLg3UdeAHW1d-GNIOZD2CKwCNgWaM3fXlTkfY"
TASK_ID = 4  # 已完成的任务

def test_frontend_task_result_flow():
    """测试前端获取任务结果的完整流程"""

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    print("=== 测试前端任务结果获取流程 ===\n")

    # 1. 模拟前端调用：获取任务状态
    print("1. 模拟前端调用：获取任务状态")
    url = f"{PRODUCTION_BACKEND_URL}/api/tasks/{TASK_ID}/status"

    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"请求URL: {url}")
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"响应成功: {data.get('success')}")
            print(f"任务状态: {data.get('status')}")

            # 2. 检查任务结果数据格式
            if data.get('success') and data.get('status') == 'completed':
                task = data.get('task', {})
                result_data = task.get('result_data', {})

                print(f"\n2. 检查任务结果数据格式:")
                print(f"   任务ID: {task.get('id')}")
                print(f"   任务类型: {task.get('task_type')}")
                print(f"   是否有result_data: {'result_data' in task}")
                print(f"   result_data类型: {type(result_data)}")

                # 3. 检查结果数据内容
                if result_data:
                    print(f"\n3. 检查结果数据内容:")
                    print(f"   result_data.keys(): {list(result_data.keys())}")
                    print(f"   是否有text字段: {'text' in result_data}")
                    print(f"   text字段类型: {type(result_data.get('text'))}")
                    print(f"   text字段长度: {len(result_data.get('text', '')) if result_data.get('text') else 0}")
                    print(f"   是否有steps字段: {'steps' in result_data}")
                    print(f"   steps字段类型: {type(result_data.get('steps'))}")
                    print(f"   steps长度: {len(result_data.get('steps', []))}")

                    # 4. 检查前端需要的字段
                    print(f"\n4. 检查前端需要的字段:")
                    text = result_data.get('text') or result_data.get('result') or '任务完成'
                    print(f"   提取的文本: {text[:200]}...")
                    print(f"   文本长度: {len(text)}")

                    # 5. 检查编码问题
                    print(f"\n5. 检查编码问题:")
                    text_sample = text[:500]
                    non_ascii_count = sum(1 for c in text_sample if ord(c) > 127)
                    print(f"   前500字符中非ASCII字符数: {non_ascii_count}")
                    print(f"   响应编码: {response.encoding}")
                    print(f"   响应头Content-Type: {response.headers.get('Content-Type')}")

                    # 6. 检查前端cleanMarkdown函数可能遇到的问题
                    print(f"\n6. 检查前端cleanMarkdown函数可能遇到的问题:")
                    # 检查是否有markdown符号
                    has_markdown_headings = '#' in text_sample
                    has_markdown_bold = '**' in text_sample
                    has_markdown_italic = '*' in text_sample
                    has_markdown_code = '`' in text_sample
                    has_markdown_links = '[' in text_sample and '](' in text_sample
                    print(f"   包含#标题: {has_markdown_headings}")
                    print(f"   包含**粗体**: {has_markdown_bold}")
                    print(f"   包含*斜体*: {has_markdown_italic}")
                    print(f"   包含`代码`: {has_markdown_code}")
                    print(f"   包含[链接]: {has_markdown_links}")

                else:
                    print(f"\n警告: result_data为空或不存在")

            else:
                print(f"\n错误: 任务未完成或请求失败")
                print(f"   错误信息: {data.get('error')}")

        else:
            print(f"错误: HTTP {response.status_code}")
            print(f"响应: {response.text[:500]}")

    except Exception as e:
        print(f"请求异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_frontend_task_result_flow()