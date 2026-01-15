"""
PDF 转 Markdown 转换器
使用 VL 引擎将 PDF 文档转换为 Markdown 格式
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

# 尝试导入 PDF 转图片库
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    convert_from_path = None

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    fitz = None

from vl_engine_manager import VLEngineManager


class VLPDFConverter:
    """VL PDF 转 Markdown 转换器"""

    def __init__(self, vl_manager: VLEngineManager = None):
        """
        初始化转换器

        Args:
            vl_manager: VL 引擎管理器（如未提供则创建新的）
        """
        self.vl_manager = vl_manager or VLEngineManager()

        # 检查依赖
        if not PDF2IMAGE_AVAILABLE and not PYMUPDF_AVAILABLE:
            print("⚠️  警告: pdf2image 和 PyMuPDF 都未安装")
            print("   请运行: pip install pdf2image")
        elif PDF2IMAGE_AVAILABLE:
            print("✓ 使用 pdf2image 进行 PDF 转换")
        else:
            print("✓ 使用 PyMuPDF 进行 PDF 转换")

    async def convert_pdf_to_markdown(
        self,
        pdf_path: Path,
        job_id: str,
        document_id: str,
        analysis_prompt: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        转换 PDF 为 Markdown 格式

        Args:
            pdf_path: PDF 文件路径
            job_id: 作业 ID
            document_id: 文档 ID
            analysis_prompt: 自定义分析提示词
            **kwargs: 其他参数

        Returns:
            转换结果字典
        """
        print(f"\n开始处理 PDF: {pdf_path}")

        try:
            # 1. 初始化 VL 引擎
            if not await self.vl_manager.initialize_engines():
                raise RuntimeError("无法初始化任何 VL 引擎")

            # 2. 将 PDF 转换为图片
            print("正在将 PDF 转换为图片...")
            images = self._pdf_to_images(pdf_path)
            if not images:
                raise RuntimeError("PDF 转图片失败")

            print(f"✓ PDF 已转换为 {len(images)} 张图片")

            # 3. 使用 VL 引擎分析每张图片
            pages = []
            prompt = analysis_prompt or self._build_default_prompt()

            for i, image_path in enumerate(images, 1):
                print(f"正在分析页面 {i}/{len(images)}...")

                try:
                    # 调用 VL 引擎
                    result = await self.vl_manager.analyze_image(
                        image_path=image_path,
                        prompt=prompt,
                        **kwargs
                    )

                    if result.get("success"):
                        result_text = result.get("result", "")
                        page_content = {
                            "page_number": i,
                            "text": result_text,
                            "raw_text": result_text,
                            "markdown": result_text,
                            "metadata": {
                                "vl_engine": result.get("engine", "unknown"),
                                "vl_model": result.get("model", "unknown"),
                            }
                        }
                        pages.append(page_content)
                        print(f"  ✓ 页面 {i} 分析成功")
                    else:
                        error_msg = result.get("error", "未知错误")
                        print(f"  ✗ 页面 {i} 分析失败: {error_msg}")
                        page_content = {
                            "page_number": i,
                            "text": "",
                            "raw_text": "",
                            "markdown": f"<!-- 页面 {i} 分析失败: {error_msg} -->",
                            "metadata": {
                                "vl_engine": "failed",
                                "vl_model": "unknown",
                                "error": error_msg,
                            }
                        }
                        pages.append(page_content)

                except Exception as e:
                    print(f"  ✗ 处理页面 {i} 时出错: {str(e)}")
                    page_content = {
                        "page_number": i,
                        "text": "",
                        "raw_text": "",
                        "markdown": f"<!-- 页面 {i} 处理出错: {str(e)} -->",
                        "metadata": {
                            "vl_engine": "error",
                            "vl_model": "unknown",
                            "error": str(e),
                        }
                    }
                    pages.append(page_content)

                finally:
                    # 清理临时图片
                    try:
                        os.unlink(image_path)
                    except Exception:
                        pass

            # 4. 生成完整的 Markdown
            markdown = self._generate_markdown(pages)

            # 5. 提取原始文本
            raw_text = "\n\n---\n\n".join([page.get("raw_text", "") for page in pages])

            # 6. 统计信息
            success_pages = sum(
                1 for page in pages
                if page.get("text") and not page.get("text").startswith("<!--")
            )
            failed_pages = len(pages) - success_pages
            total_text_length = sum(len(page.get("text", "")) for page in pages)

            print(f"\n✓ 处理完成！")
            print(f"  总页数: {len(pages)}")
            print(f"  成功: {success_pages}")
            print(f"  失败: {failed_pages}")
            print(f"  成功率: {success_pages/len(pages)*100:.1f}%")

            return {
                "markdown": markdown,
                "raw_text": raw_text,
                "pages": pages,
                "metadata": {
                    "engine": "vl",
                    "page_count": len(pages),
                    "image_count": len(images),
                    "success_pages": success_pages,
                    "failed_pages": failed_pages,
                    "total_text_length": total_text_length,
                }
            }

        except Exception as e:
            print(f"\n✗ PDF 转换失败: {str(e)}")
            raise

    def _pdf_to_images(self, pdf_path: Path) -> List[str]:
        """
        将 PDF 转换为图片

        Args:
            pdf_path: PDF 文件路径

        Returns:
            图片文件路径列表
        """
        image_paths = []

        try:
            # 优先使用 pdf2image
            if PDF2IMAGE_AVAILABLE:
                images = convert_from_path(
                    str(pdf_path),
                    dpi=200,
                    fmt="jpeg",
                    thread_count=4
                )

                # 保存图片到临时文件
                for i, image in enumerate(images):
                    with tempfile.NamedTemporaryFile(
                        suffix=f"_page_{i + 1}.jpg",
                        delete=False
                    ) as tmp:
                        image.save(tmp.name, "JPEG")
                        image_paths.append(tmp.name)

            # 回退到 PyMuPDF
            elif PYMUPDF_AVAILABLE:
                pdf_document = fitz.open(str(pdf_path))

                for page_num in range(len(pdf_document)):
                    page = pdf_document.load_page(page_num)

                    # 设置缩放因子
                    mat = fitz.Matrix(2.0, 2.0)
                    pix = page.get_pixmap(matrix=mat)

                    with tempfile.NamedTemporaryFile(
                        suffix=f"_page_{page_num + 1}.jpg",
                        delete=False
                    ) as tmp:
                        pix.save(tmp.name)
                        image_paths.append(tmp.name)

                pdf_document.close()

            else:
                raise RuntimeError("没有可用的 PDF 转图片工具")

            return image_paths

        except Exception as e:
            # 清理已创建的图片文件
            for path in image_paths:
                try:
                    os.unlink(path)
                except Exception:
                    pass

            raise RuntimeError(f"PDF 转图片失败: {str(e)}") from e

    def _build_default_prompt(self) -> str:
        """
        构建默认分析提示词

        Returns:
            提示词
        """
        return """作为文档分析专家，请提取此页面中的所有内容：

提取要求：
1. 文本内容：提取所有文字，保持原文不变
2. 表格内容：识别表格数据，保持表格结构
3. 布局结构：保持文档原始结构
4. 格式标记：使用 Markdown 格式输出

输出格式：
- 使用标准 Markdown 语法
- 表格使用 Markdown 表格格式
- 标题使用 # ## ### 等层级
- 列表使用 - 或 1. 2. 3. 等格式

注意事项：
- 不要翻译或改写，保持原文内容
- 不要添加额外解释或评论
- 确保提取内容完整准确

请严格按照要求提取页面内容。"""

    def _generate_markdown(self, pages: List[Dict[str, Any]]) -> str:
        """
        生成完整的 Markdown

        Args:
            pages: 页面内容列表

        Returns:
            完整的 Markdown 文本
        """
        markdown_parts = []

        for i, page in enumerate(pages):
            # 添加页码标题
            markdown_parts.append(f"\n\n## 第 {page['page_number']} 页\n")

            # 添加页面内容
            page_content = page.get("markdown", "")
            if page_content:
                markdown_parts.append(page_content)

            # 添加页面分隔符（最后一页除外）
            if i < len(pages) - 1:
                markdown_parts.append("\n\n---\n")

        return "".join(markdown_parts)
