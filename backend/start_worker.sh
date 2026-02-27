#!/bin/bash

# 后台工作器启动脚本 (Unix/Linux)
# 用于本地开发环境启动后台任务处理工作器

echo "========================================"
echo "Otium 后台工作器启动脚本 (Unix/Linux)"
echo "========================================"
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "[错误] Python3未安装或不在PATH中"
    exit 1
fi

# 检查虚拟环境是否激活
if [ -z "$VIRTUAL_ENV" ]; then
    echo "[警告] 虚拟环境未激活，正在尝试激活..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo "[成功] 虚拟环境已激活"
    else
        echo "[错误] 虚拟环境目录不存在: venv/bin/activate"
        echo "[提示] 请先创建虚拟环境: python3 -m venv venv"
        exit 1
    fi
else
    echo "[信息] 虚拟环境已激活: $VIRTUAL_ENV"
fi

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "[警告] .env文件不存在，正在从示例文件创建..."
    if [ -f ".env.example" ]; then
        cp ".env.example" ".env"
        echo "[信息] 已创建.env文件，请根据需要编辑配置"
    else
        echo "[错误] .env.example文件不存在"
        exit 1
    fi
fi

# 检查是否启用后台工作器
export ENABLE_BACKGROUND_WORKER=True
echo "[信息] 设置ENABLE_BACKGROUND_WORKER=True"

# 设置工作器参数
WORKER_INTERVAL=5
WORKER_MAX_TASKS=3
WORKER_ID=1

echo "[信息] 工作器参数:"
echo "        轮询间隔: ${WORKER_INTERVAL}秒"
echo "        最大任务数: $WORKER_MAX_TASKS"
echo "        工作器ID: $WORKER_ID"

echo ""
echo "[信息] 正在启动后台工作器..."
echo "[提示] 按Ctrl+C停止工作器"
echo "========================================"
echo ""

# 启动后台工作器
python3 worker.py --interval $WORKER_INTERVAL --max-tasks $WORKER_MAX_TASKS --worker-id $WORKER_ID

echo ""
echo "========================================"
echo "[信息] 后台工作器已停止"
echo "========================================"