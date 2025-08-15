"""
数据模型层 (Models Module)

定义智能排程系统的核心数据模型和业务实体。
使用Pydantic进行数据验证和序列化，确保数据的类型安全和一致性。

主要模型：
- Job: 工卡子项目模型
- Resource: 资源模型（人力、工具、设备等）
- PreparationTask: 准备任务模型
- MaterialItem: 物料项模型
- ToolAsset: 工装设备模型
- Event: 事件模型
- Schedule: 排程结果模型
"""

# Job模型
from .job import (
    Job,
    JobCreate,
    JobUpdate,
    JobInDB,
    JobPriority,
    ResourceRequirement,
    PerformanceFactor,
)

# Resource模型
from .resource import (
    Resource,
    HumanResource,
    PhysicalResource,
    ResourceCalendar,
    ResourceAvailability,
    AvailabilityStatus,
    ShiftType,
    TimeSlot,
    WorkingDay,
)

# Preparation模型
from .preparation import (
    PreparationTask,
    MaterialItem,
    ToolAsset,
    Gate,
    Evidence,
    EvidenceType,
)

# Event模型
from .event import (
    Event,
    EventCreate,
    EventLog,
    EventScope,
    EventPriority,
    EventStatus,
    ProcessingPolicy,
    ETAChangePayload,
    SAPUpdatePayload,
    WeatherEventPayload,
    ThirdPartyAckPayload,
    ResourceStatusPayload,
)

# Schedule模型
from .schedule import (
    Schedule,
    TaskInterval,
    ResourceAllocation,
    ScheduleMetrics,
    ScheduleDiff,
    IntervalType,
    AllocationStatus,
)

__all__ = [
    # Job模型
    "Job",
    "JobCreate",
    "JobUpdate",
    "JobInDB",
    "JobPriority",
    "ResourceRequirement",
    "PerformanceFactor",
    # Resource模型
    "Resource",
    "HumanResource",
    "PhysicalResource",
    "ResourceCalendar",
    "ResourceAvailability",
    "AvailabilityStatus",
    "ShiftType",
    "TimeSlot",
    "WorkingDay",
    # Preparation模型
    "PreparationTask",
    "MaterialItem",
    "ToolAsset",
    "Gate",
    "Evidence",
    "EvidenceType",
    # Event模型
    "Event",
    "EventCreate",
    "EventLog",
    "EventScope",
    "EventPriority",
    "EventStatus",
    "ProcessingPolicy",
    "ETAChangePayload",
    "SAPUpdatePayload",
    "WeatherEventPayload",
    "ThirdPartyAckPayload",
    "ResourceStatusPayload",
    # Schedule模型
    "Schedule",
    "TaskInterval",
    "ResourceAllocation",
    "ScheduleMetrics",
    "ScheduleDiff",
    "IntervalType",
    "AllocationStatus",
]
