"""
GLM-4V 视觉语言引擎实现
使用智谱AI的GLM-4V模型进行图片分析
"""

import os
import base64
from typing import Dict, Any, Optional
import asyncio

from vl_engine_base import VLEngineBase

# 尝试导入 zhipuai SDK
try:
    from zhipuai import ZhipuAI
    ZHIPUAI_AVAILABLE = True
except ImportError:
    ZHIPUAI_AVAILABLE = False
    ZhipuAI = None


class GLMVLEngine(VLEngineBase):
    """GLM-4V 视觉语言引擎"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: str = "https://open.bigmodel.cn/api/paas/v4/",
        model_name: str = "glm-4v-plus-0111",
        timeout: int = 60
    ):
        """
        初始化 GLM 引擎

        Args:
            api_key: API 密钥（如未提供则从环境变量 GLM_API_KEY 读取）
            api_base: API 基础 URL
            model_name: 模型名称
            timeout: 请求超时时间（秒）
        """
        super().__init__("glm", model_name)
        self.api_key = api_key or os.getenv("GLM_API_KEY", "")
        self.api_base = api_base
        self.timeout = timeout
        self.client = None

    async def initialize(self) -> bool:
        """
        初始化 GLM 引擎

        Returns:
            是否初始化成功
        """
        try:
            if not self.api_key:
                print("⚠️  GLM API 密钥未配置")
                self._enabled = False
                return False

            if not ZHIPUAI_AVAILABLE:
                print("⚠️  zhipuai SDK 未安装，请运行: pip install zhipuai")
                self._enabled = False
                return False

            # 初始化客户端
            self.client = ZhipuAI(api_key=self.api_key)
            self._enabled = True
            print(f"✓ GLM 引擎初始化成功 (模型: {self.model_name})")
            return True

        except Exception as e:
            print(f"✗ GLM 引擎初始化失败: {str(e)}")
            self._enabled = False
            return False

    async def analyze_image(
        self,
        image_path: str,
        prompt: str,
        temperature: float = 0.5,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        分析图片

        Args:
            image_path: 图片路径
            prompt: 分析提示词
            temperature: 创造性参数 (0-1)
            max_tokens: 最大输出令牌数
            **kwargs: 其他参数

        Returns:
            分析结果
        """
        if not self._enabled or not self.client:
            return {
                "success": False,
                "error": "GLM 引擎未初始化",
                "engine": "glm",
                "model": self.model_name
            }

        try:
            # 验证文件存在
            if not os.path.exists(image_path):
                return {
                    "success": False,
                    "error": f"图片文件不存在: {image_path}",
                    "engine": "glm",
                    "model": self.model_name
                }

            # 编码图片
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            # 构建消息
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ]

            # 调用 API
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                ),
                timeout=self.timeout
            )

            # 解析响应
            if response.choices and response.choices[0].message:
                result_text = response.choices[0].message.content
                return {
                    "success": True,
                    "result": result_text,
                    "engine": "glm",
                    "model": self.model_name
                }
            else:
                return {
                    "success": False,
                    "error": "GLM API 返回空响应",
                    "engine": "glm",
                    "model": self.model_name
                }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "GLM API 超时",
                "engine": "glm",
                "model": self.model_name
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"GLM API 错误: {str(e)}",
                "engine": "glm",
                "model": self.model_name
            }

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            引擎是否健康可用
        """
        if not self._enabled or not self.client:
            return False

        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model_name,
                    messages=[{"role": "user", "content": "ping"}],
                    max_tokens=10
                ),
                timeout=10
            )
            return True
        except Exception:
            return False
