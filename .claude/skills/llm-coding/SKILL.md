---
name: llm-coding
description: 在创建或编辑LLM相关代码时使用此技能。它提供LLM多引擎架构的编码标准、最佳实践和规范，包括引擎抽象层、故障转移、成本监控、性能优化和错误处理。
---

# LLM 编码标准

此技能为 LLM 多引擎架构开发提供全面的编码标准和最佳实践。在创建新的 LLM 引擎、修改 LLM 管理器或实现 LLM 相关功能时使用此技能。

## 何时使用此技能

在以下情况下使用此技能：
- 创建新的 LLM 引擎实现（继承 LLMEngineBase）
- 实现结构化数据提取功能
- 配置 LLM 引擎管理器和故障转移
- 实现成本监控和性能指标收集
- 处理 LLM API 调用和错误重试
- 优化 Prompt 以降低成本
- 实现健康检查和监控
- 设计 LLM 相关的服务层代码

## 架构设计原则

### 核心架构层次

```
应用层 (Application Layer)
    ↓
引擎管理层 (LLMEngineManager)
    ↓
引擎抽象层 (LLMEngineBase)
    ↓
引擎实现层 (GLMEngine/DeepSeekEngine/KimiEngine)
    ↓
第三方 API 层
```

### 设计原则

1. **单一职责原则 (SRP)**
   - LLMEngineBase：定义统一接口
   - LLMEngineManager：管理多引擎和故障转移
   - 具体引擎类：实现特定 API 调用

2. **依赖倒置原则 (DIP)**
   - 依赖 LLMEngineBase 抽象，而非具体实现
   - 通过管理器统一调度，降低耦合

3. **开闭原则 (OCP)**
   - 对扩展开放：添加新引擎只需继承基类
   - 对修改关闭：无需修改现有代码

4. **接口隔离原则 (ISP)**
   - 提供专注的接口：extract_with_schema、chat_completion、health_check

## 引擎基类规范

### LLMEngineBase 必需方法

所有 LLM 引擎必须实现以下抽象方法：

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from src.services.llm_engine_base import LLMEngineBase, LLMExtractionResult

class CustomEngine(LLMEngineBase):
    """自定义LLM引擎"""

    @abstractmethod
    async def initialize(self) -> bool:
        """初始化引擎，验证API密钥和连接

        Returns:
            是否初始化成功
        """
        pass

    @abstractmethod
    async def extract_with_schema(
        self,
        content: str,
        json_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        **kwargs
    ) -> LLMExtractionResult:
        """使用JSON Schema进行结构化抽取

        Args:
            content: 待抽取的文本内容
            json_schema: JSON Schema定义
            system_prompt: 系统提示词（可选）
            temperature: 温度参数，控制随机性
            **kwargs: 其他参数

        Returns:
            LLMExtractionResult: 抽取结果
        """
        pass

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMExtractionResult:
        """通用聊天补全接口

        Args:
            messages: 对话消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数

        Returns:
            LLMExtractionResult: 生成结果
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查，验证引擎可用性

        Returns:
            引擎是否健康可用
        """
        pass

    @abstractmethod
    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """计算请求成本（美元）

        Args:
            input_tokens: 输入token数
            output_tokens: 输出token数

        Returns:
            成本（美元）
        """
        pass
```

### 引擎初始化规范

```python
class CustomEngine(LLMEngineBase):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 2
    ):
        """初始化引擎配置

        Args:
            api_key: API密钥（优先级高于环境变量）
            model_name: 模型名称
            base_url: API基础URL
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        super().__init__(
            engine_name="custom",
            model_name=model_name or "default-model"
        )

        # 从环境变量获取配置
        self.api_key = api_key or os.getenv("CUSTOM_API_KEY", "")
        self.base_url = base_url or os.getenv("CUSTOM_BASE_URL", "")
        self.timeout = timeout
        self.max_retries = max_retries

        # 定价配置（单位：美元/1K tokens）
        self.input_cost_per_1k = 0.001
        self.output_cost_per_1k = 0.002

        # 客户端初始化
        self.client = None

    async def initialize(self) -> bool:
        """初始化引擎"""
        try:
            if not self.api_key:
                logger.warning("API key not provided")
                return False

            # 初始化客户端
            self.client = self._create_client()

            # 验证连接
            is_healthy = await self.health_check()
            if is_healthy:
                self._enabled = True
                self._initialized = True
                logger.info(f"{self.engine_name} engine initialized successfully")
            return is_healthy

        except Exception as e:
            logger.error(f"Failed to initialize {self.engine_name}: {str(e)}")
            return False
```

## 结构化抽取实现规范

### 核心实现流程

```python
async def extract_with_schema(
    self,
    content: str,
    json_schema: Dict[str, Any],
    system_prompt: Optional[str] = None,
    temperature: float = 0.1,
    **kwargs
) -> LLMExtractionResult:
    """使用JSON Schema进行结构化抽取"""
    start_time = time.time()

    try:
        # 1. 参数验证
        if not content or not json_schema:
            return LLMExtractionResult(
                success=False,
                extracted_data={},
                error_message="Content and schema are required"
            )

        # 2. 构建Prompt
        prompt = self._build_extraction_prompt(
            content=content,
            schema=json_schema,
            system_prompt=system_prompt
        )

        # 3. 调用API（带重试）
        response = await self._call_api_with_retry(
            prompt=prompt,
            temperature=temperature,
            max_retries=self.max_retries
        )

        # 4. 解析响应
        extracted_data = self._parse_response(response)

        # 5. 验证结果
        validated_data = self._validate_result(extracted_data, json_schema)

        processing_time = (time.time() - start_time) * 1000

        # 6. 记录指标
        cost = self.record_request(
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            duration_ms=processing_time,
            success=True
        )

        return LLMExtractionResult(
            success=True,
            extracted_data=validated_data,
            confidence=0.9,
            processing_time_ms=processing_time,
            model_used=self.model_name,
            token_usage={
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            cost_usd=cost
        )

    except Exception as e:
        processing_time = (time.time() - start_time) * 1000

        logger.error(f"Extraction failed: {str(e)}")
        self.record_request(0, 0, processing_time, False, str(e))

        return LLMExtractionResult(
            success=False,
            extracted_data={},
            error_message=str(e),
            processing_time_ms=processing_time
        )
```

### Prompt 构建规范

```python
def _build_extraction_prompt(
    self,
    content: str,
    schema: Dict[str, Any],
    system_prompt: Optional[str] = None
) -> str:
    """构建抽取Prompt

    Args:
        content: 待抽取文本
        schema: JSON Schema
        system_prompt: 系统提示词

    Returns:
        完整Prompt
    """
    # 默认系统提示
    default_system = "你是一个专业的数据提取助手，请从文本中提取结构化信息。"

    # 优先使用自定义系统提示（注意：保持不变以触发缓存）
    final_system = system_prompt or default_system

    # 构建Schema说明
    schema_desc = self._format_schema_description(schema)

    # 组装完整Prompt
    prompt = f"""{final_system}

请从以下文本中提取信息，按照JSON Schema格式返回：

{schema_desc}

待提取文本：
{content}

要求：
1. 严格按照JSON Schema格式返回
2. 只返回JSON对象，不要包含其他内容
3. 如果某个字段无法提取，使用null或默认值
4. 确保JSON格式正确，可以被解析
"""
    return prompt

def _format_schema_description(self, schema: Dict[str, Any]) -> str:
    """格式化Schema描述"""
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    descriptions = []
    for field_name, field_info in properties.items():
        field_type = field_info.get("type", "string")
        field_desc = field_info.get("description", "")
        is_required = "必需" if field_name in required else "可选"

        descriptions.append(
            f"- {field_name} ({field_type}, {is_required}): {field_desc}"
        )

    return "\n".join(descriptions)
```

### 重试机制实现

```python
async def _call_api_with_retry(
    self,
    prompt: str,
    temperature: float,
    max_retries: int
) -> Any:
    """带重试的API调用

    Args:
        prompt: 完整提示词
        temperature: 温度参数
        max_retries: 最大重试次数

    Returns:
        API响应

    Raises:
        Exception: 重试耗尽后仍失败
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            # 调用API
            response = await asyncio.wait_for(
                self._make_api_call(prompt, temperature),
                timeout=self.timeout
            )

            return response

        except asyncio.TimeoutError:
            last_exception = Exception(f"API timeout after {self.timeout}s")
            if attempt < max_retries:
                wait_time = 1 * (attempt + 1)  # 递增延迟
                logger.warning(
                    f"Timeout, retrying in {wait_time}s ({attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(wait_time)
                continue

        except Exception as e:
            last_exception = e

            # 错误分类
            error_type = self._classify_error(e)

            # 不可重试错误
            if error_type in ["authentication_error", "token_limit_error"]:
                raise e

            # 可重试错误
            if attempt < max_retries:
                wait_time = 1 * (attempt + 1)
                logger.warning(
                    f"API error, retrying: {str(e)} ({attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(wait_time)
                continue

    # 重试耗尽
    raise last_exception

def _classify_error(self, e: Exception) -> str:
    """分类错误类型

    Args:
        e: 异常对象

    Returns:
        错误类型
    """
    error_str = str(e).lower()

    if "api_key" in error_str or "unauthorized" in error_str or "401" in error_str:
        return "authentication_error"
    elif "rate" in error_str or "limit" in error_str or "429" in error_str:
        return "rate_limit_error"
    elif "network" in error_str or "connection" in error_str:
        return "network_error"
    elif "token" in error_str and ("limit" in error_str or "exceed" in error_str):
        return "token_limit_error"
    else:
        return "unknown"
```

## 引擎管理器使用规范

### 创建和初始化管理器

```python
from src.services.llm_engine_manager import LLMEngineManager
from src.services.glm_engine import GLMEngine
from src.services.deepseek_engine import DeepSeekEngine
from src.services.kimi_engine import KimiEngine

# 创建管理器
manager = LLMEngineManager(
    auto_switch=True,                # 启用自动故障转移
    request_timeout_seconds=60,      # 请求超时
    max_retries=2,                   # 最大重试次数
    health_check_interval=300,       # 健康检查间隔（秒）
    enable_cost_monitoring=True      # 启用成本监控
)

# 注册引擎
manager.register_engine(GLMEngine())
manager.register_engine(DeepSeekEngine())
manager.register_engine(KimiEngine())

# 初始化所有引擎
await manager.initialize_engines()

# 设置主引擎和回退引擎
manager.set_primary_engine("glm")        # 主引擎
manager.set_fallback_engine("deepseek")  # 回退引擎
```

### 调用结构化抽取

```python
result = await manager.extract_with_schema(
    content="待提取的文本内容...",
    json_schema={
        "type": "object",
        "properties": {
            "field1": {
                "type": "string",
                "description": "字段1说明"
            },
            "field2": {
                "type": "number",
                "description": "字段2说明"
            }
        },
        "required": ["field1"]
    },
    system_prompt="固定系统提示（触发缓存）",
    temperature=0.1
)

if result.success:
    print(f"提取成功: {result.extracted_data}")
    print(f"Token使用: {result.token_usage}")
    print(f"成本: ${result.cost_usd:.6f}")
else:
    print(f"提取失败: {result.error_message}")
```

### 动态切换引擎

```python
# 临时指定引擎
result = await manager.extract_with_schema(
    content="...",
    json_schema=schema,
    primary_engine="deepseek",    # 临时主引擎
    fallback_engine="glm"         # 临时回退引擎
)

# 永久切换引擎
manager.set_primary_engine("kimi")
```

## 成本优化最佳实践

### 1. 引擎选择策略

**开发测试环境：使用免费引擎**
```python
if settings.ENVIRONMENT == "development":
    manager.set_primary_engine("glm")  # 完全免费
    manager.set_fallback_engine("deepseek")
```

**生产环境：使用低成本引擎**
```python
if settings.ENVIRONMENT == "production":
    manager.set_primary_engine("deepseek")  # 成本极低
    manager.set_fallback_engine("glm")
```

**长文本处理：使用长上下文引擎**
```python
if len(content) > 50000:
    manager.set_primary_engine("kimi")  # 支持128K上下文
```

### 2. Prompt 缓存优化

**关键：保持 system_prompt 不变**

```python
# ❌ 错误：每次生成不同 prompt
for item in items:
    system_prompt = f"当前时间: {datetime.now()}，请提取..."
    result = await manager.extract_with_schema(
        content=item,
        system_prompt=system_prompt  # 每次都不同
    )

# ✅ 正确：使用固定 prompt
FIXED_SYSTEM_PROMPT = "你是一个专业的数据提取助手..."

for item in items:
    result = await manager.extract_with_schema(
        content=item,
        system_prompt=FIXED_SYSTEM_PROMPT  # 固定不变
    )
```

### 3. 预算控制

```python
# 检查预算
if not manager.cost_monitor.check_budget('daily'):
    logger.warning("Daily budget exceeded")
    # 切换到免费引擎
    manager.set_primary_engine("glm")

# 设置预算限制
manager.cost_monitor.daily_budget_usd = 10.0
manager.cost_monitor.monthly_budget_usd = 100.0
```

### 4. 批量处理优化

```python
import asyncio
from asyncio import Semaphore

# 限制并发数，避免过载
semaphore = Semaphore(10)

async def process_with_limit(item):
    async with semaphore:
        return await manager.extract_with_schema(
            content=item,
            json_schema=schema
        )

# 并发处理
tasks = [process_with_limit(item) for item in items]
results = await asyncio.gather(*tasks)
```

## 错误处理规范

### 分层错误处理

```python
async def robust_extract(content: str, schema: dict):
    """健壮的抽取函数"""
    try:
        result = await manager.extract_with_schema(
            content=content,
            json_schema=schema
        )

        if result.success:
            return result.extracted_data
        else:
            # 根据错误类型处理
            if "authentication" in result.error_message.lower():
                logger.error("API认证失败，请检查配置")
                # 发送告警
                send_alert("API认证失败")

            elif "rate_limit" in result.error_message.lower():
                logger.warning("触发限流，等待后重试")
                await asyncio.sleep(60)
                return await robust_extract(content, schema)

            elif "budget" in result.error_message.lower():
                logger.error("预算超限，切换到免费引擎")
                manager.set_primary_engine("glm")
                return await robust_extract(content, schema)

            else:
                logger.error(f"提取失败: {result.error_message}")
                return None

    except Exception as e:
        logger.error(f"未预期错误: {str(e)}", exc_info=True)
        return None
```

### 优雅降级

```python
async def extract_with_fallback(content: str, schema: dict):
    """带回退的抽取"""
    # 尝试 LLM 提取
    result = await manager.extract_with_schema(
        content=content,
        json_schema=schema
    )

    if result.success:
        return result.extracted_data

    # LLM 失败，使用规则提取
    logger.warning("LLM提取失败，使用规则提取")
    return rule_based_extract(content)
```

## 日志和监控规范

### 结构化日志

```python
from src.core.logging import get_logger

logger = get_logger(__name__)

# 请求日志
logger.info(
    "LLM extraction request",
    extra={
        "engine": manager.primary_engine,
        "content_length": len(content),
        "schema_fields": list(schema.get("properties", {}).keys())
    }
)

# 响应日志
logger.info(
    "LLM extraction response",
    extra={
        "success": result.success,
        "model_used": result.model_used,
        "token_usage": result.token_usage,
        "cost_usd": result.cost_usd,
        "processing_time_ms": result.processing_time_ms
    }
)
```

### 性能监控

```python
# 定期输出指标
async def monitor_performance():
    while True:
        await asyncio.sleep(300)  # 每5分钟

        for engine_name, engine in manager.engines.items():
            metrics = engine.metrics
            logger.info(
                f"Engine {engine_name} metrics",
                extra={
                    "total_requests": metrics.total_requests,
                    "success_rate": metrics.success_rate,
                    "avg_latency_ms": metrics.avg_latency_ms,
                    "total_cost_usd": metrics.total_cost_usd
                }
            )
```

## 安全实践

### 1. API 密钥管理

```python
# ❌ 错误：硬编码密钥
api_key = "sk-1234567890abcdef"

# ✅ 正确：使用环境变量
api_key = os.getenv("CUSTOM_API_KEY")

# ✅ 更好：使用配置管理
from src.config.settings import settings
api_key = settings.CUSTOM_API_KEY
```

### 2. 敏感信息过滤

```python
import re

def sanitize_log(content: str) -> str:
    """过滤日志中的敏感信息"""
    # 移除邮箱
    content = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        '[EMAIL]',
        content
    )
    # 移除电话
    content = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', content)
    # 移除身份证
    content = re.sub(r'\b\d{17}[\dXx]\b', '[ID_CARD]', content)
    return content

logger.info(f"Processing: {sanitize_log(content)}")
```

## 代码检查清单

在提交 LLM 相关代码前，确保：

- [ ] 继承自 LLMEngineBase 并实现所有必需方法
- [ ] 实现完整的错误处理和重试机制
- [ ] 使用类型提示和文档字符串
- [ ] 记录性能指标和成本
- [ ] 实现健康检查
- [ ] API 密钥通过环境变量管理
- [ ] 过滤日志中的敏感信息
- [ ] 遵循命名约定和代码结构规范
- [ ] 添加适当的测试用例
- [ ] 更新相关文档
