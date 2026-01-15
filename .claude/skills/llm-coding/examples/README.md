# LLM Coding Skill - 示例代码

本文件夹包含 LLM 编程的实用示例代码，可直接复制到项目中使用。

## 文件说明

### 1. simple_engine.py
**简单引擎实现示例**

演示如何实现一个符合 `LLMEngineBase` 规范的 OpenAI 兼容引擎。

**包含内容：**
- 完整的引擎类实现
- 结构化抽取（extract_with_schema）
- 聊天补全（chat_completion）
- 健康检查（health_check）
- 重试机制和错误处理
- 成本计算（calculate_cost）

**适用场景：**
- 学习如何创建新的 LLM 引擎
- 作为实现其他引擎的模板

---

### 2. engine_usage.py
**引擎管理器使用示例**

演示如何使用 `LLMEngineManager` 进行多引擎管理和故障转移。

**包含内容：**
- 创建和初始化管理器
- 注册多个引擎（GLM、DeepSeek、Kimi）
- 设置主引擎和回退引擎
- 结构化抽取调用
- 查看引擎状态和性能指标
- 成本监控统计
- 动态切换引擎
- 批量并发处理

**适用场景：**
- 学习如何使用引擎管理器
- 了解多引擎故障转移机制
- 实现生产环境的 LLM 服务

---

### 3. cost_optimization.py
**成本优化示例**

演示如何通过各种策略降低 LLM 调用成本。

**包含内容：**
- 开发环境使用免费引擎（GLM）
- 利用 DeepSeek Prompt 缓存降低成本
- 预算控制和自动切换
- 根据场景选择最优引擎
- 成本监控和告警
- 批量处理优化

**适用场景：**
- 学习成本优化策略
- 实现预算控制机制
- 优化生产环境的 LLM 成本

## 使用方式

### 直接运行示例

```bash
# 运行简单引擎示例
python examples/simple_engine.py

# 运行引擎管理器示例
python examples/engine_usage.py

# 运行成本优化示例
python examples/cost_optimization.py
```

### 复制到项目

根据需要，将示例代码复制到项目中：

```bash
# 复制简单引擎实现
cp examples/simple_engine.py src/services/my_custom_engine.py

# 复制使用示例
cp examples/engine_usage.py tests/test_llm_integration.py
```

## 依赖要求

所有示例都需要以下依赖：

```bash
# 核心依赖
- openai (OpenAI API SDK)
- zhipuai (智谱AI SDK)
- asyncio (异步支持)

# 项目依赖
- src.services.llm_engine_base
- src.services.llm_engine_manager
- src.core.logging
```

## 注意事项

1. **API 密钥配置**
   - 所有示例都需要配置相应的 API 密钥
   - 通过环境变量或直接传入构造函数

2. **成本提醒**
   - 某些示例会调用实际 API，产生费用
   - 建议先使用免费引擎（GLM）进行测试

3. **错误处理**
   - 示例代码包含基础错误处理
   - 生产环境需要更完善的错误处理和日志记录

4. **并发控制**
   - 批量处理示例使用了信号量限制并发
   - 根据实际情况调整并发数

## 扩展建议

基于这些示例，你可以：

1. **实现自定义引擎**
   - 参考 `simple_engine.py` 实现其他 LLM 服务

2. **集成到项目**
   - 参考 `engine_usage.py` 集成到现有项目

3. **优化成本**
   - 参考 `cost_optimization.py` 实现成本控制

4. **添加监控**
   - 扩展示例，添加 Prometheus 指标导出
   - 实现告警通知机制

## 相关文档

- LLM Engine 基类：`src/services/llm_engine_base.py`
- 引擎管理器：`src/services/llm_engine_manager.py`
- 具体实现：
  - `src/services/glm_engine.py`
  - `src/services/deepseek_engine.py`
  - `src/services/kimi_engine.py`
