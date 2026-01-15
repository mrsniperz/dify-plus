#!/bin/bash

# VL 引擎示例代码快速设置脚本

echo "=================================="
echo "VL 引擎示例代码 - 快速设置"
echo "=================================="
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python 3，请先安装 Python"
    exit 1
fi

echo "✓ Python 版本: $(python3 --version)"
echo ""

# 创建虚拟环境（可选）
read -p "是否创建虚拟环境？(y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "创建虚拟环境..."
    python3 -m venv venv

    echo "激活虚拟环境..."
    source venv/bin/activate

    echo "✓ 虚拟环境已创建并激活"
    echo ""
fi

# 安装依赖
echo "安装 Python 依赖..."
pip install -r requirements.txt

echo ""
echo "✓ 依赖安装完成"
echo ""

# 检查 poppler
echo "检查系统依赖..."
if command -v pdftoppm &> /dev/null; then
    echo "✓ poppler 已安装"
else
    echo "⚠️  未找到 poppler"
    echo ""
    echo "请根据你的系统安装 poppler："
    echo "  Ubuntu/Debian: sudo apt-get install poppler-utils"
    echo "  macOS: brew install poppler"
    echo "  Windows: 下载并安装 poppler for Windows"
    echo ""
fi

# 创建 .env 文件
if [ ! -f .env ]; then
    echo ""
    echo "创建 .env 文件..."
    cat > .env << EOF
# GLM-4V 配置
GLM_API_KEY=your_glm_api_key_here

# OpenAI 配置（可选）
OPENAI_API_KEY=your_openai_api_key_here
EOF
    echo "✓ .env 文件已创建"
    echo ""
    echo "⚠️  请编辑 .env 文件并添加你的 API 密钥"
    echo ""
fi

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p pdfs output cache

echo "✓ 目录创建完成"
echo ""

echo "=================================="
echo "设置完成！"
echo "=================================="
echo ""
echo "下一步："
echo "1. 编辑 .env 文件，添加你的 API 密钥"
echo "2. 将 PDF 文件放入 pdfs/ 目录"
echo "3. 运行示例："
echo "   python 01_basic_engine.py"
echo "   python 02_pdf_converter.py"
echo "   python 03_multi_engine.py"
echo "   python 04_batch_processing.py"
echo ""
echo "详细文档请查看 README.md"
echo ""
