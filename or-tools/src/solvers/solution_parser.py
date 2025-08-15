"""
解析器 (Solution Parser)

负责将求解器的原始输出转换为业务对象。
提供统一的解析接口，支持不同类型的求解器结果。

解析功能：
- 任务时间间隔解析
- 资源分配解析
- 排程指标计算
- 关键路径分析
"""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

from ortools.sat.python import cp_model

from ..models import (
    Job, Resource, PreparationTask, Schedule, TaskInterval, 
    ResourceAllocation, ScheduleMetrics, IntervalType, AllocationStatus
)
from ..core.constants import SolverStatus, TaskStatus
from ..core.exceptions import SolverError


class SolutionParser(ABC):
    """
    解析器抽象基类
    """
    
    @abstractmethod
    def parse_solution(
        self,
        solver_result: Any,
        jobs: List[Job],
        resources: List[Resource],
        preparation_tasks: List[PreparationTask],
        variables: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Schedule:
        """
        解析求解结果
        
        Args:
            solver_result: 求解器结果
            jobs: 工卡子项目列表
            resources: 资源列表
            preparation_tasks: 准备任务列表
            variables: 求解器变量
            config: 配置参数
            
        Returns:
            排程计划
        """
        pass


class CPSATSolutionParser(SolutionParser):
    """
    CP-SAT解析器
    """
    
    def parse_solution(
        self,
        solver_result: Any,
        jobs: List[Job],
        resources: List[Resource],
        preparation_tasks: List[PreparationTask],
        variables: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Schedule:
        """
        解析CP-SAT求解结果
        """
        if not hasattr(solver_result, 'status') or not hasattr(solver_result, 'solve_time_seconds'):
            raise SolverError("Invalid solver result format")

        # 如果solver_result是SolverResult对象，我们需要获取实际的CP-SAT求解器
        # 这里我们需要从外部传入CP-SAT求解器对象
        # 为了兼容性，我们假设config中包含了求解器对象
        cp_solver = config.get('cp_solver')
        if not cp_solver:
            raise SolverError("CP-SAT solver not provided in config")
        
        # 获取变量
        task_starts = variables.get("task_starts", {})
        task_ends = variables.get("task_ends", {})
        task_durations = variables.get("task_durations", {})
        resource_assignments = variables.get("resource_assignments", {})
        
        # 解析任务时间间隔
        print(f"🔍 开始解析任务时间间隔:")
        print(f"   任务数量: {len(jobs)}")
        print(f"   任务开始变量: {len(task_starts)}")
        print(f"   任务结束变量: {len(task_ends)}")
        print(f"   任务持续变量: {len(task_durations)}")

        task_intervals = self._parse_task_intervals(
            cp_solver, jobs, preparation_tasks,
            task_starts, task_ends, task_durations, config
        )

        print(f"   解析得到的任务间隔: {len(task_intervals)}")

        # 解析资源分配
        resource_allocations = self._parse_resource_allocations(
            cp_solver, resources, resource_assignments,
            task_starts, task_ends, config
        )

        # 计算排程指标
        metrics = self._calculate_metrics(
            solver_result, task_intervals, resource_allocations,
            resources, config
        )
        
        # 分析关键路径
        critical_path = self._analyze_critical_path(
            task_intervals, jobs, preparation_tasks
        )
        
        # 创建排程计划
        plan_start_time = self._get_plan_start_time(config)
        plan_end_time = self._calculate_plan_end_time(task_intervals, plan_start_time)
        
        schedule = Schedule(
            plan_id=config.get("plan_id", f"PLAN-{datetime.now().strftime('%Y%m%d-%H%M%S')}"),
            name=config.get("plan_name"),
            description=config.get("plan_description"),
            plan_start_time=plan_start_time,
            plan_end_time=plan_end_time,
            task_intervals=task_intervals,
            resource_allocations=resource_allocations,
            metrics=metrics,
            critical_path=critical_path,
            is_feasible=solver_result.status in [SolverStatus.OPTIMAL, SolverStatus.FEASIBLE],
            is_optimal=solver_result.status == SolverStatus.OPTIMAL,
            solver_config=config.get("solver_config", {}),
            metadata=config.get("metadata", {})
        )
        
        return schedule
    
    def _parse_task_intervals(
        self,
        cp_solver: Any,
        jobs: List[Job],
        preparation_tasks: List[PreparationTask],
        task_starts: Dict[str, cp_model.IntVar],
        task_ends: Dict[str, cp_model.IntVar],
        task_durations: Dict[str, cp_model.IntVar],
        config: Dict[str, Any]
    ) -> List[TaskInterval]:
        """
        解析任务时间间隔
        """
        intervals = []
        plan_start_time = self._get_plan_start_time(config)

        # 解析工卡子项目
        for job in jobs:
            task_id = job.job_id

            if (task_id in task_starts and task_id in task_ends and
                task_id in task_durations):

                start_minutes = cp_solver.Value(task_starts[task_id])
                end_minutes = cp_solver.Value(task_ends[task_id])
                duration_minutes = cp_solver.Value(task_durations[task_id])
                
                start_time = plan_start_time + timedelta(minutes=start_minutes)
                end_time = plan_start_time + timedelta(minutes=end_minutes)
                duration_hours = duration_minutes / 60.0
                
                interval = TaskInterval(
                    task_id=task_id,
                    task_type=IntervalType.JOB,
                    start_time=start_time,
                    end_time=end_time,
                    duration_hours=duration_hours,
                    task_name=job.name,
                    work_package_id=getattr(job, 'work_card_id', None),
                    engine_id=job.engine_id,
                    status=TaskStatus.NOT_STARTED,
                    is_fixed=job.fixed_start is not None
                )
                intervals.append(interval)
        
        # 解析准备任务
        for task in preparation_tasks:
            task_id = task.prep_id
            
            if (task_id in task_starts and task_id in task_ends and 
                task_id in task_durations):
                
                start_minutes = cp_solver.Value(task_starts[task_id])
                end_minutes = cp_solver.Value(task_ends[task_id])
                duration_minutes = cp_solver.Value(task_durations[task_id])
                
                start_time = plan_start_time + timedelta(minutes=start_minutes)
                end_time = plan_start_time + timedelta(minutes=end_minutes)
                duration_hours = duration_minutes / 60.0
                
                interval = TaskInterval(
                    task_id=task_id,
                    task_type=IntervalType.PREPARATION,
                    start_time=start_time,
                    end_time=end_time,
                    duration_hours=duration_hours,
                    task_name=task.name,
                    work_package_id=task.work_package_id,
                    engine_id=task.engine_id,
                    status=TaskStatus.NOT_STARTED
                )
                intervals.append(interval)
        
        return intervals
    
    def _parse_resource_allocations(
        self,
        cp_solver: Any,
        resources: List[Resource],
        resource_assignments: Dict[str, Dict[str, cp_model.BoolVarT]],
        task_starts: Dict[str, cp_model.IntVar],
        task_ends: Dict[str, cp_model.IntVar],
        config: Dict[str, Any]
    ) -> List[ResourceAllocation]:
        """
        解析资源分配
        """
        allocations = []
        plan_start_time = self._get_plan_start_time(config)
        resource_by_id = {r.resource_id: r for r in resources}
        
        for resource_id, assignments in resource_assignments.items():
            resource = resource_by_id.get(resource_id)
            if not resource:
                continue
            
            for task_id, assign_var in assignments.items():
                if cp_solver.Value(assign_var):  # 如果分配变量为True
                    if task_id in task_starts and task_id in task_ends:
                        start_minutes = cp_solver.Value(task_starts[task_id])
                        end_minutes = cp_solver.Value(task_ends[task_id])
                        
                        start_time = plan_start_time + timedelta(minutes=start_minutes)
                        end_time = plan_start_time + timedelta(minutes=end_minutes)
                        
                        # 计算成本
                        cost = None
                        if resource.hourly_cost:
                            duration_hours = (end_minutes - start_minutes) / 60.0
                            cost = resource.hourly_cost * duration_hours
                        
                        allocation = ResourceAllocation(
                            resource_id=resource_id,
                            resource_name=resource.name,
                            allocated_to=task_id,
                            quantity=1,  # 简化处理，假设数量为1
                            start_time=start_time,
                            end_time=end_time,
                            status=AllocationStatus.ALLOCATED,
                            cost=cost
                        )
                        allocations.append(allocation)
        
        return allocations
    
    def _calculate_metrics(
        self,
        solver_result: Any,
        task_intervals: List[TaskInterval],
        resource_allocations: List[ResourceAllocation],
        resources: List[Resource],
        config: Dict[str, Any]
    ) -> ScheduleMetrics:
        """
        计算排程指标
        """
        if not task_intervals:
            return ScheduleMetrics(
                makespan_hours=0.0,
                total_duration_hours=0.0,
                critical_path_length_hours=0.0,
                solve_time_seconds=solver_result.solve_time_seconds,
                solver_status=SolverStatus(solver_result.status.name.lower()),
                objective_value=getattr(solver_result, 'objective_value', None)
            )
        
        # 计算总完工时间
        max_end_time = max(interval.end_time for interval in task_intervals)
        min_start_time = min(interval.start_time for interval in task_intervals)
        makespan_hours = (max_end_time - min_start_time).total_seconds() / 3600
        
        # 计算总持续时间
        total_duration_hours = sum(interval.duration_hours for interval in task_intervals)
        
        # 计算资源利用率
        resource_utilization = self._calculate_resource_utilization(
            resource_allocations, resources, min_start_time, max_end_time
        )
        
        average_utilization = (
            sum(resource_utilization.values()) / len(resource_utilization)
            if resource_utilization else 0.0
        )
        
        # 计算总成本
        total_cost = sum(
            alloc.cost for alloc in resource_allocations 
            if alloc.cost is not None
        )
        
        # 计算等待时间（简化实现）
        total_waiting_time_hours = 0.0  # TODO: 实现等待时间计算
        
        return ScheduleMetrics(
            makespan_hours=makespan_hours,
            total_duration_hours=total_duration_hours,
            critical_path_length_hours=makespan_hours,  # 简化处理
            resource_utilization=resource_utilization,
            average_utilization=average_utilization,
            total_waiting_time_hours=total_waiting_time_hours,
            average_waiting_time_hours=total_waiting_time_hours / len(task_intervals) if task_intervals else 0.0,
            total_cost=total_cost if total_cost > 0 else None,
            constraint_violations=0,  # TODO: 实现约束违反检查
            solve_time_seconds=solver_result.solve_time_seconds,
            solver_status=SolverStatus(solver_result.status.name.lower()),
            objective_value=getattr(solver_result, 'objective_value', None)
        )
    
    def _calculate_resource_utilization(
        self,
        resource_allocations: List[ResourceAllocation],
        resources: List[Resource],
        plan_start: datetime,
        plan_end: datetime
    ) -> Dict[str, float]:
        """
        计算资源利用率
        """
        utilization = {}
        total_plan_hours = (plan_end - plan_start).total_seconds() / 3600
        
        if total_plan_hours <= 0:
            return utilization
        
        # 按资源分组分配
        allocations_by_resource = {}
        for alloc in resource_allocations:
            if alloc.resource_id not in allocations_by_resource:
                allocations_by_resource[alloc.resource_id] = []
            allocations_by_resource[alloc.resource_id].append(alloc)
        
        # 计算每个资源的利用率
        for resource in resources:
            resource_id = resource.resource_id
            resource_allocations_list = allocations_by_resource.get(resource_id, [])
            
            if not resource_allocations_list:
                utilization[resource_id] = 0.0
                continue
            
            # 计算总使用时间
            total_used_hours = sum(
                alloc.get_duration_hours() for alloc in resource_allocations_list
            )
            
            # 利用率 = 使用时间 / 计划时间
            utilization[resource_id] = min(total_used_hours / total_plan_hours, 1.0)
        
        return utilization
    
    def _analyze_critical_path(
        self,
        task_intervals: List[TaskInterval],
        jobs: List[Job],
        preparation_tasks: List[PreparationTask]
    ) -> List[str]:
        """
        分析关键路径
        """
        # 简化实现：返回最长路径上的任务
        # TODO: 实现真正的关键路径分析算法
        
        if not task_intervals:
            return []
        
        # 按结束时间排序，取最晚结束的任务作为关键路径的一部分
        sorted_intervals = sorted(task_intervals, key=lambda x: x.end_time, reverse=True)
        
        # 简单地返回前几个任务作为关键路径
        critical_path_length = min(len(sorted_intervals), 5)
        critical_path = [interval.task_id for interval in sorted_intervals[:critical_path_length]]
        
        return critical_path
    
    def _get_plan_start_time(self, config: Dict[str, Any]) -> datetime:
        """
        获取计划开始时间
        """
        plan_start = config.get("plan_start_time", datetime.now())
        if isinstance(plan_start, str):
            plan_start = datetime.fromisoformat(plan_start.replace('Z', '+00:00'))
        return plan_start
    
    def _calculate_plan_end_time(
        self,
        task_intervals: List[TaskInterval],
        plan_start_time: datetime
    ) -> datetime:
        """
        计算计划结束时间
        """
        if not task_intervals:
            # 如果没有任务间隔，返回开始时间后1小时作为默认结束时间
            return plan_start_time + timedelta(hours=1)

        max_end_time = max(interval.end_time for interval in task_intervals)

        # 确保结束时间在开始时间之后
        if max_end_time <= plan_start_time:
            return plan_start_time + timedelta(hours=1)

        return max_end_time
