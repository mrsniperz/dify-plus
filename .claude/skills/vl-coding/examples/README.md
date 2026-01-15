# VL 视觉语言引擎示例代码

这是一套完整的、独立的 VL 视觉语言引擎实现，可以在任何项目中使用。

## 文件说明

### 核心文件

- **vl_engine_base.py** - VL 引擎基类，定义所有引擎必须实现的接口
- **vl_engine_manager.py** - 引擎管理器，支持多引擎和故障转移
- **vl_engine_glm.py** - GLM-4V 引擎实现
- **vl_engine_openai.py** - GPT-4V 引擎实现
- **pdf_converter.py** - PDF 转 Markdown 转换器

### 示例文件

- **01_basic_engine.py** - 基础图片分析示例
- **02_pdf_converter.py** - PDF 转换示例
- **03_multi_engine.py** - 多引擎故障转移示例
- **04_batch_processing.py** - 批量处理示例

## 快速开始

### 1. 安装依赖

```bash
# 核心依赖
pip install pdf2image PyMuPDF
pip install zhipuai  # GLM-4V
pip install openai   # GPT-4V (可选)

# 其他依赖
pip install Pillow asyncio
```

### 2. 系统依赖

```bash
# Ubuntu/Debian
sudo apt-get install poppler-utils

# macOS
brew install poppler
```

### 3. 配置环境变量

创建 `.env` 文件：

```env
# GLM-4V 配置（推荐）
GLM_API_KEY=your_glm_api_key_here

# OpenAI 配置（可选）
OPENAI_API_KEY=your_openai_api_key_here
```

或者在代码中直接设置：

```python
engine = GLMVLEngine(
    api_key="your_api_key_here",
    model_name="glm-4v-flash"
)
```

### 4. 运行示例

```bash
# 示例 1: 基础图片分析
python 01_basic_engine.py

# 示例 2: PDF 转 Markdown
python 02_pdf_converter.py

# 示例 3: 多引擎故障转移
python 03_multi_engine.py

# 示例 4: 批量处理
python 04_batch_processing.py
```

## 使用指南

### 分析单张图片

```python
from vl_engine_glm import GLMVLEngine
import asyncio

async def analyze():
    engine = GLMVLEngine()
    await engine.initialize()

    result = await engine.analyze_image(
        image_path="example.jpg",
        prompt="描述这张图片"
    )

    if result["success"]:
        print(result["result"])

asyncio.run(analyze())
```

### PDF 转 Markdown

```python
from pdf_converter import VLPDFConverter
from pathlib import Path
import asyncio

async def convert():
    converter = VLPDFConverter()

    result = await converter.convert_pdf_to_markdown(
        pdf_path=Path("document.pdf"),
        job_id="demo",
        document_id="doc"
    )

    # 保存结果
    Path("output.md").write_text(result["markdown"])

asyncio.run(convert())
```

### 创建自定义引擎

```python
from vl_engine_base import VLEngineBase

class MyVLEngine(VLEngineBase):
    def __init__(self):
        super().__init__("myengine", "my-model-v1")

    async def initialize(self) -> bool:
        # 初始化逻辑
        self._enabled = True
        return True

    async def analyze_image(self, image_path: str, prompt: str, **kwargs):
        # 分析逻辑
        return {
            "success": True,
            "result": "分析结果",
            "engine": "myengine",
            "model": self.model_name
        }

    async def health_check(self) -> bool:
        # 健康检查逻辑
        return True
```

## 模型推荐

### GLM-4V 系列

| 模型 | 特点 | 适用场景 |
|------|------|----------|
| glm-4v-flash | 快速、成本低 | 大批量处理 |
| glm-4v | 平衡性能和速度 | 一般文档 |
| glm-4v-plus | 高质量输出 | 复杂文档 |
| glm-4v-plus-0111 | 最新版本 | **推荐** |

### GPT-4V 系列

| 模型 | 特点 | 适用场景 |
|------|------|----------|
| gpt-4-vision-preview | 视觉能力强 | 复杂图表 |
| gpt-4o | 性价比高 | 通用场景 |

## 性能优化

### 并发控制

```python
from asyncio import Semaphore

semaphore = Semaphore(3)  # 最多同时处理 3 个

async def process_with_limit():
    async with semaphore:
        result = await engine.analyze_image(...)
```

### 错误重试

```python
async def analyze_with_retry(engine, image_path, max_retries=3):
    for attempt in range(max_retries):
        result = await engine.analyze_image(image_path, prompt)
        if result["success"]:
            return result
        await asyncio.sleep(2 ** attempt)  # 指数退避
    return {"success": False, "error": "Max retries exceeded"}
```

### 缓存结果

```python
import hashlib
import pickle

class CachedEngine:
    def __init__(self, engine, cache_dir="cache"):
        self.engine = engine
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    async def analyze_image(self, image_path, prompt):
        cache_key = hashlib.md5(Path(image_path).read_bytes()).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        if cache_file.exists():
            return pickle.load(open(cache_file, "rb"))

        result = await self.engine.analyze_image(image_path, prompt)
        pickle.dump(result, open(cache_file, "wb"))
        return result
```

## 故障排查

### PDF 转图片失败

```bash
# 检查 poppler
pdftoppm -v

# Ubuntu/Debian
sudo apt-get install poppler-utils

# macOS
brew install poppler
```

### API 调用失败

- 检查 API 密钥是否正确
- 确认网络连接
- 验证 API 配额

### 内存占用过高

```python
# 降低 DPI
images = convert_from_path(pdf_path, dpi=150)  # 默认 200

# 分批处理
for i in range(0, len(images), 10):
    batch = images[i:i+10]
    process_batch(batch)
```

## 最佳实践

1. **选择合适的模型**
   - 大批量处理：使用 glm-4v-flash
   - 高质量要求：使用 glm-4v-plus-0111

2. **控制并发数**
   - 建议同时处理 2-3 个文件
   - 避免超过 API 限流

3. **实现错误处理**
   - 使用重试机制
   - 保存中间结果
   - 记录详细日志

4. **优化成本**
   - 实现结果缓存
   - 使用故障转移
   - 监控 API 使用量

## 扩展阅读

- [GLM-4V 文档](https://open.bigmodel.cn/dev/api)
- [OpenAI Vision 文档](https://platform.openai.com/docs/guides/vision)
- [项目主文档](../skill.md)

## 许可

这些示例代码可以自由使用和修改，适用于任何项目。
