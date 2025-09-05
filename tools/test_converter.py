#!/usr/bin/env python3
"""
测试转换器脚本

用于验证md_to_excel_converter.py的转换结果
"""

import pandas as pd
from pathlib import Path


def test_excel_output():
    """测试Excel输出文件"""
    excel_file = "测试用例汇总.xlsx"
    
    if not Path(excel_file).exists():
        print(f"错误: Excel文件不存在: {excel_file}")
        return False
    
    try:
        # 读取Excel文件
        df = pd.read_excel(excel_file)
        
        print(f"Excel文件读取成功: {excel_file}")
        print(f"总行数: {len(df)}")
        print(f"总列数: {len(df.columns)}")
        print("\n列名:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i}. {col}")
        
        print("\n数据统计:")
        print(f"  - 不同文件数量: {df['文件名'].nunique()}")
        print(f"  - 测试用例总数: {len(df)}")
        
        # 按文件统计
        print("\n各文件测试用例数量:")
        file_counts = df['文件名'].value_counts()
        for filename, count in file_counts.items():
            print(f"  - {filename}: {count} 个")
        
        # 按状态统计
        print("\n测试状态统计:")
        status_counts = df['测试状态'].value_counts()
        for status, count in status_counts.items():
            print(f"  - {status}: {count} 个")
        
        # 显示前几行数据示例
        print("\n前3行数据示例:")
        print(df.head(3).to_string(index=False, max_colwidth=30))
        
        return True
        
    except Exception as e:
        print(f"读取Excel文件时发生错误: {e}")
        return False


def main():
    """主函数"""
    print("开始测试转换器输出...")
    print("=" * 50)
    
    success = test_excel_output()
    
    print("=" * 50)
    if success:
        print("✅ 测试通过！转换器工作正常。")
    else:
        print("❌ 测试失败！请检查转换器。")


if __name__ == "__main__":
    main()
