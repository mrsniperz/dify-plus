"""
事件处理服务 (Event Service)

负责处理外部事件和触发动态重排的业务逻辑。
支持各种类型的事件处理，包括ETA变更、SAP状态更新、天气事件等。

主要功能：
- 事件接收和验证
- 事件影响分析
- 重排触发和执行
- 事件日志记录
"""

import uuid
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import logging

from ..models import (
    Event, EventCreate, EventLog, EventScope, Schedule, ScheduleDiff,
    ETAChangePayload, SAPUpdatePayload, WeatherEventPayload,
    ThirdPartyAckPayload, ResourceStatusPayload
)
from ..core.exceptions import EventProcessingError, ValidationError
from ..core.constants import EventType
from ..models.event import EventStatus, ProcessingPolicy


logger = logging.getLogger(__name__)


class EventProcessor:
    """事件处理器基类"""
    
    def __init__(self, event_type: EventType):
        self.event_type = event_type
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def can_process(self, event: Event) -> bool:
        """检查是否可以处理此事件"""
        return event.event_type == self.event_type
    
    def process(self, event: Event, current_schedule: Optional[Schedule] = None) -> Dict[str, Any]:
        """
        处理事件
        
        Args:
            event: 事件对象
            current_schedule: 当前排程计划
            
        Returns:
            处理结果
        """
        raise NotImplementedError


class ETAChangeProcessor(EventProcessor):
    """ETA变更事件处理器"""
    
    def __init__(self):
        super().__init__(EventType.ETA_CHANGE)
    
    def process(self, event: Event, current_schedule: Optional[Schedule] = None) -> Dict[str, Any]:
        """处理ETA变更事件"""
        try:
            # 解析事件载荷
            payload = event.get_typed_payload(ETAChangePayload)
            
            self.logger.info(f"Processing ETA change for {payload.material_id or payload.resource_id}")
            
            # 分析影响范围
            affected_tasks = self._analyze_eta_impact(payload, current_schedule)
            
            # 计算延误时间
            delay_hours = 0.0
            if payload.old_eta and payload.new_eta:
                delay_hours = (payload.new_eta - payload.old_eta).total_seconds() / 3600
            
            return {
                "affected_tasks": affected_tasks,
                "delay_hours": delay_hours,
                "requires_replan": delay_hours > 0.5,  # 超过30分钟需要重排
                "impact_level": "high" if delay_hours > 4 else "medium" if delay_hours > 1 else "low"
            }
            
        except Exception as e:
            raise EventProcessingError(
                f"Failed to process ETA change event: {e}",
                event_type=event.event_type.value,
                event_id=event.event_id
            )
    
    def _analyze_eta_impact(
        self, 
        payload: ETAChangePayload, 
        schedule: Optional[Schedule]
    ) -> List[str]:
        """分析ETA变更的影响范围"""
        affected_tasks = []
        
        if not schedule:
            return affected_tasks
        
        # 查找使用该物料或资源的任务
        for interval in schedule.task_intervals:
            # 检查是否使用了相关资源
            if payload.resource_id and payload.resource_id in interval.assigned_resources:
                affected_tasks.append(interval.task_id)
            
            # 检查是否依赖相关物料（需要从任务元数据中获取）
            if payload.material_id:
                task_materials = interval.metadata.get("required_materials", [])
                if payload.material_id in task_materials:
                    affected_tasks.append(interval.task_id)
        
        return affected_tasks


class SAPUpdateProcessor(EventProcessor):
    """SAP状态更新事件处理器"""
    
    def __init__(self):
        super().__init__(EventType.SAP_UPDATE)
    
    def process(self, event: Event, current_schedule: Optional[Schedule] = None) -> Dict[str, Any]:
        """处理SAP状态更新事件"""
        try:
            payload = event.get_typed_payload(SAPUpdatePayload)
            
            self.logger.info(f"Processing SAP update for instruction {payload.instruction_id}")
            
            # 根据SAP状态变化确定影响
            impact_level = "low"
            requires_replan = False
            
            if payload.new_status in ["approved", "released"]:
                impact_level = "medium"
                requires_replan = True
            elif payload.new_status in ["rejected", "cancelled"]:
                impact_level = "high"
                requires_replan = True
            
            return {
                "instruction_id": payload.instruction_id,
                "status_change": f"{payload.old_status} -> {payload.new_status}",
                "requires_replan": requires_replan,
                "impact_level": impact_level
            }
            
        except Exception as e:
            raise EventProcessingError(
                f"Failed to process SAP update event: {e}",
                event_type=event.event_type.value,
                event_id=event.event_id
            )


class WeatherEventProcessor(EventProcessor):
    """天气事件处理器"""
    
    def __init__(self):
        super().__init__(EventType.WEATHER)
    
    def process(self, event: Event, current_schedule: Optional[Schedule] = None) -> Dict[str, Any]:
        """处理天气事件"""
        try:
            payload = event.get_typed_payload(WeatherEventPayload)
            
            self.logger.info(f"Processing weather event: {payload.weather_type}")
            
            # 分析天气对资源的影响
            affected_resources = self._analyze_weather_impact(payload)
            
            # 确定影响级别
            impact_level = payload.severity
            requires_replan = payload.severity in ["high", "critical"]
            
            return {
                "weather_type": payload.weather_type,
                "severity": payload.severity,
                "affected_areas": payload.affected_areas,
                "affected_resources": affected_resources,
                "requires_replan": requires_replan,
                "impact_level": impact_level,
                "duration_hours": (
                    (payload.end_time - payload.start_time).total_seconds() / 3600
                    if payload.end_time else None
                )
            }
            
        except Exception as e:
            raise EventProcessingError(
                f"Failed to process weather event: {e}",
                event_type=event.event_type.value,
                event_id=event.event_id
            )
    
    def _analyze_weather_impact(self, payload: WeatherEventPayload) -> List[str]:
        """分析天气对资源的影响"""
        affected_resources = []
        
        # 根据天气类型和影响区域确定受影响的资源
        if payload.weather_type in ["typhoon", "storm", "heavy_rain"]:
            if "outdoor_area" in payload.affected_areas:
                affected_resources.extend(["CRANE-1", "CRANE-2"])  # 室外行车
            if "crane_zone" in payload.affected_areas:
                affected_resources.extend(["CRANE-3", "CRANE-4"])  # 行车区域
        
        return affected_resources


class EventService:
    """
    事件处理服务
    
    负责事件的接收、处理和重排触发。
    """
    
    def __init__(self):
        self.processors: Dict[EventType, EventProcessor] = {}
        self.event_logs: List[EventLog] = []
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # 注册事件处理器
        self._register_processors()
    
    def _register_processors(self) -> None:
        """注册事件处理器"""
        processors = [
            ETAChangeProcessor(),
            SAPUpdateProcessor(),
            WeatherEventProcessor(),
        ]
        
        for processor in processors:
            self.processors[processor.event_type] = processor
    
    def create_event(self, event_data: EventCreate) -> Event:
        """
        创建事件
        
        Args:
            event_data: 事件创建数据
            
        Returns:
            创建的事件对象
        """
        # 生成事件ID
        event_id = f"EV-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"
        
        # 创建事件对象
        event = Event(
            event_id=event_id,
            event_type=event_data.event_type,
            title=event_data.title,
            description=event_data.description,
            effective_time=event_data.effective_time,
            expires_at=event_data.expires_at,
            priority=event_data.priority,
            scope=event_data.scope,
            policy=event_data.policy,
            payload=event_data.payload,
            source=event_data.source,
            correlation_id=event_data.correlation_id,
            metadata=event_data.metadata
        )
        
        self.logger.info(f"Created event {event_id} of type {event_data.event_type}")
        
        return event
    
    def process_event(
        self, 
        event: Event, 
        current_schedule: Optional[Schedule] = None
    ) -> Dict[str, Any]:
        """
        处理事件
        
        Args:
            event: 事件对象
            current_schedule: 当前排程计划
            
        Returns:
            处理结果
        """
        try:
            # 验证事件
            self._validate_event(event)
            
            # 标记为处理中
            event.mark_processing()
            
            # 记录开始处理日志
            self._log_event(event, "INFO", "Event processing started")
            
            # 查找处理器
            processor = self.processors.get(event.event_type)
            if not processor:
                raise EventProcessingError(
                    f"No processor found for event type {event.event_type}",
                    event_type=event.event_type.value,
                    event_id=event.event_id
                )
            
            # 处理事件
            result = processor.process(event, current_schedule)
            
            # 标记为完成
            event.mark_completed(result)
            
            # 记录完成日志
            self._log_event(event, "INFO", "Event processing completed", result)
            
            self.logger.info(f"Successfully processed event {event.event_id}")
            
            return {
                "event_id": event.event_id,
                "status": "completed",
                "result": result,
                "processed_at": event.processed_at.isoformat() if event.processed_at else None
            }
            
        except Exception as e:
            # 标记为失败
            event.mark_failed(str(e))
            
            # 记录错误日志
            self._log_event(event, "ERROR", f"Event processing failed: {e}")
            
            self.logger.error(f"Failed to process event {event.event_id}: {e}")
            
            raise
    
    def apply_events(
        self, 
        plan_id: str, 
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        应用多个事件
        
        Args:
            plan_id: 计划ID
            events: 事件列表
            
        Returns:
            应用结果
        """
        try:
            self.logger.info(f"Applying {len(events)} events to plan {plan_id}")
            
            affected_tasks = set()
            delays = []
            resource_reallocation = []
            total_delay_hours = 0.0
            
            # 处理每个事件
            for event_data in events:
                # 创建事件对象
                event_create = EventCreate(**event_data)
                event = self.create_event(event_create)
                
                # 处理事件
                result = self.process_event(event)
                
                # 合并结果
                if "result" in result:
                    event_result = result["result"]
                    
                    if "affected_tasks" in event_result:
                        affected_tasks.update(event_result["affected_tasks"])
                    
                    if "delay_hours" in event_result:
                        delay_hours = event_result["delay_hours"]
                        total_delay_hours += delay_hours
                        
                        if delay_hours > 0:
                            delays.append({
                                "event_id": event.event_id,
                                "delay_hours": delay_hours,
                                "reason": event.event_type.value
                            })
            
            # 计算新的makespan
            new_makespan_hours = 24.0 + total_delay_hours  # 简化计算
            
            return {
                "plan_id": plan_id,
                "diff": {
                    "affected_tasks": list(affected_tasks),
                    "delays": delays,
                    "resource_reallocation": resource_reallocation
                },
                "new_makespan": f"PT{int(new_makespan_hours)}H",
                "request_id": f"req-{uuid.uuid4().hex[:8]}"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to apply events to plan {plan_id}: {e}")
            raise EventProcessingError(
                f"Failed to apply events: {e}",
                event_type="batch_processing"
            )
    
    def _validate_event(self, event: Event) -> None:
        """验证事件"""
        if event.is_expired():
            raise ValidationError(f"Event {event.event_id} has expired")
        
        if not event.is_effective():
            raise ValidationError(f"Event {event.event_id} is not yet effective")
        
        if event.scope.is_empty():
            raise ValidationError(f"Event {event.event_id} has empty scope")
    
    def _log_event(
        self, 
        event: Event, 
        level: str, 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录事件日志"""
        log_id = f"LOG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"
        
        event_log = EventLog(
            log_id=log_id,
            event_id=event.event_id,
            level=level,
            message=message,
            details=details or {}
        )
        
        self.event_logs.append(event_log)
    
    def get_event_logs(self, event_id: Optional[str] = None) -> List[EventLog]:
        """
        获取事件日志
        
        Args:
            event_id: 事件ID，如果为None则返回所有日志
            
        Returns:
            事件日志列表
        """
        if event_id:
            return [log for log in self.event_logs if log.event_id == event_id]
        return self.event_logs.copy()
