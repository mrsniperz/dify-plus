"""
常量定义模块 (Constants Module)

定义智能排程系统的系统级常量和枚举类型。
包括资源类型、任务状态、门禁类型、事件类型等核心枚举。

这些常量确保了系统中数据类型的一致性和可维护性。
"""

from enum import Enum, IntEnum
from typing import Final


class ResourceType(str, Enum):
    """
    资源类型枚举
    
    定义系统中所有资源的类型分类。
    """
    HUMAN = "human"              # 人力资源
    TOOL = "tool"                # 工具
    EQUIPMENT = "equipment"      # 设备
    BAY = "bay"                  # 工位
    CRANE = "crane"              # 行车
    MATERIAL = "material"        # 航材
    WORKSPACE = "workspace"      # 工作区域


class TaskStatus(str, Enum):
    """
    任务状态枚举
    
    定义任务在生命周期中的各种状态。
    """
    NOT_STARTED = "not_started"  # 未开始
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"      # 已完成
    CANCELLED = "cancelled"      # 已取消
    BLOCKED = "blocked"          # 被阻塞
    PAUSED = "paused"           # 已暂停


class GateType(str, Enum):
    """
    门禁类型枚举
    
    定义准备阶段的各种门禁检查类型。
    """
    CRITICAL_TOOLS_READY = "critical_tools_ready"        # 关键工装齐套
    MATERIALS_READY = "materials_ready"                  # 航材齐套
    DOC_READY = "doc_ready"                             # 技术资料就绪
    ASSESSMENT_COMPLETE = "assessment_complete"          # 评估完成
    QEC_SHELF_HANDOVER = "qec_shelf_handover"           # QEC货架交接
    INVENTORY_CHECK = "inventory_check"                  # 库存确认
    SAP_INSTRUCTION = "sap_instruction"                  # SAP指令接收


class EventType(str, Enum):
    """
    事件类型枚举
    
    定义系统处理的各种外部事件类型。
    """
    ETA_CHANGE = "eta_change"                    # ETA变更
    SAP_UPDATE = "sap_update"                    # SAP状态更新
    WEATHER = "weather"                          # 天气事件
    THIRD_PARTY_ACK = "third_party_ack"         # 第三方确认
    RESOURCE_AVAILABLE = "resource_available"    # 资源可用
    RESOURCE_UNAVAILABLE = "resource_unavailable" # 资源不可用
    TASK_COMPLETE = "task_complete"              # 任务完成
    EMERGENCY = "emergency"                      # 紧急事件


class PriorityTemplate(str, Enum):
    """
    优先级策略模板枚举
    
    定义预设的优先级策略模板。
    """
    BALANCED = "balanced"           # 均衡公平型
    PROTECT_SLA = "protect_sla"     # 保护SLA型
    COST_MIN = "cost_min"           # 成本最小型


class SolverStatus(str, Enum):
    """
    求解器状态枚举
    
    定义OR-Tools求解器的各种状态。
    """
    OPTIMAL = "optimal"             # 最优解
    FEASIBLE = "feasible"           # 可行解
    INFEASIBLE = "infeasible"       # 无可行解
    UNBOUNDED = "unbounded"         # 无界
    ABNORMAL = "abnormal"           # 异常
    MODEL_INVALID = "model_invalid" # 模型无效
    UNKNOWN = "unknown"             # 未知状态


class ConstraintType(str, Enum):
    """
    约束类型枚举
    
    定义系统中的各种约束类型。
    """
    PRECEDENCE = "precedence"           # 前置约束
    RESOURCE_CAPACITY = "resource_capacity"  # 资源容量约束
    TIME_WINDOW = "time_window"         # 时间窗约束
    QUALIFICATION = "qualification"      # 资质约束
    MATERIAL_READY = "material_ready"   # 物料就绪约束
    GATE_DEPENDENCY = "gate_dependency" # 门禁依赖约束
    EXCLUSIVE_RESOURCE = "exclusive_resource" # 资源独占约束


class PreparationTaskType(str, Enum):
    """
    准备任务类型枚举
    
    定义准备阶段的各种任务类型。
    """
    TOOL_ALLOCATION = "tool_allocation"     # 工装调配
    MATERIAL_KITTING = "material_kitting"  # 航材配套
    DOC_READY = "doc_ready"                # 技术资料准备
    ASSESSMENT = "assessment"               # 评估
    SHELF_HANDOVER = "shelf_handover"      # 货架交接
    INVENTORY_CHECK = "inventory_check"     # 库存检查
    HOIST_PREP = "hoist_prep"              # 吊装准备


class MaterialCriticality(str, Enum):
    """
    物料关键性枚举
    
    定义物料的关键性等级。
    """
    HIGH = "high"       # 高关键性
    MEDIUM = "medium"   # 中等关键性
    LOW = "low"         # 低关键性


class AssetCategory(str, Enum):
    """
    资产类别枚举
    
    定义工装设备的类别。
    """
    HOIST = "hoist"     # 行车
    SLING = "sling"     # 吊具
    STAND = "stand"     # 支撑架
    OTHER = "other"     # 其他


# 系统级常量
class SystemConstants:
    """系统级常量定义"""
    
    # 默认求解时间限制（秒）
    DEFAULT_SOLVE_TIME_LIMIT: Final[int] = 300
    
    # 单工包求解时间限制（秒）
    SINGLE_PACKAGE_SOLVE_LIMIT: Final[int] = 5
    
    # 多工包求解时间限制（秒）
    MULTI_PACKAGE_SOLVE_LIMIT: Final[int] = 20
    
    # 重排求解时间限制比例
    RESCHEDULE_TIME_RATIO: Final[float] = 0.4
    
    # 默认准备窗口天数
    DEFAULT_PREP_WINDOW_DAYS: Final[int] = 2
    
    # 插单护栏默认值
    DEFAULT_MAX_PREEMPTIONS_PER_DAY: Final[int] = 2
    DEFAULT_MAX_PREEMPTION_HOURS: Final[int] = 4
    
    # SLA风险阈值（小时）
    SLA_RISK_THRESHOLD_HOURS: Final[int] = 12
    
    # 关键路径延误阈值（小时）
    CRITICAL_PATH_DELAY_THRESHOLD_HOURS: Final[int] = 2


# API相关常量
class APIConstants:
    """API相关常量定义"""
    
    # API版本
    API_VERSION: Final[str] = "v1"
    
    # 默认分页大小
    DEFAULT_PAGE_SIZE: Final[int] = 20
    
    # 最大分页大小
    MAX_PAGE_SIZE: Final[int] = 100
    
    # 请求超时时间（秒）
    REQUEST_TIMEOUT: Final[int] = 30
    
    # 幂等性键过期时间（秒）
    IDEMPOTENCY_KEY_TTL: Final[int] = 3600


# 错误代码常量
class ErrorCodes:
    """错误代码常量定义"""
    
    # 通用错误
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    
    # 业务错误
    SOLVER_ERROR = "SOLVER_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"
    GATE_ERROR = "GATE_ERROR"
    EVENT_PROCESSING_ERROR = "EVENT_PROCESSING_ERROR"
