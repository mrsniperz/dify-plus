"""
VL 引擎管理器
管理多个VL引擎的生命周期、故障转移和性能监控
"""

from typing import Dict, Any, Optional
import asyncio
import time

from vl_engine_base import VLEngineBase


class VLEngineManager:
    """VL 引擎管理器"""

    def __init__(self):
        """初始化管理器"""
        self.engines: Dict[str, VLEngineBase] = {}
        self.primary_engine: Optional[str] = None
        self.fallback_engine: Optional[str] = None
        self.auto_switch: bool = True
        self.request_timeout_seconds: int = 30

    def register_engine(self, engine: VLEngineBase) -> None:
        """
        注册引擎

        Args:
            engine: VL 引擎实例
        """
        self.engines[engine.engine_name] = engine
        print(f"✓ 已注册引擎: {engine.engine_name} ({engine.model_name})")

    async def initialize_engines(self) -> bool:
        """
        初始化所有已注册的引擎

        Returns:
            是否至少有一个引擎初始化成功
        """
        print("开始初始化 VL 引擎...")
        results = []

        for engine_name, engine in self.engines.items():
            try:
                success = await engine.initialize()
                results.append(success)
                if success:
                    print(f"✓ {engine_name} 引擎初始化成功")
                else:
                    print(f"✗ {engine_name} 引擎初始化失败")
            except Exception as e:
                print(f"✗ {engine_name} 引擎初始化出错: {str(e)}")
                results.append(False)

        return any(results)

    def set_primary_engine(self, engine_name: str) -> None:
        """
        设置首选引擎

        Args:
            engine_name: 引擎名称
        """
        if engine_name not in self.engines:
            raise ValueError(f"引擎 {engine_name} 未注册")
        self.primary_engine = engine_name
        print(f"主引擎设置为: {engine_name}")

    def set_fallback_engine(self, engine_name: str) -> None:
        """
        设置回退引擎

        Args:
            engine_name: 引擎名称
        """
        if engine_name not in self.engines:
            raise ValueError(f"引擎 {engine_name} 未注册")
        self.fallback_engine = engine_name
        print(f"备用引擎设置为: {engine_name}")

    def get_current_engine(self) -> Optional[str]:
        """获取当前主引擎名称"""
        return self.primary_engine

    def get_fallback_engine(self) -> Optional[str]:
        """获取当前备用引擎名称"""
        return self.fallback_engine

    async def analyze_image(
        self,
        image_path: str,
        prompt: str,
        primary_engine: Optional[str] = None,
        fallback_engine: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        分析图片（支持故障转移）

        Args:
            image_path: 图片路径
            prompt: 分析提示词
            primary_engine: 首选引擎（可选）
            fallback_engine: 回退引擎（可选）
            **kwargs: 其他参数

        Returns:
            分析结果
        """
        primary = primary_engine or self.primary_engine
        fallback = fallback_engine or self.fallback_engine

        if not primary:
            return {
                "success": False,
                "error": "未配置主引擎"
            }

        # 尝试主引擎
        print(f"尝试使用主引擎: {primary}")
        result = await self._try_engine(primary, image_path, prompt, **kwargs)

        if result.get("success"):
            return result

        # 如果主引擎失败，尝试回退引擎
        if self.auto_switch and fallback and fallback != primary:
            print(f"主引擎失败，尝试备用引擎: {fallback}")
            result = await self._try_engine(fallback, image_path, prompt, **kwargs)
            if result.get("success"):
                return result

        return result

    async def _try_engine(
        self,
        engine_name: str,
        image_path: str,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        尝试使用指定引擎

        Args:
            engine_name: 引擎名称
            image_path: 图片路径
            prompt: 分析提示词
            **kwargs: 其他参数

        Returns:
            分析结果
        """
        if engine_name not in self.engines:
            return {"success": False, "error": f"引擎 {engine_name} 不存在"}

        engine = self.engines[engine_name]
        if not engine.enabled:
            return {"success": False, "error": f"引擎 {engine_name} 未启用"}

        try:
            start_time = time.time()
            result = await asyncio.wait_for(
                engine.analyze_image(image_path, prompt, **kwargs),
                timeout=self.request_timeout_seconds
            )
            duration_ms = (time.time() - start_time) * 1000

            engine.record_request(duration_ms, result.get("success", False))
            return result

        except asyncio.TimeoutError:
            engine.record_request(self.request_timeout_seconds * 1000, False, "Timeout")
            return {"success": False, "error": f"引擎 {engine_name} 超时"}
        except Exception as e:
            engine.record_request(0, False, str(e))
            return {"success": False, "error": f"引擎 {engine_name} 错误: {str(e)}"}

    def get_status(self) -> Dict[str, Any]:
        """
        获取所有引擎状态

        Returns:
            引擎状态字典
        """
        return {
            engine_name: engine.get_status()
            for engine_name, engine in self.engines.items()
        }

    async def health_check(self) -> Dict[str, bool]:
        """
        检查所有引擎健康状态

        Returns:
            引擎健康状态字典
        """
        results = {}
        for engine_name, engine in self.engines.items():
            try:
                results[engine_name] = await engine.health_check()
            except Exception as e:
                print(f"健康检查失败 {engine_name}: {str(e)}")
                results[engine_name] = False
        return results
