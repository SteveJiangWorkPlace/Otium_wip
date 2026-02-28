@echo off
REM 生产环境诊断脚本（Windows批处理版本）
REM
REM 使用方法：
REM   diagnose_production.bat
REM
REM 环境变量（可选）：
REM   set PRODUCTION_BACKEND_URL=https://your-backend-url.com
REM   set PRODUCTION_FRONTEND_URL=https://your-frontend-url.com
REM   set TEST_USERNAME=admin
REM   set TEST_PASSWORD=admin123

echo ========================================
echo 文献调研功能生产环境诊断
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python未安装或不在PATH中
    echo 请安装Python 3.7+并将其添加到PATH环境变量
    pause
    exit /b 1
)

REM 检查requests库
echo [信息] 检查requests库...
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo [警告] requests库未安装，正在尝试安装...
    pip install requests
    if errorlevel 1 (
        echo [错误] 无法安装requests库
        echo 请手动安装：pip install requests
        pause
        exit /b 1
    )
    echo [成功] requests库安装完成
)

echo.
echo [信息] 开始生产环境诊断...
echo.

REM 运行Python诊断脚本
python scripts/diagnose_production.py

REM 检查退出代码
if errorlevel 1 (
    echo.
    echo ========================================
    echo [警告] 诊断发现一些问题
    echo ========================================
    echo.
    echo 请根据诊断报告进行修复：
    echo 1. 检查Render Dashboard服务状态
    echo 2. 验证环境变量设置
    echo 3. 查看服务日志
    echo 4. 参考docs/literature_research_refactor/生产环境诊断检查清单.md
) else (
    echo.
    echo ========================================
    echo [成功] 诊断完成
    echo ========================================
    echo.
    echo 生产环境诊断通过，可以继续测试文献调研功能
)

echo.
pause