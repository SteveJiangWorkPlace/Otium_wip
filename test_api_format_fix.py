#!/usr/bin/env python3
"""
测试API响应格式修复后的效果
"""
import requests
import json

# 生产环境配置
PRODUCTION_BACKEND_URL = "https://otium.onrender.com"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkb2ciLCJyb2xlIjoidXNlciJ9.-8E2fPqLg3UdeAHW1d-GNIOZD2CKwCNgWaM3fXlTkfY"
TASK_ID = 4

def test_fixed_api_response():
    """测试修复后的API响应格式"""

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    print("=== 测试修复后的API响应格式 ===\n")

    # 1. 获取实际API响应
    url = f"{PRODUCTION_BACKEND_URL}/api/tasks/{TASK_ID}/status"

    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"1. 实际API响应:")
        print(f"   状态码: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type')}")

        data = response.json()

        # 2. 分析实际响应结构
        print(f"\n2. 实际响应结构:")
        print(f"   响应字段: {list(data.keys())}")

        # 检查是否有task字段
        has_task_field = 'task' in data
        print(f"   是否有'task'字段: {has_task_field}")

        if has_task_field:
            task = data['task']
            print(f"   'task'字段类型: {type(task)}")
            print(f"   'task'字段包含的键: {list(task.keys())}")

            # 检查前端期望的字段是否都存在
            required_fields = ['id', 'status', 'result_data']
            print(f"\n3. 检查前端必需字段:")
            for field in required_fields:
                has_field = field in task
                print(f"   {field}: {'存在' if has_field else '缺失'}")

            # 检查result_data内容
            if 'result_data' in task and task['result_data']:
                result_data = task['result_data']
                print(f"\n4. 检查result_data:")
                print(f"   result_data类型: {type(result_data)}")
                print(f"   result_data包含的键: {list(result_data.keys())}")

                if 'text' in result_data:
                    text = result_data['text']
                    print(f"   有text字段，长度: {len(text)}")
                    print(f"   前200字符预览: {text[:200]}...")

        # 5. 验证前端解析
        print(f"\n5. 验证前端解析逻辑:")
        print(f"   前端期望: const {{ success, task, error }} = response.data;")
        success = data.get('success')
        task = data.get('task')
        error = data.get('error')
        print(f"   解析结果:")
        print(f"     success: {success}")
        print(f"     task: {'存在' if task else 'None/undefined'}")
        print(f"     error: {error}")

        if task:
            print(f"\n6. 前端可以正常访问的任务字段:")
            print(f"    task.id: {task.get('id')}")
            print(f"    task.status: {task.get('status')}")
            print(f"    task.result_data: {'存在' if task.get('result_data') else 'None'}")

    except Exception as e:
        print(f"请求异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_api_response()