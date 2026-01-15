"""
示例 3: 多引擎故障转移
演示如何配置多个引擎并实现自动故障转移
"""

import asyncio
from vl_engine_manager import VLEngineManager
from vl_engine_glm import GLMVLEngine
from vl_engine_openai import OpenAIVLEngine


async def main():
    """主函数"""
    # 创建管理器
    manager = VLEngineManager()

    # 注册 GLM 引擎
    print("注册 GLM 引擎...")
    glm_engine = GLMVLEngine(model_name="glm-4v-flash")
    manager.register_engine(glm_engine)

    # 注册 OpenAI 引擎（可选）
    # print("注册 OpenAI 引擎...")
    # openai_engine = OpenAIVLEngine(model_name="gpt-4o")
    # manager.register_engine(openai_engine)

    # 设置主引擎和备用引擎
    manager.set_primary_engine("glm")
    manager.set_fallback_engine("openai")  # 如果注册了 OpenAI

    # 初始化所有引擎
    print("\n初始化引擎...")
    if not await manager.initialize_engines():
        print("✗ 没有引擎初始化成功")
        return

    # 健康检查
    print("\n执行健康检查...")
    health = await manager.health_check()
    for engine_name, is_healthy in health.items():
        status = "✓ 健康" if is_healthy else "✗ 不健康"
        print(f"  {engine_name}: {status}")

    # 分析图片（自动故障转移）
    image_path = "example.jpg"  # 替换为你的图片路径

    print(f"\n分析图片: {image_path}")
    print("（如果主引擎失败，会自动切换到备用引擎）")

    result = await manager.analyze_image(
        image_path=image_path,
        prompt="请提取这张图片中的所有文本内容"
    )

    # 显示结果
    if result["success"]:
        print(f"\n✓ 分析成功")
        print(f"使用引擎: {result['engine']}")
        print(f"使用模型: {result['model']}")
        print(f"\n结果:")
        print("-" * 60)
        print(result["result"])
        print("-" * 60)
    else:
        print(f"\n✗ 分析失败: {result['error']}")

    # 显示所有引擎状态
    print(f"\n引擎状态:")
    statuses = manager.get_status()
    for engine_name, status in statuses.items():
        print(f"\n{engine_name}:")
        print(f"  模型: {status['model']}")
        print(f"  启用: {status['enabled']}")
        print(f"  请求数: {status['metrics']['total_requests']}")
        print(f"  成功率: {status['metrics']['success_rate']}")


if __name__ == "__main__":
    print("=" * 60)
    print("多引擎故障转移示例")
    print("=" * 60)

    asyncio.run(main())
