@echo off
echo ========================================
echo 强力终止所有Otium相关进程
echo ========================================
echo.

echo [1] 终止所有Node.js进程（前端）...
taskkill /IM node.exe /F 2>nul
if errorlevel 1 (
    echo [信息] 未找到运行的Node.js进程
) else (
    echo [成功] Node.js进程已终止
)

echo.
echo [2] 终止所有Python进程（后端）...
taskkill /IM python.exe /F 2>nul
if errorlevel 1 (
    echo [信息] 未找到运行的Python进程
) else (
    echo [成功] Python进程已终止
)

echo.
echo [3] 终止所有占用8000端口的进程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo [强制终止] 发现PID: %%a
    taskkill /PID %%a /F 2>nul
)

echo.
echo [4] 终止所有占用3000端口的进程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
    echo [强制终止] 发现PID: %%a
    taskkill /PID %%a /F 2>nul
)

echo.
echo [5] 等待2秒确保进程完全终止...
timeout /t 2 /nobreak >nul

echo.
echo [6] 再次检查端口占用...
echo 检查8000端口：
netstat -ano | findstr :8000 || echo [清理完成] 8000端口已释放
echo.
echo 检查3000端口：
netstat -ano | findstr :3000 || echo [清理完成] 3000端口已释放

echo.
echo ========================================
echo 进程终止完成！
echo ========================================
pause