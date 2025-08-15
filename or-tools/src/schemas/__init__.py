"""
数据结构定义层 (Schemas Module)

定义API请求和响应的数据结构，以及数据验证规则。
使用Pydantic进行数据验证和序列化，确保API接口的数据一致性。

主要结构：
- request_schemas: API请求数据结构
  - PlanRequest: 排程计划请求
  - EventRequest: 事件处理请求
  - ConfigRequest: 配置变更请求
  
- response_schemas: API响应数据结构
  - PlanResponse: 排程计划响应
  - SummaryResponse: 汇总信息响应
  - ErrorResponse: 错误响应
  
- validation: 数据验证工具
  - 业务规则验证器
  - 数据格式验证器
  - 约束条件验证器

设计原则：
- 类型安全: 完整的类型注解和验证
- 可扩展: 支持添加新的数据结构
- 文档化: 详细的字段说明和示例
- 向后兼容: 保持API版本兼容性
"""

# 数据结构导入将在具体实现时添加
# from .request_schemas import (
#     PlanRequest,
#     EventRequest,
#     HandoverRequest,
#     ConfigRequest,
# )
# from .response_schemas import (
#     PlanResponse,
#     SummaryResponse,
#     ErrorResponse,
#     AuditResponse,
# )
# from .validation import (
#     validate_time_window,
#     validate_resource_allocation,
#     validate_gate_conditions,
# )

__all__ = [
    # 数据结构将在实现时添加
]
