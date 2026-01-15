"""
LLM引擎管理器使用示例

演示如何使用LLMEngineManager进行多引擎管理和故障转移
"""

import asyncio
from src.services.llm_engine_manager import LLMEngineManager
from src.services.glm_engine import GLMEngine
from src.services.deepseek_engine import DeepSeekEngine
from src.services.kimi_engine import KimiEngine


async def main():
    # ========== 1. 创建管理器 ==========
    manager = LLMEngineManager(
        auto_switch=True,                # 启用自动故障转移
        request_timeout_seconds=60,      # 请求超时
        max_retries=2,                   # 最大重试次数
        health_check_interval=300,       # 健康检查间隔（秒）
        enable_cost_monitoring=True      # 启用成本监控
    )

    # ========== 2. 注册引擎 ==========
    manager.register_engine(GLMEngine())
    manager.register_engine(DeepSeekEngine())
    manager.register_engine(KimiEngine())

    # ========== 3. 初始化所有引擎 ==========
    success = await manager.initialize_engines()
    if not success:
        print("Failed to initialize any engine")
        return

    # ========== 4. 设置主引擎和回退引擎 ==========
    # 开发环境：使用免费的GLM
    manager.set_primary_engine("glm")
    manager.set_fallback_engine("deepseek")

    # 生产环境：使用低成本的DeepSeek
    # manager.set_primary_engine("deepseek")
    # manager.set_fallback_engine("glm")

    # ========== 5. 结构化抽取示例 ==========
    schema = {
        "type": "object",
        "properties": {
            "company_name": {
                "type": "string",
                "description": "公司名称"
            },
            "contact_person": {
                "type": "string",
                "description": "联系人姓名"
            },
            "phone": {
                "type": "string",
                "description": "联系电话"
            },
            "email": {
                "type": "string",
                "description": "电子邮箱"
            }
        },
        "required": ["company_name", "contact_person"]
    }

    content = """
    尊敬的负责人：

    我公司（北京科技有限公司）的法人代表张三，联系电话：13800138000，
    邮箱：zhangsan@example.com。希望与贵公司建立业务合作关系。

    此致
    敬礼
    """

    # 固定系统提示（触发DeepSeek缓存）
    FIXED_SYSTEM_PROMPT = "你是一个专业的信息提取助手，请从文本中提取结构化数据。"

    result = await manager.extract_with_schema(
        content=content,
        json_schema=schema,
        system_prompt=FIXED_SYSTEM_PROMPT,
        temperature=0.1
    )

    # ========== 6. 处理结果 ==========
    if result.success:
        print("✅ 提取成功")
        print(f"数据: {result.extracted_data}")
        print(f"模型: {result.model_used}")
        print(f"Token使用: {result.token_usage}")
        print(f"成本: ${result.cost_usd:.6f}")
        print(f"耗时: {result.processing_time_ms:.2f}ms")
    else:
        print(f"❌ 提取失败: {result.error_message}")

    # ========== 7. 查看引擎状态 ==========
    print("\n========== 引擎状态 ==========")
    for engine_name, engine in manager.engines.items():
        status = engine.get_status()
        metrics = status["metrics"]
        print(f"\n{engine_name}:")
        print(f"  可用: {status['available']}")
        print(f"  请求总数: {metrics['total_requests']}")
        print(f"  成功率: {metrics['success_rate']:.2%}")
        print(f"  平均延迟: {metrics['latency_ms']:.2f}ms")
        print(f"  总成本: ${metrics['total_cost_usd']:.6f}")

    # ========== 8. 查看成本监控 ==========
    if manager.cost_monitor:
        print("\n========== 成本统计 ==========")
        print(f"每日成本: ${manager.cost_monitor.daily_cost:.4f} / ${manager.cost_monitor.daily_budget_usd}")
        print(f"每月成本: ${manager.cost_monitor.monthly_cost:.4f} / ${manager.cost_monitor.monthly_budget_usd}")


async def dynamic_engine_switch_example():
    """动态切换引擎示例"""
    manager = LLMEngineManager()
    manager.register_engine(GLMEngine())
    manager.register_engine(DeepSeekEngine())

    await manager.initialize_engines()

    # 根据任务类型动态选择引擎
    async def smart_extract(content: str, task_type: str):
        if task_type == "long_text":
            primary = "kimi"  # 长文本处理
            fallback = "deepseek"
        elif task_type == "high_frequency":
            primary = "glm"  # 免费，高频调用
            fallback = "deepseek"
        else:
            primary = "deepseek"  # 默认低成本
            fallback = "glm"

        return await manager.extract_with_schema(
            content=content,
            json_schema={},
            primary_engine=primary,
            fallback_engine=fallback
        )

    # 使用
    result = await smart_extract("长文本内容...", "long_text")


async def batch_processing_example():
    """批量处理示例"""
    import asyncio
    from asyncio import Semaphore

    manager = LLMEngineManager()
    manager.register_engine(GLMEngine())
    manager.register_engine(DeepSeekEngine())

    await manager.initialize_engines()
    manager.set_primary_engine("deepseek")
    manager.set_fallback_engine("glm")

    # 限制并发数
    semaphore = Semaphore(10)

    async def process_with_limit(item):
        async with semaphore:
            return await manager.extract_with_schema(
                content=item,
                json_schema={}
            )

    # 并发处理
    items = ["内容1", "内容2", "内容3", ...]
    tasks = [process_with_limit(item) for item in items]
    results = await asyncio.gather(*tasks)

    return results


if __name__ == "__main__":
    asyncio.run(main())
