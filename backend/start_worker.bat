@echo off
REM 后台工作器启动脚本 (Windows批处理)
REM 用于本地开发环境启动后台任务处理工作器

echo ========================================
echo Otium 后台工作器启动脚本 (Windows)
echo ========================================
echo.

REM 检查Python环境
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [错误] Python未安装或不在PATH中
    pause
    exit /b 1
)

REM 检查虚拟环境是否激活
if "%VIRTUAL_ENV%"=="" (
    echo [警告] 虚拟环境未激活，正在尝试激活...
    if exist "venv\Scripts\activate.bat" (
        call venv\Scripts\activate.bat
        echo [成功] 虚拟环境已激活
    ) else (
        echo [错误] 虚拟环境目录不存在: venv\Scripts\activate.bat
        echo [提示] 请先创建虚拟环境: python -m venv venv
        pause
        exit /b 1
    )
) else (
    echo [信息] 虚拟环境已激活: %VIRTUAL_ENV%
)

REM 检查环境变量文件
if not exist ".env" (
    echo [警告] .env文件不存在，正在从示例文件创建...
    if exist ".env.example" (
        copy ".env.example" ".env"
        echo [信息] 已创建.env文件，请根据需要编辑配置
    ) else (
        echo [错误] .env.example文件不存在
        pause
        exit /b 1
    )
)

REM 检查是否启用后台工作器
set ENABLE_BACKGROUND_WORKER=True
echo [信息] 设置ENABLE_BACKGROUND_WORKER=True

REM 设置工作器参数
set WORKER_INTERVAL=5
set WORKER_MAX_TASKS=3
set WORKER_ID=1

echo [信息] 工作器参数:
echo        轮询间隔: %WORKER_INTERVAL%秒
echo        最大任务数: %WORKER_MAX_TASKS%
echo        工作器ID: %WORKER_ID%

echo.
echo [信息] 正在启动后台工作器...
echo [提示] 按Ctrl+C停止工作器
echo ========================================
echo.

REM 启动后台工作器
python worker.py --interval %WORKER_INTERVAL% --max-tasks %WORKER_MAX_TASKS% --worker-id %WORKER_ID%

echo.
echo ========================================
echo [信息] 后台工作器已停止
echo ========================================
pause