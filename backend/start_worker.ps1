# 后台工作器启动脚本 (PowerShell)
# 用于本地开发环境启动后台任务处理工作器

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Otium 后台工作器启动脚本 (PowerShell)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python环境
try {
    $pythonPath = (Get-Command python -ErrorAction Stop).Source
    Write-Host "[信息] Python路径: $pythonPath" -ForegroundColor Green
} catch {
    Write-Host "[错误] Python未安装或不在PATH中" -ForegroundColor Red
    pause
    exit 1
}

# 检查虚拟环境是否激活
if (-not $env:VIRTUAL_ENV) {
    Write-Host "[警告] 虚拟环境未激活，正在尝试激活..." -ForegroundColor Yellow
    $activateScript = "venv\Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        & $activateScript
        Write-Host "[成功] 虚拟环境已激活" -ForegroundColor Green
    } else {
        Write-Host "[错误] 虚拟环境目录不存在: $activateScript" -ForegroundColor Red
        Write-Host "[提示] 请先创建虚拟环境: python -m venv venv" -ForegroundColor Yellow
        pause
        exit 1
    }
} else {
    Write-Host "[信息] 虚拟环境已激活: $env:VIRTUAL_ENV" -ForegroundColor Green
}

# 检查环境变量文件
if (-not (Test-Path ".env")) {
    Write-Host "[警告] .env文件不存在，正在从示例文件创建..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" -Destination ".env"
        Write-Host "[信息] 已创建.env文件，请根据需要编辑配置" -ForegroundColor Green
    } else {
        Write-Host "[错误] .env.example文件不存在" -ForegroundColor Red
        pause
        exit 1
    }
}

# 检查是否启用后台工作器
$env:ENABLE_BACKGROUND_WORKER = "True"
Write-Host "[信息] 设置ENABLE_BACKGROUND_WORKER=True" -ForegroundColor Green

# 设置工作器参数
$WORKER_INTERVAL = 5
$WORKER_MAX_TASKS = 3
$WORKER_ID = 1

Write-Host "[信息] 工作器参数:" -ForegroundColor Green
Write-Host "        轮询间隔: ${WORKER_INTERVAL}秒"
Write-Host "        最大任务数: $WORKER_MAX_TASKS"
Write-Host "        工作器ID: $WORKER_ID"

Write-Host ""
Write-Host "[信息] 正在启动后台工作器..." -ForegroundColor Cyan
Write-Host "[提示] 按Ctrl+C停止工作器" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 启动后台工作器
python worker.py --interval $WORKER_INTERVAL --max-tasks $WORKER_MAX_TASKS --worker-id $WORKER_ID

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "[信息] 后台工作器已停止" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan