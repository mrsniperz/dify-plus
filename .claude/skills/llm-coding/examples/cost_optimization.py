"""
成本优化示例

演示如何通过合理配置和优化策略降低LLM调用成本
"""

import asyncio
from src.services.llm_engine_manager import LLMEngineManager
from src.services.glm_engine import GLMEngine
from src.services.deepseek_engine import DeepSeekEngine


async def example_1_free_engine_for_development():
    """示例1：开发环境使用免费引擎"""
    manager = LLMEngineManager()

    # 注册免费引擎
    manager.register_engine(GLMEngine())  # GLM-4.5-Flash完全免费

    await manager.initialize_engines()
    manager.set_primary_engine("glm")

    # 开发和测试阶段，零成本
    result = await manager.extract_with_schema(
        content="测试内容...",
        json_schema={}
    )

    print(f"开发测试成本: ${result.cost_usd:.6f}")  # $0.000000


async def example_2_cache_optimization():
    """示例2：利用DeepSeek缓存降低成本"""
    manager = LLMEngineManager()
    manager.register_engine(DeepSeekEngine())

    await manager.initialize_engines()
    manager.set_primary_engine("deepseek")

    # ❌ 错误：每次都生成不同的prompt
    # for item in items:
    #     prompt = f"当前时间: {datetime.now()}，请提取..."
    #     result = await manager.extract_with_schema(
    #         content=item,
    #         system_prompt=prompt  # 无法触发缓存
    #     )

    # ✅ 正确：使用固定的prompt
    FIXED_SYSTEM_PROMPT = "你是一个专业的数据提取助手。请从文本中提取结构化信息。"

    items = ["内容1", "内容2", "内容3", ...]

    total_cost = 0
    for item in items:
        result = await manager.extract_with_schema(
            content=item,
            json_schema={},
            system_prompt=FIXED_SYSTEM_PROMPT  # 固定不变，触发缓存
        )
        total_cost += result.cost_usd

    print(f"批量处理成本（缓存优化后）: ${total_cost:.6f}")
    # 第一次调用：¥2.0/1M tokens（缓存未命中）
    # 后续调用：¥0.2/1M tokens（缓存命中）


async def example_3_budget_control():
    """示例3：预算控制和自动切换"""
    manager = LLMEngineManager(
        enable_cost_monitoring=True
    )

    # 注册引擎
    manager.register_engine(DeepSeekEngine())  # 低成本
    manager.register_engine(GLMEngine())  # 免费

    await manager.initialize_engines()

    # 设置预算限制
    manager.cost_monitor.daily_budget_usd = 10.0
    manager.cost_monitor.monthly_budget_usd = 100.0

    # 生产环境使用低成本引擎
    manager.set_primary_engine("deepseek")
    manager.set_fallback_engine("glm")

    # 处理请求前检查预算
    if manager.cost_monitor.check_budget('daily'):
        result = await manager.extract_with_schema(
            content="内容...",
            json_schema={}
        )
    else:
        print("⚠️ 每日预算已达上限，切换到免费引擎")
        manager.set_primary_engine("glm")
        result = await manager.extract_with_schema(
            content="内容...",
            json_schema={}
        )


async def example_4_engine_selection_by_scenario():
    """示例4：根据场景选择最优引擎"""
    manager = LLMEngineManager()

    # 注册所有可用引擎
    manager.register_engine(GLMEngine())         # 免费
    manager.register_engine(DeepSeekEngine())    # 低成本
    manager.register_engine(KimiEngine())        # 长上下文

    await manager.initialize_engines()

    # 根据任务特征选择引擎
    async def optimal_extract(content: str, schema: dict):
        content_length = len(content)

        # 长文本：使用Kimi（支持128K上下文）
        if content_length > 50000:
            print("使用Kimi引擎（长文本处理）")
            return await manager.extract_with_schema(
                content=content,
                json_schema=schema,
                primary_engine="kimi",
                fallback_engine="deepseek"
            )

        # 高频简单任务：使用GLM（免费）
        elif content_length < 1000:
            print("使用GLM引擎（免费快速）")
            return await manager.extract_with_schema(
                content=content,
                json_schema=schema,
                primary_engine="glm",
                fallback_engine="deepseek"
            )

        # 常规任务：使用DeepSeek（低成本，缓存优化）
        else:
            print("使用DeepSeek引擎（低成本+缓存）")
            return await manager.extract_with_schema(
                content=content,
                json_schema=schema,
                primary_engine="deepseek",
                fallback_engine="glm"
            )

    # 使用
    result = await optimal_extract("内容...", {})


async def example_5_cost_monitoring():
    """示例5：成本监控和告警"""
    manager = LLMEngineManager(
        enable_cost_monitoring=True
    )

    manager.register_engine(DeepSeekEngine())
    manager.register_engine(GLMEngine())

    await manager.initialize_engines()
    manager.set_primary_engine("deepseek")

    # 设置告警阈值
    manager.cost_monitor.alert_threshold = 0.8  # 80%时告警

    # 定期检查成本
    async def monitor_cost():
        monitor = manager.cost_monitor

        # 每日成本检查
        if monitor.daily_cost >= monitor.daily_budget_usd * monitor.alert_threshold:
            print(f"⚠️ 每日成本告警: ${monitor.daily_cost:.2f} / ${monitor.daily_budget_usd}")
            # 发送告警通知
            # send_alert(...)

            # 自动切换到免费引擎
            manager.set_primary_engine("glm")

        # 每月成本检查
        if monitor.monthly_cost >= monitor.monthly_budget_usd * monitor.alert_threshold:
            print(f"⚠️ 每月成本告警: ${monitor.monthly_cost:.2f} / ${monitor.monthly_budget_usd}")

        # 获取优化建议
        suggestions = monitor.get_optimization_suggestions()
        if suggestions:
            print("\n💡 成本优化建议:")
            for suggestion in suggestions:
                print(f"  - {suggestion}")

    # 模拟使用
    await manager.extract_with_schema(content="...", json_schema={})
    await monitor_cost()


async def example_6_batch_cost_optimization():
    """示例6：批量处理成本优化"""
    from asyncio import Semaphore

    manager = LLMEngineManager()
    manager.register_engine(DeepSeekEngine())
    manager.register_engine(GLMEngine())

    await manager.initialize_engines()
    manager.set_primary_engine("deepseek")

    # 固定prompt（触发缓存）
    FIXED_PROMPT = "你是一个专业的数据提取助手。"

    # 限制并发（避免触发限流）
    semaphore = Semaphore(10)

    async def process_item(item):
        async with semaphore:
            return await manager.extract_with_schema(
                content=item,
                json_schema={},
                system_prompt=FIXED_PROMPT  # 固定触发缓存
            )

    # 批量处理
    items = [f"内容{i}" for i in range(100)]
    tasks = [process_item(item) for item in items]
    results = await asyncio.gather(*tasks)

    # 统计成本
    total_cost = sum(r.cost_usd for r in results if r.success)
    print(f"100个请求总成本: ${total_cost:.4f}")
    print(f"平均每请求: ${total_cost/100:.6f}")


if __name__ == "__main__":
    print("=== 示例1：开发环境使用免费引擎 ===")
    asyncio.run(example_1_free_engine_for_development())

    print("\n=== 示例2：利用DeepSeek缓存 ===")
    asyncio.run(example_2_cache_optimization())

    print("\n=== 示例3：预算控制 ===")
    asyncio.run(example_3_budget_control())

    print("\n=== 示例4：场景化引擎选择 ===")
    asyncio.run(example_4_engine_selection_by_scenario())

    print("\n=== 示例5：成本监控 ===")
    asyncio.run(example_5_cost_monitoring())

    print("\n=== 示例6：批量处理优化 ===")
    asyncio.run(example_6_batch_cost_optimization())
