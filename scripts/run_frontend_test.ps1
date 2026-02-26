# 前端测试脚本 - PowerShell版本
# 运行前端健康检查测试

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Otium前端健康检查测试" -ForegroundColor Cyan
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

# 检查Node.js是否安装
try {
    $nodeVersion = node --version 2>&1
    Write-Host "[成功] Node.js版本: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "[警告] 未找到Node.js，前端测试可能不完整" -ForegroundColor Yellow
    Write-Host "但将继续运行Python检查部分..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[信息] 正在运行前端测试..." -ForegroundColor Cyan
Write-Host ""

# 运行测试脚本
python scripts/test_frontend.py

# 根据测试结果设置退出代码
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[失败] 前端测试未通过" -ForegroundColor Red
    Read-Host "按Enter键退出"
    exit 1
} else {
    Write-Host ""
    Write-Host "[成功] 前端测试通过" -ForegroundColor Green
    Read-Host "按Enter键退出"
    exit 0
}