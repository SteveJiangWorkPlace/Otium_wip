#!/usr/bin/env pwsh
# 生产环境诊断脚本（PowerShell版本）
#
# 使用方法：
#   .\diagnose_production.ps1
#
# 环境变量（可选）：
#   $env:PRODUCTION_BACKEND_URL="https://your-backend-url.com"
#   $env:PRODUCTION_FRONTEND_URL="https://your-frontend-url.com"
#   $env:TEST_USERNAME="admin"
#   $env:TEST_PASSWORD="admin123"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "文献调研功能生产环境诊断" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python是否安装
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[信息] Python版本: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[错误] Python未安装或不在PATH中" -ForegroundColor Red
    Write-Host "请安装Python 3.7+并将其添加到PATH环境变量" -ForegroundColor Yellow
    Read-Host "按Enter键退出"
    exit 1
}

# 检查requests库
Write-Host "[信息] 检查requests库..." -ForegroundColor Green
try {
    python -c "import requests" 2>&1 | Out-Null
    Write-Host "[成功] requests库已安装" -ForegroundColor Green
} catch {
    Write-Host "[警告] requests库未安装，正在尝试安装..." -ForegroundColor Yellow
    try {
        pip install requests
        Write-Host "[成功] requests库安装完成" -ForegroundColor Green
    } catch {
        Write-Host "[错误] 无法安装requests库" -ForegroundColor Red
        Write-Host "请手动安装：pip install requests" -ForegroundColor Yellow
        Read-Host "按Enter键退出"
        exit 1
    }
}

Write-Host ""
Write-Host "[信息] 开始生产环境诊断..." -ForegroundColor Green
Write-Host ""

# 运行Python诊断脚本
try {
    python scripts/diagnose_production.py

    # 检查退出代码
    if ($LASTEXITCODE -eq 0) {
        Write-Host "" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "[成功] 诊断完成" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "" -ForegroundColor Green
        Write-Host "生产环境诊断通过，可以继续测试文献调研功能" -ForegroundColor Green
    } else {
        Write-Host "" -ForegroundColor Yellow
        Write-Host "========================================" -ForegroundColor Yellow
        Write-Host "[警告] 诊断发现一些问题" -ForegroundColor Yellow
        Write-Host "========================================" -ForegroundColor Yellow
        Write-Host "" -ForegroundColor Yellow
        Write-Host "请根据诊断报告进行修复：" -ForegroundColor Yellow
        Write-Host "1. 检查Render Dashboard服务状态" -ForegroundColor Yellow
        Write-Host "2. 验证环境变量设置" -ForegroundColor Yellow
        Write-Host "3. 查看服务日志" -ForegroundColor Yellow
        Write-Host "4. 参考docs/literature_research_refactor/生产环境诊断检查清单.md" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[错误] 诊断脚本执行失败: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Read-Host "按Enter键退出"