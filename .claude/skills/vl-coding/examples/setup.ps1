# VL 引擎示例代码快速设置脚本 (Windows)

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "VL 引擎示例代码 - 快速设置" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
}

if (-not $pythonCmd) {
    Write-Host "❌ 未找到 Python，请先安装 Python" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Python 版本:" -ForegroundColor Green
& $pythonCmd --version
Write-Host ""

# 创建虚拟环境
$response = Read-Host "是否创建虚拟环境？(y/n)"
if ($response -eq 'y' -or $response -eq 'Y') {
    Write-Host "创建虚拟环境..." -ForegroundColor Yellow
    & $pythonCmd -m venv venv

    Write-Host "激活虚拟环境..." -ForegroundColor Yellow
    & .\venv\Scripts\Activate.ps1

    Write-Host "✓ 虚拟环境已创建并激活" -ForegroundColor Green
    Write-Host ""
}

# 安装依赖
Write-Host "安装 Python 依赖..." -ForegroundColor Yellow
& $pythonCmd -m pip install -r requirements.txt

Write-Host ""
Write-Host "✓ 依赖安装完成" -ForegroundColor Green
Write-Host ""

# 创建 .env 文件
if (-not (Test-Path .env)) {
    Write-Host "创建 .env 文件..." -ForegroundColor Yellow
    @"
# GLM-4V 配置
GLM_API_KEY=your_glm_api_key_here

# OpenAI 配置（可选）
OPENAI_API_KEY=your_openai_api_key_here
"@ | Out-File -FilePath .env -Encoding utf8

    Write-Host "✓ .env 文件已创建" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠️  请编辑 .env 文件并添加你的 API 密钥" -ForegroundColor Yellow
    Write-Host ""
}

# 创建必要的目录
Write-Host "创建必要的目录..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path pdfs | Out-Null
New-Item -ItemType Directory -Force -Path output | Out-Null
New-Item -ItemType Directory -Force -Path cache | Out-Null

Write-Host "✓ 目录创建完成" -ForegroundColor Green
Write-Host ""

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "设置完成！" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "1. 编辑 .env 文件，添加你的 API 密钥"
Write-Host "2. 将 PDF 文件放入 pdfs/ 目录"
Write-Host "3. 运行示例："
Write-Host "   python 01_basic_engine.py"
Write-Host "   python 02_pdf_converter.py"
Write-Host "   python 03_multi_engine.py"
Write-Host "   python 04_batch_processing.py"
Write-Host ""
Write-Host "详细文档请查看 README.md"
Write-Host ""
