"""
测试模块 (Tests Module)

智能排程系统的测试套件，包含单元测试、集成测试和场景测试。

测试结构：
- unit/: 单元测试，测试各个组件的独立功能
- integration/: 集成测试，测试组件间的协作
- fixtures/: 测试数据和夹具
- mocks/: 模拟对象和存根

测试策略：
- 单元测试覆盖率目标: 核心逻辑 > 90%
- 集成测试覆盖主要业务场景
- 基于test_scenarios.md的场景测试
- 性能测试验证求解SLO

测试工具：
- pytest: 测试框架
- pytest-asyncio: 异步测试支持
- pytest-cov: 覆盖率统计
- httpx: API测试客户端
"""
