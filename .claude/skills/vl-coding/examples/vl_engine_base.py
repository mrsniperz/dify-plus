"""
VL 引擎基类
定义所有视觉语言引擎必须实现的接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import time


class VLEngineMetrics:
    """VL 引擎性能指标"""

    def __init__(self):
        self.total_requests = 0
        self.failed_requests = 0
        self.total_duration_ms = 0.0
        self.last_request_time = None
        self.last_error = None

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 0.0
        return (self.total_requests - self.failed_requests) / self.total_requests

    @property
    def avg_latency_ms(self) -> float:
        """平均延迟"""
        if self.total_requests == 0:
            return 0.0
        return self.total_duration_ms / self.total_requests

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "success_rate": f"{self.success_rate:.1%}",
            "avg_latency_ms": f"{self.avg_latency_ms:.1f}",
            "last_request_time": self.last_request_time.isoformat() if self.last_request_time else None,
            "last_error": self.last_error
        }


class VLEngineBase(ABC):
    """VL 引擎基类"""

    def __init__(self, engine_name: str, model_name: str):
        """
        初始化引擎

        Args:
            engine_name: 引擎名称（如 'glm', 'baidu'）
            model_name: 模型名称（如 'glm-4v-plus-0111', 'gpt-4o'）
        """
        self.engine_name = engine_name
        self.model_name = model_name
        self.metrics = VLEngineMetrics()
        self._enabled = False

    @property
    def enabled(self) -> bool:
        """引擎是否启用"""
        return self._enabled

    @abstractmethod
    async def initialize(self) -> bool:
        """
        初始化引擎

        Returns:
            是否初始化成功
        """
        pass

    @abstractmethod
    async def analyze_image(
        self,
        image_path: str,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        分析图片

        Args:
            image_path: 图片路径
            prompt: 分析提示词
            **kwargs: 其他参数（如 temperature, max_tokens）

        Returns:
            分析结果字典，必须包含:
            - success: bool - 是否成功
            - result: str - 分析结果文本（成功时）
            - engine: str - 引擎名称
            - model: str - 模型名称
            - error: str - 错误信息（失败时）
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            引擎是否健康可用
        """
        pass

    def record_request(self, duration_ms: float, success: bool, error: Optional[str] = None):
        """
        记录请求指标

        Args:
            duration_ms: 请求耗时（毫秒）
            success: 是否成功
            error: 错误信息
        """
        self.metrics.total_requests += 1
        if not success:
            self.metrics.failed_requests += 1
            self.metrics.last_error = error
        self.metrics.total_duration_ms += duration_ms
        self.metrics.last_request_time = datetime.now(timezone.utc)

    def get_status(self) -> Dict[str, Any]:
        """
        获取引擎状态

        Returns:
            引擎状态字典
        """
        return {
            "engine": self.engine_name,
            "model": self.model_name,
            "enabled": self.enabled,
            "available": self.enabled,
            "metrics": self.metrics.to_dict()
        }
