#!/usr/bin/env python3
"""
验证文献调研功能修复
"""
import requests
import json

# 生产环境配置
PRODUCTION_BACKEND_URL = "https://otium.onrender.com"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkb2ciLCJyb2xlIjoidXNlciJ9.-8E2fPqLg3UdeAHW1d-GNIOZD2CKwCNgWaM3fXlTkfY"
TASK_ID = 4

def test_full_flow():
    """测试完整流程"""

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    print("=== 文献调研功能完整测试 ===\n")

    # 1. 测试任务状态API
    print("1. 测试任务状态API响应格式")
    url = f"{PRODUCTION_BACKEND_URL}/api/tasks/{TASK_ID}/status"

    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"   状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            # 检查响应格式
            print(f"   响应字段: {list(data.keys())}")

            # 检查关键字段
            has_task = 'task' in data
            has_success = 'success' in data

            print(f"   是否有'task'字段: {has_task}")
            print(f"   是否有'success'字段: {has_success}")

            if has_task and has_success:
                task = data['task']
                success = data['success']

                print(f"\n2. 任务对象结构:")
                print(f"   任务ID: {task.get('id')}")
                print(f"   任务状态: {task.get('status')}")
                print(f"   是否有result_data: {'result_data' in task}")

                if 'result_data' in task and task['result_data']:
                    result_data = task['result_data']
                    print(f"\n3. 结果数据:")
                    print(f"   结果字段: {list(result_data.keys())}")

                    if 'text' in result_data:
                        text = result_data['text']
                        print(f"   文本长度: {len(text)}")
                        print(f"   前300字符预览: {text[:300]}...")

                        # 检查编码
                        non_ascii = sum(1 for c in text[:500] if ord(c) > 127)
                        print(f"   前500字符中非ASCII字符数: {non_ascii}")

                        if non_ascii > 0:
                            print(f"   注意: 文本包含中文或其他非ASCII字符")

                    if 'steps' in result_data:
                        steps = result_data['steps']
                        print(f"   步骤数量: {len(steps)}")

                print(f"\n4. 前端兼容性验证:")
                print(f"   前端解析: const {{ success, task, error }} = response.data")
                print(f"   success: {success}")
                print(f"   task: {'有效对象' if task else 'None'}")
                print(f"   error: {data.get('error')}")

                if task and 'result_data' in task and task['result_data']:
                    print(f"\n✅ 结果可以正确传递到前端!")
                else:
                    print(f"\n❌ 结果可能无法正确传递到前端")
            else:
                print(f"\n❌ API响应格式不符合前端期望")
                print(f"   需要部署修复代码")

        else:
            print(f"❌ API请求失败: {response.status_code}")
            print(f"   响应: {response.text[:500]}")

    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n=== 修复建议 ===")
    print(f"1. 部署修改后的代码到生产环境:")
    print(f"   - backend/main.py: get_task_status函数")
    print(f"   - backend/schemas.py: TaskStatusResponse模型")
    print(f"   - backend/api_services.py: 已包含提示词模板系统")
    print(f"")
    print(f"2. 验证前端加载动画修改:")
    print(f"   - frontend/src/components/AIChatPanel/AIChatPanel.tsx")
    print(f"     已统一加载动画格式，移除复杂显示")
    print(f"")
    print(f"3. 测试流程:")
    print(f"   a) 发送文献调研请求")
    print(f"   b) 检查任务创建和状态轮询")
    print(f"   c) 验证结果正确显示在前端")

if __name__ == "__main__":
    test_full_flow()