@echo off
REM 后端测试脚本 - Windows批处理文件
REM 运行后端健康检查测试

echo ========================================
echo Otium后端健康检查测试
echo ========================================

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请确保Python已安装并添加到PATH
    pause
    exit /b 1
)

REM 检查requests库
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo [警告] requests库未安装，正在安装...
    pip install requests
    if errorlevel 1 (
        echo [错误] 安装requests库失败
        pause
        exit /b 1
    )
    echo [成功] requests库安装完成
)

echo.
echo [信息] 正在运行后端测试...
echo.

REM 运行测试脚本
python scripts\test_backend.py

REM 根据测试结果设置退出代码
if errorlevel 1 (
    echo.
    echo [失败] 后端测试未通过
    pause
    exit /b 1
) else (
    echo.
    echo [成功] 后端测试通过
    pause
    exit /b 0
)