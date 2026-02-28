#!/usr/bin/env python3
"""
模拟前端轮询流程，检查任务状态获取和处理
"""
import requests
import time
import json

PRODUCTION_BACKEND_URL = "https://otium.onrender.com"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkb2ciLCJyb2xlIjoidXNlciJ9.-8E2fPqLg3UdeAHW1d-GNIOZD2CKwCNgWaM3fXlTkfY"
TASK_ID = 4

def simulate_frontend_polling():
    """模拟前端轮询流程"""

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    print("=== 模拟前端轮询流程 ===\n")

    # 模拟指数退避轮询
    interval = 1000  # 1秒
    max_attempts = 600  # 10分钟
    current_interval = interval

    for attempt in range(1, max_attempts + 1):
        print(f"轮询尝试 #{attempt}/{max_attempts}，间隔: {current_interval}ms")

        # 获取任务状态
        url = f"{PRODUCTION_BACKEND_URL}/api/tasks/{TASK_ID}/status"
        try:
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code != 200:
                print(f"  请求失败，状态码: {response.status_code}")
                print(f"  响应: {response.text[:200]}")
                time.sleep(current_interval / 1000)
                current_interval = min(current_interval * 1.5, 10000)
                continue

            data = response.json()

            # 模拟前端解析：const { success, task, error } = response.data
            success = data.get('success')
            task = data.get('task')
            error = data.get('error')

            if not success:
                print(f"  任务失败: {error}")
                break

            if not task:
                print("  任务对象为空")
                time.sleep(current_interval / 1000)
                current_interval = min(current_interval * 1.5, 10000)
                continue

            # 检查任务状态
            status = task.get('status')
            result_data = task.get('result_data')

            print(f"  任务状态: {status}")
            print(f"  是否有result_data: {result_data is not None}")

            # 模拟前端条件检查
            if status == 'completed':
                if result_data and 'text' in result_data:
                    print("\n[成功] 任务完成，可以显示结果！")
                    print(f"  文本长度: {len(result_data['text'])}")
                    print(f"  前300字符预览: {result_data['text'][:300]}...")
                    print(f"  模型: {result_data.get('model_used', '未知')}")
                    return True
                else:
                    print("  任务状态为completed，但没有有效的结果数据")
                    break
            elif status == 'failed':
                print(f"  任务失败: {task.get('error_message', '未知错误')}")
                break
            elif status in ['pending', 'processing']:
                print(f"  任务仍在处理中...")
                # 继续轮询
            else:
                print(f"  未知状态: {status}")

            # 等待下一次轮询
            time.sleep(current_interval / 1000)
            current_interval = min(current_interval * 1.5, 10000)

        except Exception as e:
            print(f"  轮询异常: {e}")
            time.sleep(current_interval / 1000)
            current_interval = min(current_interval * 1.5, 10000)

    print("\n[失败] 轮询超时或失败")
    return False

def check_frontend_conditions():
    """检查前端显示结果的条件"""

    print("\n=== 检查前端显示条件 ===\n")

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    url = f"{PRODUCTION_BACKEND_URL}/api/tasks/{TASK_ID}/status"
    response = requests.get(url, headers=headers, timeout=30)
    data = response.json()

    task = data['task']

    # 前端AIChatPanel.tsx中的条件检查
    # if (task.status === BackgroundTaskStatus.COMPLETED && task.result_data)
    status = task.get('status')
    result_data = task.get('result_data')

    print("前端条件检查:")
    print(f"  1. task.status === 'completed': {status == 'completed'}")
    print(f"  2. task.result_data 存在: {result_data is not None}")
    print(f"  3. task.result_data.text 存在: {'text' in result_data if result_data else False}")

    # AIChatPanel.tsx第535-541行中的内容提取
    if status == 'completed' and result_data:
        text = result_data.get('text')
        result = result_data.get('result')

        print(f"\n前端提取内容:")
        print(f"  resultData.text: {text[:100] if text else 'None'}...")
        print(f"  resultData.result: {result[:100] if result else 'None'}...")
        print(f"  最终使用的内容: {text or result or '任务完成'}")

        # 检查编码问题
        if text:
            non_ascii = sum(1 for c in text[:500] if ord(c) > 127)
            print(f"  文本前500字符中非ASCII字符数: {non_ascii}")
            if non_ascii > 0:
                print(f"  注意: 文本包含中文或其他非ASCII字符，可能影响前端显示")

    # 检查BackgroundTaskStatus枚举值
    print(f"\nBackgroundTaskStatus枚举值比较:")
    print(f"  BackgroundTaskStatus.COMPLETED = 'completed'")
    print(f"  task.status = '{status}'")
    print(f"  两者相等: {status == 'completed'}")

if __name__ == "__main__":
    print(f"测试任务ID: {TASK_ID}")
    print(f"API地址: {PRODUCTION_BACKEND_URL}")
    print("=" * 50)

    # 运行模拟轮询
    success = simulate_frontend_polling()

    # 检查条件
    check_frontend_conditions()

    print("\n" + "=" * 50)
    if success:
        print("结论: API返回数据正常，前端应该能够显示结果")
        print("问题可能在前端代码实现、部署版本或网络通信中")
    else:
        print("结论: 轮询过程中发现问题，需要进一步检查")