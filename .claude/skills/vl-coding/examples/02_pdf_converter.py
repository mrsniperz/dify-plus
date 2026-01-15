"""
示例 2: PDF 转 Markdown
演示如何使用 VL 引擎将 PDF 文档转换为 Markdown 格式
"""

import asyncio
from pathlib import Path
from pdf_converter import VLPDFConverter
from vl_engine_glm import GLMVLEngine
from vl_engine_manager import VLEngineManager


async def main():
    """主函数"""
    # 创建 VL 管理器
    manager = VLEngineManager()

    # 注册 GLM 引擎
    glm_engine = GLMVLEngine(model_name="glm-4v-flash")  # 使用快速版本
    manager.register_engine(glm_engine)
    manager.set_primary_engine("glm")

    # 创建转换器
    converter = VLPDFConverter(vl_manager=manager)

    # 转换 PDF
    pdf_path = Path("document.pdf")  # 替换为你的 PDF 路径

    if not pdf_path.exists():
        print(f"✗ PDF 文件不存在: {pdf_path}")
        print("\n请将 PDF 文件放在当前目录并命名为 'document.pdf'")
        print("或者修改代码中的 pdf_path 变量")
        return

    print(f"开始转换 PDF: {pdf_path.name}")

    result = await converter.convert_pdf_to_markdown(
        pdf_path=pdf_path,
        job_id="demo_job",
        document_id="demo_doc"
    )

    # 保存结果
    output_path = Path("output.md")
    output_path.write_text(result["markdown"], encoding="utf-8")

    print(f"\n✓ Markdown 已保存到: {output_path}")

    # 显示统计信息
    metadata = result["metadata"]
    print(f"\n转换统计:")
    print(f"  总页数: {metadata['page_count']}")
    print(f"  成功: {metadata['success_pages']}")
    print(f"  失败: {metadata['failed_pages']}")
    print(f"  总字符数: {metadata['total_text_length']}")


if __name__ == "__main__":
    print("=" * 60)
    print("PDF 转 Markdown 示例")
    print("=" * 60)

    asyncio.run(main())
