"""
事件模型 (Event Models)

定义系统中各种事件的数据模型，用于处理外部变化和触发重排。
事件是动态调度的核心机制，需要精确建模以支持实时响应和状态同步。

模型层次：
- Event: 基础事件模型
- EventCreate: 创建事件的请求模型
- EventProcessor: 事件处理器接口
- EventLog: 事件日志模型
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

from ..core.constants import EventType


class EventPriority(str, Enum):
    """事件优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventStatus(str, Enum):
    """事件状态枚举"""
    PENDING = "pending"         # 待处理
    PROCESSING = "processing"   # 处理中
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"          # 处理失败
    CANCELLED = "cancelled"     # 已取消


class ProcessingPolicy(str, Enum):
    """处理策略枚举"""
    REPLAN_UNSTARTED = "replan_unstarted"     # 仅重排未开始的任务
    ROLLING_WINDOW = "rolling_window"         # 滚动时间窗
    FULL_REPLAN = "full_replan"              # 全面重排
    MANUAL_REVIEW = "manual_review"           # 人工审核


class EventScope(BaseModel):
    """事件影响范围模型"""
    engines: List[str] = Field(default_factory=list, description="影响的发动机ID列表")
    work_packages: List[str] = Field(default_factory=list, description="影响的工包ID列表")
    prep_ids: List[str] = Field(default_factory=list, description="影响的准备任务ID列表")
    job_ids: List[str] = Field(default_factory=list, description="影响的工卡子项目ID列表")
    resource_ids: List[str] = Field(default_factory=list, description="影响的资源ID列表")
    
    def is_empty(self) -> bool:
        """检查影响范围是否为空"""
        return not any([
            self.engines, self.work_packages, self.prep_ids, 
            self.job_ids, self.resource_ids
        ])
    
    def merge(self, other: 'EventScope') -> 'EventScope':
        """
        合并影响范围
        
        Args:
            other: 另一个影响范围
            
        Returns:
            合并后的影响范围
        """
        return EventScope(
            engines=list(set(self.engines + other.engines)),
            work_packages=list(set(self.work_packages + other.work_packages)),
            prep_ids=list(set(self.prep_ids + other.prep_ids)),
            job_ids=list(set(self.job_ids + other.job_ids)),
            resource_ids=list(set(self.resource_ids + other.resource_ids))
        )
    
    class Config:
        schema_extra = {
            "example": {
                "engines": ["ENG-001"],
                "work_packages": ["WP-001"],
                "prep_ids": ["P-001", "P-002"],
                "job_ids": [],
                "resource_ids": ["CRANE-1"]
            }
        }


class EventPayload(BaseModel):
    """事件载荷基类"""
    pass


class ETAChangePayload(EventPayload):
    """ETA变更事件载荷"""
    material_id: Optional[str] = Field(None, description="物料ID")
    resource_id: Optional[str] = Field(None, description="资源ID")
    old_eta: Optional[datetime] = Field(None, description="原ETA时间")
    new_eta: datetime = Field(..., description="新ETA时间")
    reason: Optional[str] = Field(None, description="变更原因")
    
    class Config:
        schema_extra = {
            "example": {
                "material_id": "M-001",
                "old_eta": "2025-08-15T12:00:00Z",
                "new_eta": "2025-08-15T16:00:00Z",
                "reason": "供应商延迟"
            }
        }


class SAPUpdatePayload(EventPayload):
    """SAP状态更新事件载荷"""
    instruction_id: str = Field(..., description="SAP指令ID")
    old_status: Optional[str] = Field(None, description="原状态")
    new_status: str = Field(..., description="新状态")
    update_time: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    class Config:
        schema_extra = {
            "example": {
                "instruction_id": "SAP-001",
                "old_status": "pending",
                "new_status": "approved",
                "update_time": "2025-08-15T10:00:00Z"
            }
        }


class WeatherEventPayload(EventPayload):
    """天气事件载荷"""
    weather_type: str = Field(..., description="天气类型")
    severity: str = Field(..., description="严重程度")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    affected_areas: List[str] = Field(default_factory=list, description="影响区域")
    
    class Config:
        schema_extra = {
            "example": {
                "weather_type": "typhoon",
                "severity": "high",
                "start_time": "2025-08-15T14:00:00Z",
                "end_time": "2025-08-16T02:00:00Z",
                "affected_areas": ["outdoor_area", "crane_zone"]
            }
        }


class ThirdPartyAckPayload(EventPayload):
    """第三方确认事件载荷"""
    party_name: str = Field(..., description="第三方名称")
    confirmation_type: str = Field(..., description="确认类型")
    confirmed: bool = Field(..., description="是否确认")
    confirmation_time: datetime = Field(default_factory=datetime.now, description="确认时间")
    notes: Optional[str] = Field(None, description="备注")
    
    class Config:
        schema_extra = {
            "example": {
                "party_name": "客户代表",
                "confirmation_type": "inspection_approval",
                "confirmed": True,
                "confirmation_time": "2025-08-15T11:00:00Z",
                "notes": "检查通过，可以继续"
            }
        }


class ResourceStatusPayload(EventPayload):
    """资源状态变更事件载荷"""
    resource_id: str = Field(..., description="资源ID")
    old_status: Optional[str] = Field(None, description="原状态")
    new_status: str = Field(..., description="新状态")
    available_from: Optional[datetime] = Field(None, description="可用开始时间")
    available_until: Optional[datetime] = Field(None, description="可用结束时间")
    reason: Optional[str] = Field(None, description="状态变更原因")
    
    class Config:
        schema_extra = {
            "example": {
                "resource_id": "CRANE-1",
                "old_status": "available",
                "new_status": "maintenance",
                "available_from": "2025-08-16T08:00:00Z",
                "reason": "定期维护"
            }
        }


class Event(BaseModel):
    """
    基础事件模型
    
    定义系统中所有事件的通用属性和行为。
    """
    event_id: str = Field(..., description="事件唯一标识")
    event_type: EventType = Field(..., description="事件类型")
    
    # 基本信息
    title: str = Field(..., description="事件标题")
    description: Optional[str] = Field(None, description="事件描述")
    
    # 时间信息
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    effective_time: datetime = Field(..., description="生效时间")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    
    # 优先级和状态
    priority: EventPriority = Field(EventPriority.MEDIUM, description="事件优先级")
    status: EventStatus = Field(EventStatus.PENDING, description="事件状态")
    
    # 影响范围
    scope: EventScope = Field(default_factory=EventScope, description="影响范围")
    
    # 处理策略
    policy: ProcessingPolicy = Field(ProcessingPolicy.REPLAN_UNSTARTED, description="处理策略")
    
    # 事件载荷
    payload: Dict[str, Any] = Field(default_factory=dict, description="事件载荷数据")
    
    # 处理信息
    processed_at: Optional[datetime] = Field(None, description="处理时间")
    processed_by: Optional[str] = Field(None, description="处理者")
    processing_result: Optional[Dict[str, Any]] = Field(None, description="处理结果")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    # 元数据
    source: Optional[str] = Field(None, description="事件来源")
    correlation_id: Optional[str] = Field(None, description="关联ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")
    
    @validator('effective_time')
    def validate_effective_time_not_past(cls, v):
        """验证生效时间不能是过去时间（允许一定容差）"""
        now = datetime.now()
        if v < now.replace(second=0, microsecond=0):  # 允许分钟级容差
            # 对于历史事件，这可能是正常的，所以只是警告而不是错误
            pass
        return v
    
    def is_expired(self) -> bool:
        """
        检查事件是否已过期
        
        Returns:
            是否已过期
        """
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False
    
    def is_effective(self) -> bool:
        """
        检查事件是否已生效
        
        Returns:
            是否已生效
        """
        return datetime.now() >= self.effective_time
    
    def mark_processing(self, processed_by: Optional[str] = None):
        """
        标记为处理中
        
        Args:
            processed_by: 处理者
        """
        self.status = EventStatus.PROCESSING
        self.processed_at = datetime.now()
        if processed_by:
            self.processed_by = processed_by
    
    def mark_completed(self, result: Optional[Dict[str, Any]] = None):
        """
        标记为已完成
        
        Args:
            result: 处理结果
        """
        self.status = EventStatus.COMPLETED
        if result:
            self.processing_result = result
    
    def mark_failed(self, error_message: str):
        """
        标记为处理失败
        
        Args:
            error_message: 错误信息
        """
        self.status = EventStatus.FAILED
        self.error_message = error_message
    
    def get_typed_payload(self, payload_class):
        """
        获取类型化的载荷对象
        
        Args:
            payload_class: 载荷类型
            
        Returns:
            类型化的载荷对象
        """
        try:
            return payload_class(**self.payload)
        except Exception as e:
            raise ValueError(f"Invalid payload for {payload_class.__name__}: {e}")
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "event_id": "EV-001",
                "event_type": "eta_change",
                "title": "物料M-001 ETA变更",
                "description": "由于供应商延迟，物料M-001的ETA推迟4小时",
                "created_at": "2025-08-15T08:00:00Z",
                "effective_time": "2025-08-15T08:00:00Z",
                "priority": "medium",
                "status": "pending",
                "scope": {
                    "engines": ["ENG-001"],
                    "prep_ids": ["P-001"]
                },
                "policy": "replan_unstarted",
                "payload": {
                    "material_id": "M-001",
                    "old_eta": "2025-08-15T12:00:00Z",
                    "new_eta": "2025-08-15T16:00:00Z",
                    "reason": "供应商延迟"
                },
                "source": "material_system"
            }
        }


class EventCreate(BaseModel):
    """创建事件的请求模型"""
    event_type: EventType = Field(..., description="事件类型")
    title: str = Field(..., description="事件标题")
    description: Optional[str] = Field(None, description="事件描述")
    effective_time: datetime = Field(..., description="生效时间")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    priority: EventPriority = Field(EventPriority.MEDIUM, description="事件优先级")
    scope: EventScope = Field(default_factory=EventScope, description="影响范围")
    policy: ProcessingPolicy = Field(ProcessingPolicy.REPLAN_UNSTARTED, description="处理策略")
    payload: Dict[str, Any] = Field(default_factory=dict, description="事件载荷数据")
    source: Optional[str] = Field(None, description="事件来源")
    correlation_id: Optional[str] = Field(None, description="关联ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")


class EventLog(BaseModel):
    """事件日志模型"""
    log_id: str = Field(..., description="日志ID")
    event_id: str = Field(..., description="关联的事件ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="日志时间")
    level: str = Field(..., description="日志级别")
    message: str = Field(..., description="日志消息")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细信息")
    
    class Config:
        schema_extra = {
            "example": {
                "log_id": "LOG-001",
                "event_id": "EV-001",
                "timestamp": "2025-08-15T08:05:00Z",
                "level": "INFO",
                "message": "Event processing started",
                "details": {"processor": "scheduling_service"}
            }
        }
