# MaaAgent 本地打包脚本
# 用于在本地测试 PyInstaller 打包
# 使用方法: 在项目根目录执行 .\tools\build_agent.ps1

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "MaaAgent PyInstaller 打包脚本" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# 确保在项目根目录
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
Set-Location $projectRoot

Write-Host "项目根目录: $projectRoot" -ForegroundColor Gray
Write-Host ""

# 检查 Python
Write-Host "[1/4] 检查 Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "✓ Python 版本: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 未找到 Python" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 检查并安装 PyInstaller
Write-Host "[2/4] 检查 PyInstaller..." -ForegroundColor Yellow
try {
    $pyiVersion = pyinstaller --version
    Write-Host "✓ PyInstaller 已安装: $pyiVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠ PyInstaller 未安装，正在安装..." -ForegroundColor Yellow
    pip install pyinstaller
    Write-Host "✓ PyInstaller 安装完成" -ForegroundColor Green
}

Write-Host ""

# 安装项目依赖
Write-Host "[3/4] 安装项目依赖..." -ForegroundColor Yellow
pip install -r requirements.txt
Write-Host "✓ 依赖安装完成" -ForegroundColor Green

Write-Host ""

# 开始打包
Write-Host "[4/4] 开始打包 MaaAgent.exe..." -ForegroundColor Yellow
Write-Host ""

# 清理旧的构建文件
if (Test-Path "dist") {
    Write-Host "清理旧的 dist 目录..." -ForegroundColor Gray
    Remove-Item -Recurse -Force dist
}
if (Test-Path "build") {
    Write-Host "清理旧的 build 目录..." -ForegroundColor Gray
    Remove-Item -Recurse -Force build
}

# 执行打包
Write-Host "执行 PyInstaller..." -ForegroundColor Cyan
pyinstaller MaaAgent.spec

Write-Host ""

# 检查结果
if (Test-Path "dist/MaaAgent.exe") {
    $fileSize = (Get-Item "dist/MaaAgent.exe").Length / 1MB
    Write-Host "=" * 60 -ForegroundColor Green
    Write-Host "✅ 打包成功!" -ForegroundColor Green
    Write-Host "=" * 60 -ForegroundColor Green
    Write-Host ""
    Write-Host "输出文件: dist/MaaAgent.exe" -ForegroundColor White
    Write-Host "文件大小: $($fileSize.ToString('0.00')) MB" -ForegroundColor White
    Write-Host ""
    Write-Host "测试运行:" -ForegroundColor Cyan
    Write-Host "  .\dist\MaaAgent.exe <socket_id>" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "=" * 60 -ForegroundColor Red
    Write-Host "❌ 打包失败!" -ForegroundColor Red
    Write-Host "=" * 60 -ForegroundColor Red
    Write-Host ""
    Write-Host "请检查上方错误信息" -ForegroundColor Yellow
    exit 1
}
