"""
示例 1: 基础图片分析
演示如何使用 GLM-4V 引擎分析单张图片
"""

import asyncio
from vl_engine_glm import GLMVLEngine


async def main():
    """主函数"""
    # 初始化 GLM 引擎
    # 确保 .env 文件中配置了 GLM_API_KEY
    engine = GLMVLEngine(
        model_name="glm-4v-plus-0111"  # 或使用 "glm-4v-flash" 以获得更快速度
    )

    # 初始化引擎
    print("正在初始化 GLM 引擎...")
    if not await engine.initialize():
        print("✗ 引擎初始化失败")
        return

    # 分析图片
    image_path = "example.jpg"  # 替换为你的图片路径

    print(f"\n正在分析图片: {image_path}")

    result = await engine.analyze_image(
        image_path=image_path,
        prompt="请详细描述这张图片的内容"
    )

    # 显示结果
    if result["success"]:
        print("\n✓ 分析成功")
        print(f"使用引擎: {result['engine']}")
        print(f"使用模型: {result['model']}")
        print(f"\n分析结果:")
        print("-" * 60)
        print(result["result"])
        print("-" * 60)
    else:
        print(f"\n✗ 分析失败: {result['error']}")

    # 显示引擎状态
    print(f"\n引擎状态:")
    status = engine.get_status()
    print(f"  总请求数: {status['metrics']['total_requests']}")
    print(f"  成功率: {status['metrics']['success_rate']}")
    print(f"  平均延迟: {status['metrics']['avg_latency_ms']} ms")


if __name__ == "__main__":
    print("=" * 60)
    print("VL 引擎基础示例")
    print("=" * 60)

    asyncio.run(main())
