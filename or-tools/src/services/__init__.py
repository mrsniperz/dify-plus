"""
业务逻辑层 (Services Module)

实现智能排程系统的核心业务逻辑和服务。
提供高层次的业务接口，协调各个组件完成复杂的业务流程。

主要服务：
- SchedulingService: 排程服务，负责生成初始排程计划
- EventService: 事件处理服务，处理外部事件和状态变更
- ResourceService: 资源管理服务，管理资源分配和冲突检测
- GateService: 门禁检查服务，验证准备阶段的门禁条件
"""

# 排程服务
from .scheduling_service import (
    SchedulingService,
    SchedulingRequest,
    SchedulingResponse,
)

# 事件处理服务
from .event_service import (
    EventService,
    EventProcessor,
    ETAChangeProcessor,
    SAPUpdateProcessor,
    WeatherEventProcessor,
)

# 资源管理服务
from .resource_service import (
    ResourceService,
    ResourceConflict,
    ResourceUtilization,
)

# 门禁检查服务
from .gate_service import (
    GateService,
    GateCheckResult,
    GateStatus,
)

__all__ = [
    # 排程服务
    "SchedulingService",
    "SchedulingRequest",
    "SchedulingResponse",
    # 事件处理服务
    "EventService",
    "EventProcessor",
    "ETAChangeProcessor",
    "SAPUpdateProcessor",
    "WeatherEventProcessor",
    # 资源管理服务
    "ResourceService",
    "ResourceConflict",
    "ResourceUtilization",
    # 门禁检查服务
    "GateService",
    "GateCheckResult",
    "GateStatus",
]
