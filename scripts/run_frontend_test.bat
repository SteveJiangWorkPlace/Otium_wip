@echo off
REM 前端测试脚本 - Windows批处理文件
REM 运行前端健康检查测试

echo ========================================
echo Otium前端健康检查测试
echo ========================================

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请确保Python已安装并添加到PATH
    pause
    exit /b 1
)

REM 检查Node.js是否安装
node --version >nul 2>&1
if errorlevel 1 (
    echo [警告] 未找到Node.js，前端测试可能不完整
    echo 但将继续运行Python检查部分...
)

echo.
echo [信息] 正在运行前端测试...
echo.

REM 运行测试脚本
python scripts\test_frontend.py

REM 根据测试结果设置退出代码
if errorlevel 1 (
    echo.
    echo [失败] 前端测试未通过
    pause
    exit /b 1
) else (
    echo.
    echo [成功] 前端测试通过
    pause
    exit /b 0
)