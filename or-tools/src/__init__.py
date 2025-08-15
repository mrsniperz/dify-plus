"""
智能排程系统 (Intelligent Scheduling System)

基于Google OR-Tools CP-SAT求解器的发动机QEC维修计划智能调度引擎。

主要功能：
- 维修计划智能化生成
- 维修计划智能化调整
- 资源规划智能化
- 准备阶段智能排程
- 多项目并行最优排程

技术架构：
- 数据模型层：定义核心业务实体和数据结构
- 求解器层：基于OR-Tools的约束求解引擎
- 业务逻辑层：排程服务、资源管理、事件处理
- API接口层：RESTful API和中间件
- 配置管理层：策略模板和参数配置

版本: 0.1.0
作者: Development Team
"""

__version__ = "0.1.0"
__author__ = "Development Team"
__email__ = "dev@company.com"
__description__ = "智能排程系统 - 基于OR-Tools的发动机QEC维修计划智能调度引擎"

# 导出主要组件
from .core.exceptions import (
    SchedulingError,
    SolverError,
    ValidationError,
    ResourceConflictError,
    ConstraintViolationError,
)

from .core.constants import (
    ResourceType,
    TaskStatus,
    GateType,
    EventType,
    PriorityTemplate,
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
]
