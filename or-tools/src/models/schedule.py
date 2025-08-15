"""
排程结果模型 (Schedule Models)

定义排程系统的输出结果模型，包括任务时间间隔、资源分配、排程计划等。
这些模型用于表示求解器的输出结果和系统的排程状态。

模型层次：
- TaskInterval: 任务时间间隔模型
- ResourceAllocation: 资源分配模型
- Schedule: 排程计划模型
- ScheduleDiff: 排程差异模型
- ScheduleMetrics: 排程指标模型
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

from ..core.constants import SolverStatus, TaskStatus


class IntervalType(str, Enum):
    """时间间隔类型枚举"""
    JOB = "job"                    # 工卡子项目
    PREPARATION = "preparation"    # 准备任务
    MAINTENANCE = "maintenance"    # 维护任务
    BUFFER = "buffer"             # 缓冲时间


class AllocationStatus(str, Enum):
    """分配状态枚举"""
    ALLOCATED = "allocated"        # 已分配
    TENTATIVE = "tentative"       # 暂定
    RELEASED = "released"         # 已释放
    CONFLICT = "conflict"         # 冲突


class TaskInterval(BaseModel):
    """
    任务时间间隔模型
    
    表示一个任务在时间轴上的执行区间。
    """
    task_id: str = Field(..., description="任务ID")
    task_type: IntervalType = Field(..., description="任务类型")
    
    # 时间信息
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    duration_hours: float = Field(..., gt=0, description="持续时间（小时）")
    
    # 任务信息
    task_name: Optional[str] = Field(None, description="任务名称")
    work_package_id: Optional[str] = Field(None, description="所属工包ID")
    engine_id: Optional[str] = Field(None, description="所属发动机ID")
    
    # 分配信息
    assigned_resources: List[str] = Field(default_factory=list, description="分配的资源ID列表")
    assigned_personnel: List[str] = Field(default_factory=list, description="分配的人员ID列表")
    
    # 状态信息
    status: TaskStatus = Field(TaskStatus.NOT_STARTED, description="任务状态")
    is_critical_path: bool = Field(False, description="是否在关键路径上")
    
    # 约束信息
    is_fixed: bool = Field(False, description="是否为固定时间间隔")
    buffer_before: float = Field(0.0, ge=0, description="前置缓冲时间（小时）")
    buffer_after: float = Field(0.0, ge=0, description="后置缓冲时间（小时）")
    
    @validator('end_time')
    def validate_end_after_start(cls, v, values):
        """验证结束时间在开始时间之后"""
        start_time = values.get('start_time')
        if start_time and v <= start_time:
            raise ValueError("End time must be after start time")
        return v
    
    @validator('duration_hours')
    def validate_duration_matches_interval(cls, v, values):
        """验证持续时间与时间间隔匹配"""
        start_time = values.get('start_time')
        end_time = values.get('end_time')
        if start_time and end_time:
            calculated_hours = (end_time - start_time).total_seconds() / 3600
            if abs(calculated_hours - v) > 0.01:  # 允许1分钟的误差
                raise ValueError(f"Duration {v} hours does not match interval {calculated_hours} hours")
        return v
    
    def overlaps_with(self, other: 'TaskInterval') -> bool:
        """
        检查是否与另一个时间间隔重叠
        
        Args:
            other: 另一个时间间隔
            
        Returns:
            是否重叠
        """
        return not (self.end_time <= other.start_time or other.end_time <= self.start_time)
    
    def get_effective_start(self) -> datetime:
        """获取包含前置缓冲的有效开始时间"""
        return self.start_time - timedelta(hours=self.buffer_before)
    
    def get_effective_end(self) -> datetime:
        """获取包含后置缓冲的有效结束时间"""
        return self.end_time + timedelta(hours=self.buffer_after)
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "task_id": "J-001",
                "task_type": "job",
                "start_time": "2025-08-15T08:00:00Z",
                "end_time": "2025-08-15T12:00:00Z",
                "duration_hours": 4.0,
                "task_name": "发动机拆卸检查",
                "work_package_id": "WP-001",
                "engine_id": "ENG-001",
                "assigned_resources": ["CRANE-1"],
                "assigned_personnel": ["E-001"],
                "status": "not_started",
                "is_critical_path": True,
                "is_fixed": False
            }
        }


class ResourceAllocation(BaseModel):
    """
    资源分配模型
    
    表示资源在特定时间段的分配情况。
    """
    resource_id: str = Field(..., description="资源ID")
    resource_name: Optional[str] = Field(None, description="资源名称")
    
    # 分配信息
    allocated_to: str = Field(..., description="分配给的任务ID")
    quantity: int = Field(1, ge=1, description="分配数量")
    
    # 时间信息
    start_time: datetime = Field(..., description="分配开始时间")
    end_time: datetime = Field(..., description="分配结束时间")
    
    # 状态信息
    status: AllocationStatus = Field(AllocationStatus.ALLOCATED, description="分配状态")
    
    # 成本信息
    cost: Optional[float] = Field(None, ge=0, description="分配成本")
    
    @validator('end_time')
    def validate_end_after_start(cls, v, values):
        """验证结束时间在开始时间之后"""
        start_time = values.get('start_time')
        if start_time and v <= start_time:
            raise ValueError("End time must be after start time")
        return v
    
    def get_duration_hours(self) -> float:
        """获取分配持续时间（小时）"""
        return (self.end_time - self.start_time).total_seconds() / 3600
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "resource_id": "CRANE-1",
                "resource_name": "行车1号",
                "allocated_to": "J-001",
                "quantity": 1,
                "start_time": "2025-08-15T08:00:00Z",
                "end_time": "2025-08-15T12:00:00Z",
                "status": "allocated",
                "cost": 400.0
            }
        }


class ScheduleMetrics(BaseModel):
    """
    排程指标模型
    
    包含排程质量和性能的各种指标。
    """
    # 时间指标
    makespan_hours: float = Field(..., ge=0, description="总完工时间（小时）")
    total_duration_hours: float = Field(..., ge=0, description="总持续时间（小时）")
    critical_path_length_hours: float = Field(..., ge=0, description="关键路径长度（小时）")
    
    # 资源利用率
    resource_utilization: Dict[str, float] = Field(
        default_factory=dict,
        description="资源利用率（资源ID -> 利用率）"
    )
    average_utilization: float = Field(0.0, ge=0, le=1, description="平均资源利用率")
    
    # 等待时间
    total_waiting_time_hours: float = Field(0.0, ge=0, description="总等待时间（小时）")
    average_waiting_time_hours: float = Field(0.0, ge=0, description="平均等待时间（小时）")
    
    # 成本指标
    total_cost: Optional[float] = Field(None, ge=0, description="总成本")
    resource_cost: Optional[float] = Field(None, ge=0, description="资源成本")
    delay_penalty: Optional[float] = Field(None, ge=0, description="延误惩罚")
    
    # 约束违反
    constraint_violations: int = Field(0, ge=0, description="约束违反数量")
    soft_constraint_violations: int = Field(0, ge=0, description="软约束违反数量")
    
    # 求解信息
    solve_time_seconds: float = Field(..., ge=0, description="求解时间（秒）")
    solver_status: SolverStatus = Field(..., description="求解器状态")
    objective_value: Optional[float] = Field(None, description="目标函数值")
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "makespan_hours": 24.0,
                "total_duration_hours": 48.0,
                "critical_path_length_hours": 20.0,
                "resource_utilization": {"CRANE-1": 0.75, "TECH-001": 0.85},
                "average_utilization": 0.80,
                "total_waiting_time_hours": 4.0,
                "average_waiting_time_hours": 1.0,
                "total_cost": 5000.0,
                "constraint_violations": 0,
                "solve_time_seconds": 2.5,
                "solver_status": "optimal",
                "objective_value": 100.0
            }
        }


class ScheduleDiff(BaseModel):
    """
    排程差异模型
    
    表示两个排程计划之间的差异。
    """
    # 受影响的任务
    affected_tasks: List[str] = Field(default_factory=list, description="受影响的任务ID列表")
    
    # 时间变化
    delays: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="延误信息列表"
    )
    advances: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="提前信息列表"
    )
    
    # 资源重新分配
    resource_reallocation: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="资源重新分配信息"
    )
    
    # 新增和取消的任务
    added_tasks: List[str] = Field(default_factory=list, description="新增任务ID列表")
    cancelled_tasks: List[str] = Field(default_factory=list, description="取消任务ID列表")
    
    # 指标变化
    makespan_change_hours: float = Field(0.0, description="总完工时间变化（小时）")
    cost_change: Optional[float] = Field(None, description="成本变化")
    utilization_change: float = Field(0.0, description="平均利用率变化")
    
    def has_significant_changes(self, threshold_hours: float = 1.0) -> bool:
        """
        检查是否有显著变化
        
        Args:
            threshold_hours: 时间变化阈值（小时）
            
        Returns:
            是否有显著变化
        """
        return (
            abs(self.makespan_change_hours) > threshold_hours or
            len(self.affected_tasks) > 0 or
            len(self.resource_reallocation) > 0 or
            len(self.added_tasks) > 0 or
            len(self.cancelled_tasks) > 0
        )
    
    class Config:
        schema_extra = {
            "example": {
                "affected_tasks": ["J-001", "J-002"],
                "delays": [
                    {"task_id": "J-001", "delay_hours": 2.0, "reason": "resource_conflict"}
                ],
                "resource_reallocation": [
                    {"resource_id": "CRANE-1", "from_task": "J-001", "to_task": "J-003"}
                ],
                "makespan_change_hours": 2.0,
                "cost_change": 200.0,
                "utilization_change": -0.05
            }
        }


class Schedule(BaseModel):
    """
    排程计划模型
    
    表示完整的排程计划结果。
    """
    plan_id: str = Field(..., description="排程计划ID")
    name: Optional[str] = Field(None, description="计划名称")
    description: Optional[str] = Field(None, description="计划描述")
    
    # 时间信息
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    plan_start_time: datetime = Field(..., description="计划开始时间")
    plan_end_time: datetime = Field(..., description="计划结束时间")
    
    # 任务间隔
    task_intervals: List[TaskInterval] = Field(
        default_factory=list,
        description="任务时间间隔列表"
    )
    
    # 资源分配
    resource_allocations: List[ResourceAllocation] = Field(
        default_factory=list,
        description="资源分配列表"
    )
    
    # 门禁状态
    gates: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="门禁状态列表"
    )
    
    # 排程指标
    metrics: ScheduleMetrics = Field(..., description="排程指标")
    
    # 关键路径
    critical_path: List[str] = Field(default_factory=list, description="关键路径任务ID列表")
    
    # 状态信息
    is_feasible: bool = Field(True, description="是否可行")
    is_optimal: bool = Field(False, description="是否最优")
    
    # 元数据
    solver_config: Dict[str, Any] = Field(default_factory=dict, description="求解器配置")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")
    
    @validator('plan_end_time')
    def validate_end_after_start(cls, v, values):
        """验证计划结束时间在开始时间之后"""
        start_time = values.get('plan_start_time')
        if start_time and v <= start_time:
            raise ValueError("Plan end time must be after start time")
        return v
    
    def get_task_interval(self, task_id: str) -> Optional[TaskInterval]:
        """
        获取指定任务的时间间隔
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务时间间隔，如果不存在则返回None
        """
        for interval in self.task_intervals:
            if interval.task_id == task_id:
                return interval
        return None
    
    def get_resource_allocations(self, resource_id: str) -> List[ResourceAllocation]:
        """
        获取指定资源的所有分配
        
        Args:
            resource_id: 资源ID
            
        Returns:
            资源分配列表
        """
        return [alloc for alloc in self.resource_allocations if alloc.resource_id == resource_id]
    
    def get_tasks_by_engine(self, engine_id: str) -> List[TaskInterval]:
        """
        获取指定发动机的所有任务
        
        Args:
            engine_id: 发动机ID
            
        Returns:
            任务时间间隔列表
        """
        return [interval for interval in self.task_intervals if interval.engine_id == engine_id]
    
    def calculate_diff(self, other: 'Schedule') -> ScheduleDiff:
        """
        计算与另一个排程计划的差异
        
        Args:
            other: 另一个排程计划
            
        Returns:
            排程差异
        """
        # 这里是一个简化的实现，实际应该更详细
        affected_tasks = []
        delays = []
        
        # 比较任务时间间隔
        for interval in self.task_intervals:
            other_interval = other.get_task_interval(interval.task_id)
            if other_interval:
                if interval.start_time != other_interval.start_time:
                    affected_tasks.append(interval.task_id)
                    if interval.start_time > other_interval.start_time:
                        delay_hours = (interval.start_time - other_interval.start_time).total_seconds() / 3600
                        delays.append({
                            "task_id": interval.task_id,
                            "delay_hours": delay_hours,
                            "reason": "schedule_change"
                        })
        
        return ScheduleDiff(
            affected_tasks=list(set(affected_tasks)),
            delays=delays,
            makespan_change_hours=self.metrics.makespan_hours - other.metrics.makespan_hours
        )
    
    class Config:
        schema_extra = {
            "example": {
                "plan_id": "PLAN-20250815-001",
                "name": "发动机ENG-001准备计划",
                "created_at": "2025-08-15T08:00:00Z",
                "plan_start_time": "2025-08-15T08:00:00Z",
                "plan_end_time": "2025-08-16T08:00:00Z",
                "task_intervals": [],
                "resource_allocations": [],
                "gates": [],
                "critical_path": ["J-001", "J-002"],
                "is_feasible": True,
                "is_optimal": True
            }
        }
