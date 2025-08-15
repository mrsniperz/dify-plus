"""
资源管理服务 (Resource Service)

负责资源分配、冲突检测和利用率管理的业务逻辑。
提供资源状态查询、分配验证、冲突解决等功能。

主要功能：
- 资源可用性检查
- 资源分配和释放
- 冲突检测和解决
- 利用率统计和分析
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from ..models import (
    Resource, HumanResource, PhysicalResource, ResourceAllocation,
    Schedule, TaskInterval, ResourceAvailability
)
from ..core.exceptions import ResourceConflictError, ValidationError
from ..core.constants import ResourceType
from ..models.resource import AvailabilityStatus


logger = logging.getLogger(__name__)


class ResourceConflict:
    """资源冲突模型"""
    
    def __init__(
        self,
        resource_id: str,
        conflicting_allocations: List[ResourceAllocation],
        conflict_type: str,
        severity: str = "medium"
    ):
        self.resource_id = resource_id
        self.conflicting_allocations = conflicting_allocations
        self.conflict_type = conflict_type
        self.severity = severity
        self.detected_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "resource_id": self.resource_id,
            "conflict_type": self.conflict_type,
            "severity": self.severity,
            "detected_at": self.detected_at.isoformat(),
            "conflicting_allocations": [
                {
                    "allocated_to": alloc.allocated_to,
                    "start_time": alloc.start_time.isoformat(),
                    "end_time": alloc.end_time.isoformat(),
                    "quantity": alloc.quantity
                }
                for alloc in self.conflicting_allocations
            ]
        }


class ResourceUtilization:
    """资源利用率模型"""
    
    def __init__(
        self,
        resource_id: str,
        total_available_hours: float,
        allocated_hours: float,
        utilization_rate: float
    ):
        self.resource_id = resource_id
        self.total_available_hours = total_available_hours
        self.allocated_hours = allocated_hours
        self.utilization_rate = utilization_rate
        self.calculated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "resource_id": self.resource_id,
            "total_available_hours": self.total_available_hours,
            "allocated_hours": self.allocated_hours,
            "utilization_rate": self.utilization_rate,
            "calculated_at": self.calculated_at.isoformat()
        }


class ResourceService:
    """
    资源管理服务
    
    提供资源管理的核心业务逻辑。
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._resource_cache: Dict[str, Resource] = {}
        self._allocation_cache: Dict[str, List[ResourceAllocation]] = {}
    
    def check_resource_availability(
        self,
        resource_id: str,
        start_time: datetime,
        end_time: datetime,
        required_quantity: int = 1
    ) -> bool:
        """
        检查资源在指定时间段的可用性
        
        Args:
            resource_id: 资源ID
            start_time: 开始时间
            end_time: 结束时间
            required_quantity: 需求数量
            
        Returns:
            是否可用
        """
        try:
            resource = self._get_resource(resource_id)
            if not resource:
                return False
            
            # 检查基本可用性
            if not resource.is_available_at(start_time):
                return False
            
            # 检查数量
            available_quantity = resource.get_available_quantity_at(start_time)
            if available_quantity < required_quantity:
                return False
            
            # 检查时间段内的分配冲突
            existing_allocations = self._get_allocations_in_period(
                resource_id, start_time, end_time
            )
            
            # 计算已分配数量
            allocated_quantity = sum(
                alloc.quantity for alloc in existing_allocations
                if self._time_periods_overlap(
                    start_time, end_time,
                    alloc.start_time, alloc.end_time
                )
            )
            
            return available_quantity >= allocated_quantity + required_quantity
            
        except Exception as e:
            self.logger.error(f"Error checking availability for resource {resource_id}: {e}")
            return False
    
    def allocate_resource(
        self,
        resource_id: str,
        task_id: str,
        start_time: datetime,
        end_time: datetime,
        quantity: int = 1
    ) -> ResourceAllocation:
        """
        分配资源
        
        Args:
            resource_id: 资源ID
            task_id: 任务ID
            start_time: 开始时间
            end_time: 结束时间
            quantity: 数量
            
        Returns:
            资源分配对象
            
        Raises:
            ResourceConflictError: 资源冲突时抛出
            ValidationError: 参数验证失败时抛出
        """
        # 验证参数
        if start_time >= end_time:
            raise ValidationError("Start time must be before end time")
        
        if quantity <= 0:
            raise ValidationError("Quantity must be positive")
        
        # 检查可用性
        if not self.check_resource_availability(resource_id, start_time, end_time, quantity):
            raise ResourceConflictError(
                f"Resource {resource_id} not available for allocation",
                conflicting_resources=[resource_id]
            )
        
        # 创建分配
        resource = self._get_resource(resource_id)
        cost = None
        if resource and resource.hourly_cost:
            duration_hours = (end_time - start_time).total_seconds() / 3600
            cost = resource.hourly_cost * duration_hours * quantity
        
        allocation = ResourceAllocation(
            resource_id=resource_id,
            resource_name=resource.name if resource else None,
            allocated_to=task_id,
            quantity=quantity,
            start_time=start_time,
            end_time=end_time,
            cost=cost
        )
        
        # 缓存分配
        if resource_id not in self._allocation_cache:
            self._allocation_cache[resource_id] = []
        self._allocation_cache[resource_id].append(allocation)
        
        self.logger.info(f"Allocated resource {resource_id} to task {task_id}")
        
        return allocation
    
    def release_resource(
        self,
        resource_id: str,
        task_id: str,
        release_time: Optional[datetime] = None
    ) -> bool:
        """
        释放资源
        
        Args:
            resource_id: 资源ID
            task_id: 任务ID
            release_time: 释放时间，默认为当前时间
            
        Returns:
            是否成功释放
        """
        try:
            release_time = release_time or datetime.now()
            
            # 查找分配
            allocations = self._allocation_cache.get(resource_id, [])
            for allocation in allocations:
                if allocation.allocated_to == task_id:
                    # 更新分配状态
                    allocation.status = "released"
                    allocation.end_time = min(allocation.end_time, release_time)
                    
                    self.logger.info(f"Released resource {resource_id} from task {task_id}")
                    return True
            
            self.logger.warning(f"No allocation found for resource {resource_id} and task {task_id}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error releasing resource {resource_id}: {e}")
            return False
    
    def detect_conflicts(
        self,
        schedule: Schedule,
        resources: List[Resource]
    ) -> List[ResourceConflict]:
        """
        检测资源冲突
        
        Args:
            schedule: 排程计划
            resources: 资源列表
            
        Returns:
            冲突列表
        """
        conflicts = []
        
        try:
            # 按资源分组分配
            allocations_by_resource = defaultdict(list)
            for allocation in schedule.resource_allocations:
                allocations_by_resource[allocation.resource_id].append(allocation)
            
            # 检查每个资源的冲突
            for resource in resources:
                resource_id = resource.resource_id
                allocations = allocations_by_resource.get(resource_id, [])
                
                if len(allocations) <= 1:
                    continue
                
                # 检查时间重叠
                overlapping_allocations = self._find_overlapping_allocations(allocations)
                if overlapping_allocations:
                    conflict_type = "time_overlap"
                    if isinstance(resource, PhysicalResource) and resource.is_exclusive:
                        conflict_type = "exclusive_resource_conflict"
                    
                    conflict = ResourceConflict(
                        resource_id=resource_id,
                        conflicting_allocations=overlapping_allocations,
                        conflict_type=conflict_type,
                        severity="high" if conflict_type == "exclusive_resource_conflict" else "medium"
                    )
                    conflicts.append(conflict)
                
                # 检查容量超限
                capacity_conflicts = self._check_capacity_conflicts(resource, allocations)
                conflicts.extend(capacity_conflicts)
            
            self.logger.info(f"Detected {len(conflicts)} resource conflicts")
            
        except Exception as e:
            self.logger.error(f"Error detecting conflicts: {e}")
        
        return conflicts
    
    def calculate_utilization(
        self,
        schedule: Schedule,
        resources: List[Resource],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[ResourceUtilization]:
        """
        计算资源利用率
        
        Args:
            schedule: 排程计划
            resources: 资源列表
            start_time: 统计开始时间
            end_time: 统计结束时间
            
        Returns:
            利用率列表
        """
        utilizations = []
        
        try:
            # 确定时间范围
            if not start_time:
                start_time = schedule.plan_start_time
            if not end_time:
                end_time = schedule.plan_end_time
            
            total_period_hours = (end_time - start_time).total_seconds() / 3600
            
            # 按资源分组分配
            allocations_by_resource = defaultdict(list)
            for allocation in schedule.resource_allocations:
                allocations_by_resource[allocation.resource_id].append(allocation)
            
            # 计算每个资源的利用率
            for resource in resources:
                resource_id = resource.resource_id
                allocations = allocations_by_resource.get(resource_id, [])
                
                # 计算总可用时间
                total_available_hours = self._calculate_available_hours(
                    resource, start_time, end_time
                )
                
                # 计算已分配时间
                allocated_hours = sum(
                    allocation.get_duration_hours()
                    for allocation in allocations
                    if self._allocation_in_period(allocation, start_time, end_time)
                )
                
                # 计算利用率
                utilization_rate = (
                    allocated_hours / total_available_hours
                    if total_available_hours > 0 else 0.0
                )
                
                utilization = ResourceUtilization(
                    resource_id=resource_id,
                    total_available_hours=total_available_hours,
                    allocated_hours=allocated_hours,
                    utilization_rate=min(utilization_rate, 1.0)  # 限制在100%以内
                )
                utilizations.append(utilization)
            
            self.logger.info(f"Calculated utilization for {len(resources)} resources")
            
        except Exception as e:
            self.logger.error(f"Error calculating utilization: {e}")
        
        return utilizations
    
    def get_resource_summary(
        self,
        plan_id: str,
        schedule: Schedule,
        resources: List[Resource]
    ) -> Dict[str, Any]:
        """
        获取资源汇总信息
        
        Args:
            plan_id: 计划ID
            schedule: 排程计划
            resources: 资源列表
            
        Returns:
            资源汇总信息
        """
        try:
            # 检测冲突
            conflicts = self.detect_conflicts(schedule, resources)
            
            # 计算利用率
            utilizations = self.calculate_utilization(schedule, resources)
            
            # 统计信息
            total_resources = len(resources)
            human_resources = len([r for r in resources if isinstance(r, HumanResource)])
            physical_resources = len([r for r in resources if isinstance(r, PhysicalResource)])
            
            # 平均利用率
            avg_utilization = (
                sum(u.utilization_rate for u in utilizations) / len(utilizations)
                if utilizations else 0.0
            )
            
            # 利用率分布
            utilization_by_resource = {
                u.resource_id: u.utilization_rate for u in utilizations
            }
            
            return {
                "plan_id": plan_id,
                "summary": {
                    "total_resources": total_resources,
                    "human_resources": human_resources,
                    "physical_resources": physical_resources,
                    "conflicts_count": len(conflicts),
                    "average_utilization": avg_utilization
                },
                "utilization": utilization_by_resource,
                "conflicts": [conflict.to_dict() for conflict in conflicts],
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating resource summary: {e}")
            return {
                "plan_id": plan_id,
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }
    
    def _get_resource(self, resource_id: str) -> Optional[Resource]:
        """获取资源对象"""
        return self._resource_cache.get(resource_id)
    
    def _get_allocations_in_period(
        self,
        resource_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[ResourceAllocation]:
        """获取指定时间段内的资源分配"""
        allocations = self._allocation_cache.get(resource_id, [])
        return [
            alloc for alloc in allocations
            if self._time_periods_overlap(
                start_time, end_time,
                alloc.start_time, alloc.end_time
            )
        ]
    
    def _time_periods_overlap(
        self,
        start1: datetime, end1: datetime,
        start2: datetime, end2: datetime
    ) -> bool:
        """检查两个时间段是否重叠"""
        return not (end1 <= start2 or end2 <= start1)
    
    def _find_overlapping_allocations(
        self,
        allocations: List[ResourceAllocation]
    ) -> List[ResourceAllocation]:
        """查找重叠的分配"""
        overlapping = []
        
        for i, alloc1 in enumerate(allocations):
            for alloc2 in allocations[i+1:]:
                if self._time_periods_overlap(
                    alloc1.start_time, alloc1.end_time,
                    alloc2.start_time, alloc2.end_time
                ):
                    if alloc1 not in overlapping:
                        overlapping.append(alloc1)
                    if alloc2 not in overlapping:
                        overlapping.append(alloc2)
        
        return overlapping
    
    def _check_capacity_conflicts(
        self,
        resource: Resource,
        allocations: List[ResourceAllocation]
    ) -> List[ResourceConflict]:
        """检查容量冲突"""
        conflicts = []
        
        # 简化实现：检查同一时间点的分配总量是否超过资源容量
        time_points = set()
        for alloc in allocations:
            time_points.add(alloc.start_time)
            time_points.add(alloc.end_time)
        
        for time_point in time_points:
            concurrent_allocations = [
                alloc for alloc in allocations
                if alloc.start_time <= time_point < alloc.end_time
            ]
            
            total_allocated = sum(alloc.quantity for alloc in concurrent_allocations)
            
            if total_allocated > resource.total_quantity:
                conflict = ResourceConflict(
                    resource_id=resource.resource_id,
                    conflicting_allocations=concurrent_allocations,
                    conflict_type="capacity_exceeded",
                    severity="high"
                )
                conflicts.append(conflict)
        
        return conflicts
    
    def _calculate_available_hours(
        self,
        resource: Resource,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """计算资源在指定时间段的可用小时数"""
        if resource.calendar:
            # 使用资源日历计算可用时间
            # 简化实现：假设每天8小时工作时间
            total_days = (end_time - start_time).days
            return total_days * 8.0
        else:
            # 没有日历限制，按全天24小时计算
            return (end_time - start_time).total_seconds() / 3600
    
    def _allocation_in_period(
        self,
        allocation: ResourceAllocation,
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """检查分配是否在指定时间段内"""
        return self._time_periods_overlap(
            start_time, end_time,
            allocation.start_time, allocation.end_time
        )
    
    def update_resource_cache(self, resources: List[Resource]) -> None:
        """更新资源缓存"""
        self._resource_cache.clear()
        for resource in resources:
            self._resource_cache[resource.resource_id] = resource
    
    def clear_allocation_cache(self) -> None:
        """清空分配缓存"""
        self._allocation_cache.clear()
