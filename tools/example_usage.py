#!/usr/bin/env python3
"""
使用示例脚本

演示如何使用md_to_excel_converter.py进行不同的转换操作
"""

import os
import sys
from pathlib import Path
from md_to_excel_converter import MarkdownToExcelConverter


def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    input_dir = "/Users/sniperz/dockerfiles/dify-plus/docs/测试用例/"
    output_file = "基本转换结果.xlsx"
    
    converter = MarkdownToExcelConverter(input_dir, output_file)
    converter.run()
    
    print(f"转换完成，输出文件: {output_file}")


def example_custom_output():
    """自定义输出文件示例"""
    print("\n=== 自定义输出文件示例 ===")
    
    input_dir = "/Users/sniperz/dockerfiles/dify-plus/docs/测试用例/"
    output_file = "知识库管理测试用例_2025-09-05.xlsx"
    
    converter = MarkdownToExcelConverter(input_dir, output_file)
    converter.run()
    
    print(f"转换完成，输出文件: {output_file}")


def example_analyze_results():
    """分析转换结果示例"""
    print("\n=== 分析转换结果示例 ===")
    
    import pandas as pd
    
    excel_file = "测试用例汇总.xlsx"
    
    if Path(excel_file).exists():
        df = pd.read_excel(excel_file)
        
        print(f"分析文件: {excel_file}")
        print(f"总测试用例数: {len(df)}")
        
        # 分析测试状态分布
        print("\n测试状态分布:")
        status_counts = df['测试状态'].value_counts()
        for status, count in status_counts.items():
            percentage = (count / len(df)) * 100
            print(f"  {status}: {count} 个 ({percentage:.1f}%)")
        
        # 分析各模块测试用例数量
        print("\n各模块测试用例数量:")
        file_counts = df['文件名'].value_counts()
        for filename, count in file_counts.items():
            module_name = filename.replace('知识库管理_', '').replace('_测试用例.md', '')
            print(f"  {module_name}: {count} 个")
        
        # 查找需要补充实际结果的测试用例
        empty_results = df[df['实际结果'].isna() | (df['实际结果'] == '')]
        print(f"\n需要补充实际结果的测试用例: {len(empty_results)} 个")
        
        if len(empty_results) > 0:
            print("示例:")
            for idx, row in empty_results.head(3).iterrows():
                print(f"  - {row['测试用例ID']}: {row['测试用例名称']}")
    
    else:
        print(f"文件不存在: {excel_file}")


def example_batch_processing():
    """批量处理示例"""
    print("\n=== 批量处理示例 ===")
    
    # 假设有多个不同的测试用例目录
    directories = [
        "/Users/sniperz/dockerfiles/dify-plus/docs/测试用例/",
        # 可以添加更多目录
    ]
    
    for i, directory in enumerate(directories, 1):
        if Path(directory).exists():
            output_file = f"批量转换结果_{i}.xlsx"
            print(f"处理目录 {i}: {directory}")
            
            converter = MarkdownToExcelConverter(directory, output_file)
            converter.run()
            
            print(f"完成，输出: {output_file}")
        else:
            print(f"目录不存在: {directory}")


def example_error_handling():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")
    
    # 测试不存在的目录
    try:
        converter = MarkdownToExcelConverter("/不存在的目录/", "错误测试.xlsx")
        converter.run()
    except Exception as e:
        print(f"预期的错误: {e}")
    
    # 测试空目录
    empty_dir = Path("temp_empty_dir")
    empty_dir.mkdir(exist_ok=True)
    
    try:
        converter = MarkdownToExcelConverter(str(empty_dir), "空目录测试.xlsx")
        converter.run()
    except Exception as e:
        print(f"空目录处理: {e}")
    finally:
        # 清理临时目录
        if empty_dir.exists():
            empty_dir.rmdir()


def main():
    """主函数 - 运行所有示例"""
    print("Markdown转Excel转换器使用示例")
    print("=" * 50)
    
    # 基本使用
    # example_basic_usage()
    
    # 自定义输出
    # example_custom_output()
    
    # 分析结果
    example_analyze_results()
    
    # 批量处理
    # example_batch_processing()
    
    # 错误处理
    # example_error_handling()
    
    print("\n" + "=" * 50)
    print("所有示例运行完成！")
    
    print("\n使用提示:")
    print("1. 取消注释相应的示例函数来运行特定示例")
    print("2. 根据需要修改输入目录和输出文件名")
    print("3. 确保有足够的磁盘空间存储输出文件")


if __name__ == "__main__":
    main()
