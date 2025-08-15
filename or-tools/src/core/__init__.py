"""
核心功能模块 (Core Module)

包含系统的核心功能组件：
- 异常定义：自定义异常类层次结构
- 常量定义：系统级常量和枚举
- 基础工具：核心工具函数和基类

这个模块为整个系统提供基础设施支持。
"""

from .exceptions import (
    SchedulingError,
    SolverError,
    ValidationError,
    ResourceConflictError,
    ConstraintViolationError,
)

from .constants import (
    ResourceType,
    TaskStatus,
    GateType,
    EventType,
    PriorityTemplate,
    SolverStatus,
    ConstraintType,
)

__all__ = [
    # 异常类
    "SchedulingError",
    "SolverError",
    "ValidationError", 
    "ResourceConflictError",
    "ConstraintViolationError",
    # 常量枚举
    "ResourceType",
    "TaskStatus",
    "GateType",
    "EventType", 
    "PriorityTemplate",
    "SolverStatus",
    "ConstraintType",
]
