"""
示例 4: 批量处理
演示如何批量处理多个 PDF 文件，带并发控制
"""

import asyncio
from pathlib import Path
from pdf_converter import VLPDFConverter
from vl_engine_glm import GLMVLEngine
from vl_engine_manager import VLEngineManager


class BatchProcessor:
    """批量处理器"""

    def __init__(self, max_concurrent: int = 3):
        """
        初始化批量处理器

        Args:
            max_concurrent: 最大并发数
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.converter = None

    async def process_single_pdf(self, pdf_path: Path, output_dir: Path):
        """
        处理单个 PDF

        Args:
            pdf_path: PDF 文件路径
            output_dir: 输出目录

        Returns:
            处理结果
        """
        async with self.semaphore:
            try:
                print(f"\n开始处理: {pdf_path.name}")

                result = await self.converter.convert_pdf_to_markdown(
                    pdf_path=pdf_path,
                    job_id=f"batch_{pdf_path.stem}",
                    document_id=pdf_path.stem
                )

                # 保存结果
                output_path = output_dir / f"{pdf_path.stem}.md"
                output_path.write_text(result["markdown"], encoding="utf-8")

                metadata = result["metadata"]
                print(f"✓ 完成: {pdf_path.name}")
                print(f"  页数: {metadata['page_count']}")
                print(f"  成功率: {metadata['success_pages']/metadata['page_count']*100:.1f}%")

                return {
                    "file": pdf_path.name,
                    "success": True,
                    "pages": metadata["page_count"]
                }

            except Exception as e:
                print(f"✗ 失败: {pdf_path.name} - {str(e)}")
                return {
                    "file": pdf_path.name,
                    "success": False,
                    "error": str(e)
                }

    async def process_batch(self, pdf_dir: Path, output_dir: Path):
        """
        批量处理 PDF

        Args:
            pdf_dir: PDF 目录
            output_dir: 输出目录
        """
        # 创建输出目录
        output_dir.mkdir(exist_ok=True)

        # 获取所有 PDF 文件
        pdf_files = list(pdf_dir.glob("*.pdf"))

        if not pdf_files:
            print(f"✗ 在 {pdf_dir} 中未找到 PDF 文件")
            return

        print(f"找到 {len(pdf_files)} 个 PDF 文件")

        # 初始化转换器
        manager = VLEngineManager()
        glm_engine = GLMVLEngine(model_name="glm-4v-flash")
        manager.register_engine(glm_engine)
        manager.set_primary_engine("glm")

        self.converter = VLPDFConverter(vl_manager=manager)

        # 并发处理
        tasks = [
            self.process_single_pdf(pdf, output_dir)
            for pdf in pdf_files
        ]

        results = await asyncio.gather(*tasks)

        # 统计结果
        success_count = sum(1 for r in results if r["success"])
        total_pages = sum(r.get("pages", 0) for r in results if r["success"])

        print(f"\n{'=' * 60}")
        print(f"批量处理完成！")
        print(f"{'=' * 60}")
        print(f"总文件数: {len(results)}")
        print(f"成功: {success_count}")
        print(f"失败: {len(results) - success_count}")
        print(f"总页数: {total_pages}")
        print(f"输出目录: {output_dir}")


async def main():
    """主函数"""
    processor = BatchProcessor(max_concurrent=2)  # 同时处理 2 个文件

    # 设置输入输出目录
    pdf_dir = Path("pdfs")  # 放置 PDF 文件的目录
    output_dir = Path("output")  # 输出目录

    if not pdf_dir.exists():
        print(f"✗ PDF 目录不存在: {pdf_dir}")
        print("\n请创建 'pdfs' 目录并放入 PDF 文件")
        return

    await processor.process_batch(pdf_dir, output_dir)


if __name__ == "__main__":
    print("=" * 60)
    print("PDF 批量处理示例")
    print("=" * 60)
    print("\n使用说明:")
    print("1. 创建 'pdfs' 目录")
    print("2. 将要处理的 PDF 文件放入该目录")
    print("3. 运行此脚本")
    print("4. 结果将保存在 'output' 目录")
    print("=" * 60)

    asyncio.run(main())
