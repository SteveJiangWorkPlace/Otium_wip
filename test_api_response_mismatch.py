#!/usr/bin/env python3
"""
测试前后端API响应格式不匹配问题
"""
import requests
import json

# 生产环境配置
PRODUCTION_BACKEND_URL = "https://otium.onrender.com"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkb2ciLCJyb2xlIjoidXNlciJ9.-8E2fPqLg3UdeAHW1d-GNIOZD2CKwCNgWaM3fXlTkfY"
TASK_ID = 4

def test_api_response_format():
    """测试API响应格式不匹配问题"""

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    print("=== 测试前后端API响应格式不匹配问题 ===\n")

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
            print(f"   'task'字段类型: {type(data['task'])}")
        else:
            print(f"   注意: 响应中没有'task'字段！")

        # 检查前端期望的字段
        print(f"\n3. 前端期望的字段 (GetTaskStatusResponse):")
        print(f"   - success: boolean")
        print(f"   - task: BackgroundTask (必需)")
        print(f"   - message?: string")
        print(f"   - error?: string")

        # 4. 比较实际响应与前端期望
        print(f"\n4. 比较实际响应与前端期望:")

        # 前端期望的字段
        expected_fields = ['success', 'task']

        for field in expected_fields:
            has_field = field in data
            print(f"   {field}: {'✓ 存在' if has_field else '✗ 缺失'}")

        # 5. 检查是否可以通过映射解决
        print(f"\n5. 可能的解决方案分析:")

        # 检查实际响应中的字段是否可以映射到BackgroundTask
        if not has_task_field:
            print(f"   a) 实际响应中没有'task'字段，但有以下相关字段:")

            # 检查是否有可以映射到BackgroundTask的字段
            task_mapping = {
                'task_id': 'id',
                'status': 'status',
                'result_data': 'result_data',
                'error_message': 'error_message',
                'started_at': 'started_at',
                'completed_at': 'completed_at',
                'progress': 'progress_percentage',
                'current_step': 'current_step',
                'total_steps': 'total_steps',
                'step_description': 'step_description',
                'step_details': 'step_details'
            }

            for api_field, task_field in task_mapping.items():
                if api_field in data:
                    print(f"      - {api_field} -> 可以映射到 task.{task_field}")
                else:
                    print(f"      - {api_field} -> 在响应中不存在")

            print(f"\n   b) 需要创建一个task对象，将API响应字段映射到task字段")

        # 6. 验证前端代码如何解析响应
        print(f"\n6. 前端代码解析方式:")
        print(f"   client.ts pollTaskResult函数期望:")
        print(f"      const {{ success, task, error }} = response.data;")
        print(f"   ")
        print(f"   如果response.data中没有'task'字段，task将为undefined")

        # 7. 建议解决方案
        print(f"\n7. 建议的解决方案:")
        print(f"   a) 修改后端: 在响应中添加'task'字段")
        print(f"   b) 修改前端: 适应后端响应格式")
        print(f"   c) 添加适配层: 在client.ts中转换响应格式")

    except Exception as e:
        print(f"请求异常: {e}")
        import traceback
        traceback.print_exc()

def simulate_frontend_parsing():
    """模拟前端解析逻辑"""
    print(f"\n=== 模拟前端解析逻辑 ===\n")

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    url = f"{PRODUCTION_BACKEND_URL}/api/tasks/{TASK_ID}/status"

    try:
        response = requests.get(url, headers=headers, timeout=30)
        data = response.json()

        # 模拟前端解析
        success = data.get('success')
        task = data.get('task')  # 前端期望这个字段
        error = data.get('error')

        print(f"前端解析结果:")
        print(f"  success: {success}")
        print(f"  task: {task}")
        print(f"  error: {error}")

        if task is None:
            print(f"\n问题: task为None/undefined!")
            print(f"  前端无法获取任务数据，结果无法显示")

            # 尝试从其他字段构建task对象
            print(f"\n尝试从响应数据构建task对象:")

            # 创建模拟的task对象
            mock_task = {
                'id': data.get('task_id'),
                'status': data.get('status'),
                'result_data': data.get('result_data'),
                'error_message': data.get('error_message'),
                'progress_percentage': data.get('progress'),
                'current_step': data.get('current_step'),
                'total_steps': data.get('total_steps'),
                'step_description': data.get('step_description'),
                'step_details': data.get('step_details'),
                'started_at': data.get('started_at'),
                'completed_at': data.get('completed_at'),
            }

            print(f"  可以构建的task字段:")
            for key, value in mock_task.items():
                if value is not None:
                    print(f"    - {key}: {type(value).__name__}")

    except Exception as e:
        print(f"模拟异常: {e}")

if __name__ == "__main__":
    test_api_response_format()
    simulate_frontend_parsing()