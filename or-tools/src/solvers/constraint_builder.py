"""
约束构建器 (Constraint Builder)

负责将业务规则转换为求解器可理解的约束条件。
支持各种类型的约束，包括硬约束和软约束。

约束类型：
- 前置约束：任务依赖关系
- 资源约束：资源容量和独占性
- 时间约束：时间窗和固定时间
- 资质约束：人员资质匹配
- 门禁约束：准备阶段门禁条件
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from abc import ABC, abstractmethod

from ortools.sat.python import cp_model

from ..models import Job, Resource, PreparationTask, HumanResource, PhysicalResource
from ..core.exceptions import ConstraintViolationError
from ..core.constants import ConstraintType, ResourceType


class ConstraintBuilder(ABC):
    """
    约束构建器抽象基类
    
    定义约束构建的通用接口和方法。
    """
    
    def __init__(self, model: cp_model.CpModel):
        """
        初始化约束构建器
        
        Args:
            model: CP-SAT模型实例
        """
        self.model = model
        self.constraints: Dict[str, Any] = {}
        self.variables: Dict[str, Any] = {}
        
    @abstractmethod
    def build_constraints(
        self,
        jobs: List[Job],
        resources: List[Resource],
        preparation_tasks: List[PreparationTask],
        constraint_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        构建所有约束
        
        Args:
            jobs: 工卡子项目列表
            resources: 资源列表
            preparation_tasks: 准备任务列表
            constraint_config: 约束配置
            
        Returns:
            约束信息字典
        """
        pass
    
    def add_constraint(self, name: str, constraint: Any) -> None:
        """
        添加约束
        
        Args:
            name: 约束名称
            constraint: 约束对象
        """
        self.constraints[name] = constraint
    
    def get_constraint(self, name: str) -> Optional[Any]:
        """
        获取约束
        
        Args:
            name: 约束名称
            
        Returns:
            约束对象，如果不存在则返回None
        """
        return self.constraints.get(name)
    
    def add_variable(self, name: str, variable: Any) -> None:
        """
        添加变量
        
        Args:
            name: 变量名称
            variable: 变量对象
        """
        self.variables[name] = variable
    
    def get_variable(self, name: str) -> Optional[Any]:
        """
        获取变量
        
        Args:
            name: 变量名称
            
        Returns:
            变量对象，如果不存在则返回None
        """
        return self.variables.get(name)


class CPSATConstraintBuilder(ConstraintBuilder):
    """
    CP-SAT约束构建器
    
    专门为Google OR-Tools CP-SAT求解器构建约束。
    """
    
    def __init__(self, model: cp_model.CpModel):
        super().__init__(model)
        self.task_intervals: Dict[str, cp_model.IntervalVar] = {}
        self.task_starts: Dict[str, cp_model.IntVar] = {}
        self.task_ends: Dict[str, cp_model.IntVar] = {}
        self.task_durations: Dict[str, cp_model.IntVar] = {}
        self.resource_assignments: Dict[str, Dict[str, cp_model.BoolVarT]] = {}
        
    def build_constraints(
        self,
        jobs: List[Job],
        resources: List[Resource],
        preparation_tasks: List[PreparationTask],
        constraint_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        构建所有约束
        """
        # 创建任务变量
        self._create_task_variables(jobs, preparation_tasks, constraint_config)
        
        # 构建前置约束
        self._build_precedence_constraints(jobs, preparation_tasks)
        
        # 构建资源约束
        self._build_resource_constraints(jobs, preparation_tasks, resources, constraint_config)
        
        # 构建时间窗约束
        self._build_time_window_constraints(jobs, preparation_tasks, constraint_config)
        
        # 构建资质约束
        self._build_qualification_constraints(jobs, resources, constraint_config)
        
        # 构建门禁约束
        self._build_gate_constraints(preparation_tasks, constraint_config)

        # 构建任务执行约束（强制所有任务必须被执行）
        self._build_task_execution_constraints(jobs, resources)

        return {
            "task_intervals": self.task_intervals,
            "task_starts": self.task_starts,
            "task_ends": self.task_ends,
            "task_durations": self.task_durations,  # 添加缺失的任务持续变量
            "resource_assignments": self.resource_assignments,
            "constraints": self.constraints
        }
    
    def _create_task_variables(
        self,
        jobs: List[Job],
        preparation_tasks: List[PreparationTask],
        config: Dict[str, Any]
    ) -> None:
        """
        创建任务相关的变量
        """
        # 时间范围配置
        time_horizon = config.get("time_horizon_hours", 168)  # 默认一周

        print(f"🔍 创建任务变量:")
        print(f"   任务数量: {len(jobs)}")
        print(f"   时间范围: {time_horizon} 小时")
        
        # 为工卡子项目创建变量
        for job in jobs:
            task_id = job.job_id
            
            # 持续时间（考虑固定持续时间）
            if job.fixed_duration:
                duration = int(job.fixed_duration * 60)  # 转换为分钟
                duration_var = self.model.NewConstant(duration)
            else:
                min_duration = int(job.base_duration_hours * 60 * 0.8)  # 最小80%
                max_duration = int(job.base_duration_hours * 60 * 1.5)  # 最大150%
                duration_var = self.model.NewIntVar(min_duration, max_duration, f"duration_{task_id}")
            
            # 开始时间
            start_var = self.model.NewIntVar(0, time_horizon * 60, f"start_{task_id}")
            
            # 结束时间
            end_var = self.model.NewIntVar(0, time_horizon * 60, f"end_{task_id}")
            
            # 时间间隔
            interval_var = self.model.NewIntervalVar(
                start_var, duration_var, end_var, f"interval_{task_id}"
            )
            
            # 存储变量
            self.task_starts[task_id] = start_var
            self.task_ends[task_id] = end_var
            self.task_durations[task_id] = duration_var
            self.task_intervals[task_id] = interval_var

            print(f"   创建任务 {task_id}: 持续时间 {job.base_duration_hours}h")
            
            # 添加变量到字典
            self.add_variable(f"start_{task_id}", start_var)
            self.add_variable(f"end_{task_id}", end_var)
            self.add_variable(f"duration_{task_id}", duration_var)
            self.add_variable(f"interval_{task_id}", interval_var)
        
        # 为准备任务创建变量
        for task in preparation_tasks:
            task_id = task.prep_id
            
            # 持续时间
            duration = int(task.duration_hours * 60)  # 转换为分钟
            duration_var = self.model.NewConstant(duration)
            
            # 开始时间
            start_var = self.model.NewIntVar(0, time_horizon * 60, f"start_{task_id}")
            
            # 结束时间
            end_var = self.model.NewIntVar(0, time_horizon * 60, f"end_{task_id}")
            
            # 时间间隔
            interval_var = self.model.NewIntervalVar(
                start_var, duration_var, end_var, f"interval_{task_id}"
            )
            
            # 存储变量
            self.task_starts[task_id] = start_var
            self.task_ends[task_id] = end_var
            self.task_durations[task_id] = duration_var
            self.task_intervals[task_id] = interval_var
            
            # 添加变量到字典
            self.add_variable(f"start_{task_id}", start_var)
            self.add_variable(f"end_{task_id}", end_var)
            self.add_variable(f"duration_{task_id}", duration_var)
            self.add_variable(f"interval_{task_id}", interval_var)
    
    def _build_precedence_constraints(
        self,
        jobs: List[Job],
        preparation_tasks: List[PreparationTask]
    ) -> None:
        """
        构建前置约束
        """
        # 工卡子项目的前置约束
        for job in jobs:
            for predecessor_id in job.predecessor_jobs:
                if predecessor_id in self.task_ends and job.job_id in self.task_starts:
                    constraint = self.model.Add(
                        self.task_ends[predecessor_id] <= self.task_starts[job.job_id]
                    )
                    self.add_constraint(
                        f"precedence_{predecessor_id}_{job.job_id}",
                        constraint
                    )
        
        # 准备任务的前置约束
        for task in preparation_tasks:
            for dependency_id in task.dependencies:
                if dependency_id in self.task_ends and task.prep_id in self.task_starts:
                    constraint = self.model.Add(
                        self.task_ends[dependency_id] <= self.task_starts[task.prep_id]
                    )
                    self.add_constraint(
                        f"precedence_{dependency_id}_{task.prep_id}",
                        constraint
                    )
    
    def _build_resource_constraints(
        self,
        jobs: List[Job],
        preparation_tasks: List[PreparationTask],
        resources: List[Resource],
        config: Dict[str, Any]
    ) -> None:
        """
        构建资源约束
        """
        # 按资源类型分组
        resource_by_id = {r.resource_id: r for r in resources}
        
        # 为每个资源创建分配变量
        for resource in resources:
            resource_id = resource.resource_id
            self.resource_assignments[resource_id] = {}

            # 收集需要此资源的所有任务
            requiring_tasks = []

            # 对于人力资源，为所有任务创建分配变量（支持协作）
            if isinstance(resource, HumanResource):
                for job in jobs:
                    requiring_tasks.append(job.job_id)
                    # 创建分配变量
                    assign_var = self.model.NewBoolVar(f"assign_{resource_id}_{job.job_id}")
                    self.resource_assignments[resource_id][job.job_id] = assign_var
            else:
                # 对于物理资源，只为明确需要的任务创建分配变量
                for job in jobs:
                    if job.has_resource_requirement(resource_id):
                        requiring_tasks.append(job.job_id)
                        # 创建分配变量
                        assign_var = self.model.NewBoolVar(f"assign_{resource_id}_{job.job_id}")
                        self.resource_assignments[resource_id][job.job_id] = assign_var
            
            # 检查准备任务
            for task in preparation_tasks:
                for asset_req in task.required_assets:
                    if asset_req.get("asset_id") == resource_id:
                        requiring_tasks.append(task.prep_id)
                        # 创建分配变量
                        assign_var = self.model.NewBoolVar(f"assign_{resource_id}_{task.prep_id}")
                        self.resource_assignments[resource_id][task.prep_id] = assign_var
            
            # 构建资源容量约束
            if isinstance(resource, PhysicalResource) and resource.is_exclusive:
                # 独占资源：同一时间只能分配给一个任务
                self._build_exclusive_resource_constraint(resource_id, requiring_tasks)
            else:
                # 可累积资源：考虑数量限制
                self._build_cumulative_resource_constraint(resource, requiring_tasks)
    
    def _build_exclusive_resource_constraint(
        self,
        resource_id: str,
        requiring_tasks: List[str]
    ) -> None:
        """
        构建独占资源约束
        """
        if len(requiring_tasks) <= 1:
            return
        
        # 收集分配给此资源的任务间隔
        intervals = []
        for task_id in requiring_tasks:
            if (resource_id in self.resource_assignments and 
                task_id in self.resource_assignments[resource_id] and
                task_id in self.task_intervals):
                
                assign_var = self.resource_assignments[resource_id][task_id]
                interval_var = self.task_intervals[task_id]
                
                # 创建可选间隔（只有分配时才激活）
                optional_interval = self.model.NewOptionalIntervalVar(
                    self.task_starts[task_id],
                    self.task_durations[task_id],
                    self.task_ends[task_id],
                    assign_var,
                    f"optional_{resource_id}_{task_id}"
                )
                intervals.append(optional_interval)
        
        # 添加无重叠约束
        if intervals:
            constraint = self.model.AddNoOverlap(intervals)
            self.add_constraint(f"no_overlap_{resource_id}", constraint)
    
    def _build_cumulative_resource_constraint(
        self,
        resource: Resource,
        requiring_tasks: List[str]
    ) -> None:
        """
        构建可累积资源约束
        """
        if resource.total_quantity <= 1:
            # 数量为1的资源按独占处理
            self._build_exclusive_resource_constraint(resource.resource_id, requiring_tasks)
            return
        
        # TODO: 实现累积资源约束
        # 这需要考虑每个任务的资源需求量和资源的总容量
        pass
    
    def _build_time_window_constraints(
        self,
        jobs: List[Job],
        preparation_tasks: List[PreparationTask],
        config: Dict[str, Any]
    ) -> None:
        """
        构建时间窗约束
        """
        # 工卡子项目的时间窗约束
        for job in jobs:
            task_id = job.job_id
            
            if job.earliest_start and task_id in self.task_starts:
                earliest_minutes = self._datetime_to_minutes(job.earliest_start, config)
                constraint = self.model.Add(self.task_starts[task_id] >= earliest_minutes)
                self.add_constraint(f"earliest_start_{task_id}", constraint)
            
            if job.latest_finish and task_id in self.task_ends:
                latest_minutes = self._datetime_to_minutes(job.latest_finish, config)
                constraint = self.model.Add(self.task_ends[task_id] <= latest_minutes)
                self.add_constraint(f"latest_finish_{task_id}", constraint)
            
            if job.fixed_start and task_id in self.task_starts:
                fixed_minutes = self._datetime_to_minutes(job.fixed_start, config)
                constraint = self.model.Add(self.task_starts[task_id] == fixed_minutes)
                self.add_constraint(f"fixed_start_{task_id}", constraint)
        
        # 准备任务的时间窗约束
        for task in preparation_tasks:
            task_id = task.prep_id
            
            if task.earliest_start and task_id in self.task_starts:
                earliest_minutes = self._datetime_to_minutes(task.earliest_start, config)
                constraint = self.model.Add(self.task_starts[task_id] >= earliest_minutes)
                self.add_constraint(f"earliest_start_{task_id}", constraint)
            
            if task.latest_finish and task_id in self.task_ends:
                latest_minutes = self._datetime_to_minutes(task.latest_finish, config)
                constraint = self.model.Add(self.task_ends[task_id] <= latest_minutes)
                self.add_constraint(f"latest_finish_{task_id}", constraint)
    
    def _build_qualification_constraints(
        self,
        jobs: List[Job],
        resources: List[Resource],
        config: Dict[str, Any]
    ) -> None:
        """
        构建资质约束 - 支持多人协作
        """
        # 获取人力资源
        human_resources = [r for r in resources if isinstance(r, HumanResource)]

        for job in jobs:
            if not job.required_qualifications:
                continue

            job_id = job.job_id

            # 检查是否有足够的人员来覆盖所有技能
            self._build_collaborative_qualification_constraint(
                job, human_resources, job_id
            )

    def _build_collaborative_qualification_constraint(
        self,
        job: Job,
        human_resources: List[HumanResource],
        job_id: str
    ) -> None:
        """
        构建协作资质约束 - 允许多人协作完成任务
        """
        required_qualifications = job.required_qualifications

        # 为每个需要的技能创建约束
        for qualification in required_qualifications:
            # 找到拥有此技能的所有人员
            qualified_for_skill = []
            for hr in human_resources:
                if hr.has_qualification(qualification):
                    if (hr.resource_id in self.resource_assignments and
                        job_id in self.resource_assignments[hr.resource_id]):
                        qualified_for_skill.append(
                            self.resource_assignments[hr.resource_id][job_id]
                        )

            if not qualified_for_skill:
                raise ConstraintViolationError(
                    f"No personnel found with qualification '{qualification}' "
                    f"for job {job_id}"
                )

            # 确保至少有一个拥有此技能的人员被分配到此任务
            constraint = self.model.Add(sum(qualified_for_skill) >= 1)
            self.add_constraint(f"qualification_{job_id}_{qualification}", constraint)
    
    def _build_gate_constraints(
        self,
        preparation_tasks: List[PreparationTask],
        config: Dict[str, Any]
    ) -> None:
        """
        构建门禁约束
        """
        # 按工包分组门禁任务
        gate_tasks_by_package = {}
        for task in preparation_tasks:
            if task.is_gate:
                package_id = task.work_package_id
                if package_id not in gate_tasks_by_package:
                    gate_tasks_by_package[package_id] = []
                gate_tasks_by_package[package_id].append(task)
        
        # 为每个工包构建门禁约束
        for package_id, gate_tasks in gate_tasks_by_package.items():
            # 所有门禁任务必须在工包开始前完成
            # 这里需要与实际的工包任务关联，暂时跳过具体实现
            pass

    def _build_task_execution_constraints(
        self,
        jobs: List[Job],
        resources: List[Resource]
    ) -> None:
        """
        构建任务执行约束 - 强制所有任务必须被执行
        """
        # 获取人力资源
        human_resources = [r for r in resources if isinstance(r, HumanResource)]

        print(f"🔍 构建任务执行约束:")
        print(f"   任务数量: {len(jobs)}")
        print(f"   人力资源数量: {len(human_resources)}")
        print(f"   任务变量数量: {len(self.task_starts)}")
        print(f"   资源分配变量: {len(self.resource_assignments)}")

        for job in jobs:
            job_id = job.job_id

            # 确保每个任务至少分配给一个人员
            if job_id in self.task_starts:  # 确保任务变量已创建
                assigned_personnel = []

                for hr in human_resources:
                    if (hr.resource_id in self.resource_assignments and
                        job_id in self.resource_assignments[hr.resource_id]):
                        assigned_personnel.append(
                            self.resource_assignments[hr.resource_id][job_id]
                        )

                print(f"   任务 {job_id}: {len(assigned_personnel)} 个分配变量")

                if assigned_personnel:
                    # 至少有一个人员必须被分配到此任务
                    constraint = self.model.Add(sum(assigned_personnel) >= 1)
                    self.add_constraint(f"task_execution_{job_id}", constraint)
                    print(f"     ✅ 添加执行约束")
                else:
                    print(f"     ❌ 没有分配变量")
            else:
                print(f"   任务 {job_id}: 没有任务变量")
    
    def _datetime_to_minutes(self, dt: datetime, config: Dict[str, Any]) -> int:
        """
        将datetime转换为相对于计划开始时间的分钟数
        """
        plan_start = config.get("plan_start_time", datetime.now())
        if isinstance(plan_start, str):
            plan_start = datetime.fromisoformat(plan_start.replace('Z', '+00:00'))
        
        delta = dt - plan_start
        return int(delta.total_seconds() / 60)
