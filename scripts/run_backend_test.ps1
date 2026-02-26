# 后端测试脚本 - PowerShell版本
# 运行后端健康检查测试

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Otium后端健康检查测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 检查Python是否安装
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[成功] Python版本: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[错误] 未找到Python，请确保Python已安装并添加到PATH" -ForegroundColor Red
    Read-Host "按Enter键退出"
    exit 1
}

# 检查requests库
try {
    python -c "import requests" 2>&1 | Out-Null
    Write-Host "[成功] requests库已安装" -ForegroundColor Green
} catch {
    Write-Host "[警告] requests库未安装，正在安装..." -ForegroundColor Yellow
    pip install requests
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[错误] 安装requests库失败" -ForegroundColor Red
        Read-Host "按Enter键退出"
        exit 1
    }
    Write-Host "[成功] requests库安装完成" -ForegroundColor Green
}

Write-Host ""
Write-Host "[信息] 正在运行后端测试..." -ForegroundColor Cyan
Write-Host ""

# 运行测试脚本
python scripts/test_backend.py

# 根据测试结果设置退出代码
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[失败] 后端测试未通过" -ForegroundColor Red
    Read-Host "按Enter键退出"
    exit 1
} else {
    Write-Host ""
    Write-Host "[成功] 后端测试通过" -ForegroundColor Green
    Read-Host "按Enter键退出"
    exit 0
}