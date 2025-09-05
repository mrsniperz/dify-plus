#!/bin/bash

# Markdown测试用例转Excel转换器启动脚本
# 作者: AI Assistant
# 创建时间: 2025-09-05

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    echo "Markdown测试用例转Excel转换器"
    echo ""
    echo "用法:"
    echo "  $0 [选项] [输入目录] [输出文件]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -t, --test     运行测试验证"
    echo "  -a, --analyze  分析转换结果"
    echo ""
    echo "参数:"
    echo "  输入目录       包含Markdown文件的目录路径"
    echo "  输出文件       输出的Excel文件名"
    echo ""
    echo "示例:"
    echo "  $0                                    # 使用默认设置"
    echo "  $0 /path/to/md/files                 # 指定输入目录"
    echo "  $0 /path/to/md/files output.xlsx     # 指定输入和输出"
    echo "  $0 --test                            # 运行测试"
    echo "  $0 --analyze                         # 分析结果"
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        exit 1
    fi
    
    # 检查UV
    if command -v uv &> /dev/null; then
        print_info "使用UV环境管理"
        PYTHON_CMD="uv run python"
    else
        print_warning "UV未安装，使用系统Python"
        PYTHON_CMD="python3"
    fi
    
    # 检查必要的Python包
    print_info "检查Python依赖包..."
    if ! $PYTHON_CMD -c "import pandas, openpyxl" 2>/dev/null; then
        print_error "缺少必要的Python包: pandas, openpyxl"
        print_info "请运行以下命令安装依赖:"
        if command -v uv &> /dev/null; then
            echo "  uv add pandas openpyxl"
        else
            echo "  pip install pandas openpyxl"
        fi
        exit 1
    fi
    
    print_success "依赖检查通过"
}

# 运行转换器
run_converter() {
    local input_dir="$1"
    local output_file="$2"
    
    print_info "开始转换..."
    print_info "输入目录: $input_dir"
    print_info "输出文件: $output_file"
    
    if [ -n "$input_dir" ] && [ -n "$output_file" ]; then
        $PYTHON_CMD md_to_excel_converter.py "$input_dir" "$output_file"
    elif [ -n "$input_dir" ]; then
        $PYTHON_CMD md_to_excel_converter.py "$input_dir"
    else
        $PYTHON_CMD md_to_excel_converter.py
    fi
    
    if [ $? -eq 0 ]; then
        print_success "转换完成！"
        
        # 显示输出文件信息
        if [ -n "$output_file" ]; then
            output_path="$output_file"
        else
            output_path="测试用例汇总.xlsx"
        fi
        
        if [ -f "$output_path" ]; then
            file_size=$(ls -lh "$output_path" | awk '{print $5}')
            print_info "输出文件: $output_path (大小: $file_size)"
        fi
    else
        print_error "转换失败"
        exit 1
    fi
}

# 运行测试
run_test() {
    print_info "运行测试验证..."
    $PYTHON_CMD test_converter.py
    
    if [ $? -eq 0 ]; then
        print_success "测试通过"
    else
        print_error "测试失败"
        exit 1
    fi
}

# 分析结果
analyze_results() {
    print_info "分析转换结果..."
    $PYTHON_CMD example_usage.py
    
    if [ $? -eq 0 ]; then
        print_success "分析完成"
    else
        print_error "分析失败"
        exit 1
    fi
}

# 主函数
main() {
    echo "========================================"
    echo "  Markdown测试用例转Excel转换器"
    echo "========================================"
    echo ""
    
    # 检查依赖
    check_dependencies
    echo ""
    
    # 解析命令行参数
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -t|--test)
            run_test
            exit 0
            ;;
        -a|--analyze)
            analyze_results
            exit 0
            ;;
        *)
            # 运行转换器
            run_converter "$1" "$2"
            ;;
    esac
    
    echo ""
    print_success "所有操作完成！"
}

# 运行主函数
main "$@"
