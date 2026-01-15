"""
简单LLM引擎实现示例

演示如何实现一个符合LLMEngineBase规范的简单引擎
"""

from typing import Dict, Any, Optional, List
from src.services.llm_engine_base import LLMEngineBase, LLMExtractionResult
from src.core.logging import get_logger

logger = get_logger(__name__)


class SimpleOpenAIEngine(LLMEngineBase):
    """简单的OpenAI兼容引擎实现

    适用于任何兼容OpenAI API的服务（如DeepSeek、Moonshot等）
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 2
    ):
        """初始化引擎

        Args:
            api_key: API密钥
            base_url: API基础URL
            model_name: 模型名称
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        super().__init__(
            engine_name="simple_openai",
            model_name=model_name or "gpt-3.5-turbo"
        )

        self.api_key = api_key
        self.base_url = base_url or "https://api.openai.com/v1"
        self.timeout = timeout
        self.max_retries = max_retries

        # 定价（示例：GPT-3.5-turbo）
        self.input_cost_per_1k = 0.0005
        self.output_cost_per_1k = 0.0015

        self.client = None

    async def initialize(self) -> bool:
        """初始化引擎"""
        try:
            from openai import AsyncOpenAI

            if not self.api_key:
                logger.warning("API key not provided")
                return False

            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout
            )

            # 健康检查
            is_healthy = await self.health_check()
            if is_healthy:
                self._enabled = True
                self._initialized = True
                logger.info(f"{self.engine_name} engine initialized")

            return is_healthy

        except Exception as e:
            logger.error(f"Failed to initialize {self.engine_name}: {str(e)}")
            return False

    async def extract_with_schema(
        self,
        content: str,
        json_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        **kwargs
    ) -> LLMExtractionResult:
        """使用JSON Schema进行结构化抽取"""
        import time
        import json
        import asyncio

        start_time = time.time()

        try:
            # 构建Prompt
            prompt = self._build_extraction_prompt(content, json_schema, system_prompt)

            # 调用API
            response = await self._call_api_with_retry(
                prompt=prompt,
                temperature=temperature,
                max_retries=self.max_retries
            )

            # 解析响应
            content_text = response.choices[0].message.content
            extracted_data = json.loads(content_text)

            processing_time = (time.time() - start_time) * 1000

            # 记录指标
            cost = self.record_request(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                duration_ms=processing_time,
                success=True
            )

            return LLMExtractionResult(
                success=True,
                extracted_data=extracted_data,
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

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMExtractionResult:
        """通用聊天补全"""
        import time

        start_time = time.time()

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            processing_time = (time.time() - start_time) * 1000

            cost = self.record_request(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                duration_ms=processing_time,
                success=True
            )

            return LLMExtractionResult(
                success=True,
                extracted_data={"content": response.choices[0].message.content},
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
            logger.error(f"Chat completion failed: {str(e)}")

            self.record_request(0, 0, processing_time, False, str(e))

            return LLMExtractionResult(
                success=False,
                extracted_data={},
                error_message=str(e),
                processing_time_ms=processing_time
            )

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """计算请求成本（美元）"""
        input_cost = (input_tokens / 1000) * self.input_cost_per_1k
        output_cost = (output_tokens / 1000) * self.output_cost_per_1k
        return input_cost + output_cost

    def _build_extraction_prompt(
        self,
        content: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None
    ) -> str:
        """构建抽取Prompt"""
        default_system = "你是一个专业的数据提取助手，请从文本中提取结构化信息。"
        final_system = system_prompt or default_system

        schema_desc = self._format_schema_description(schema)

        return f"""{final_system}

请从以下文本中提取信息，按照JSON Schema格式返回：

{schema_desc}

待提取文本：
{content}

要求：
1. 严格按照JSON Schema格式返回
2. 只返回JSON对象，不要包含其他内容
3. 如果某个字段无法提取，使用null
4. 确保JSON格式正确
"""

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

    async def _call_api_with_retry(
        self,
        prompt: str,
        temperature: float,
        max_retries: int
    ):
        """带重试的API调用"""
        import asyncio

        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature,
                        response_format={"type": "json_object"}
                    ),
                    timeout=self.timeout
                )

                return response

            except asyncio.TimeoutError:
                last_exception = Exception(f"Timeout after {self.timeout}s")
                if attempt < max_retries:
                    wait_time = 1 * (attempt + 1)
                    logger.warning(f"Timeout, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue

            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    wait_time = 1 * (attempt + 1)
                    logger.warning(f"API error, retrying: {str(e)}")
                    await asyncio.sleep(wait_time)
                    continue

        raise last_exception
