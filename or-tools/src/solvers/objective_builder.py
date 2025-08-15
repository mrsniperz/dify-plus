"""
目标函数构建器 (Objective Builder)

负责构建求解器的目标函数，支持多目标优化和权重配置。
将业务优化目标转换为求解器可理解的数学表达式。

优化目标：
- 最小化总完工时间（makespan）
- 最小化总成本
- 最大化资源利用率
- 最小化等待时间
- 最小化切换成本
"""

from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
from enum import Enum

from ortools.sat.python import cp_model

from ..models import Job, Resource, PreparationTask
from ..core.constants import PriorityTemplate
from ..core.exceptions import ConfigurationError


class ObjectiveType(str, Enum):
    """目标类型枚举"""
    MINIMIZE_MAKESPAN = "minimize_makespan"           # 最小化总完工时间
    MINIMIZE_COST = "minimize_cost"                   # 最小化总成本
    MAXIMIZE_UTILIZATION = "maximize_utilization"     # 最大化资源利用率
    MINIMIZE_WAITING = "minimize_waiting"             # 最小化等待时间
    MINIMIZE_SWITCHES = "minimize_switches"           # 最小化切换次数
    MINIMIZE_DELAYS = "minimize_delays"               # 最小化延误
    MAXIMIZE_PREFERENCE = "maximize_preference"       # 最大化偏好匹配


class ObjectiveWeight:
    """目标权重配置"""
    
    def __init__(
        self,
        makespan: float = 1.0,
        cost: float = 0.1,
        utilization: float = 0.1,
        waiting: float = 0.2,
        switches: float = 0.1,
        delays: float = 0.5,
        preference: float = 0.05
    ):
        """
        初始化目标权重
        
        Args:
            makespan: 总完工时间权重
            cost: 成本权重
            utilization: 资源利用率权重
            waiting: 等待时间权重
            switches: 切换次数权重
            delays: 延误权重
            preference: 偏好匹配权重
        """
        self.makespan = makespan
        self.cost = cost
        self.utilization = utilization
        self.waiting = waiting
        self.switches = switches
        self.delays = delays
        self.preference = preference
    
    def to_dict(self) -> Dict[str, float]:
        """转换为字典格式"""
        return {
            "makespan": self.makespan,
            "cost": self.cost,
            "utilization": self.utilization,
            "waiting": self.waiting,
            "switches": self.switches,
            "delays": self.delays,
            "preference": self.preference
        }
    
    @classmethod
    def from_template(cls, template: PriorityTemplate) -> 'ObjectiveWeight':
        """
        从策略模板创建权重配置
        
        Args:
            template: 策略模板
            
        Returns:
            权重配置实例
        """
        if template == PriorityTemplate.BALANCED:
            return cls(
                makespan=1.0,
                cost=0.3,
                utilization=0.2,
                waiting=0.4,
                switches=0.2,
                delays=0.6,
                preference=0.1
            )
        elif template == PriorityTemplate.PROTECT_SLA:
            return cls(
                makespan=2.0,
                cost=0.1,
                utilization=0.1,
                waiting=0.2,
                switches=0.1,
                delays=1.0,
                preference=0.05
            )
        elif template == PriorityTemplate.COST_MIN:
            return cls(
                makespan=0.5,
                cost=1.0,
                utilization=0.3,
                waiting=0.1,
                switches=0.5,
                delays=0.3,
                preference=0.1
            )
        else:
            return cls()  # 默认权重


class ObjectiveBuilder(ABC):
    """
    目标函数构建器抽象基类
    """
    
    def __init__(self, model: cp_model.CpModel):
        """
        初始化目标函数构建器
        
        Args:
            model: CP-SAT模型实例
        """
        self.model = model
        self.objective_terms: List[Tuple[cp_model.LinearExpr, float]] = []
        self.weights = ObjectiveWeight()
    
    @abstractmethod
    def build_objective(
        self,
        jobs: List[Job],
        resources: List[Resource],
        preparation_tasks: List[PreparationTask],
        variables: Dict[str, Any],
        config: Dict[str, Any]
    ) -> cp_model.LinearExpr:
        """
        构建目标函数
        
        Args:
            jobs: 工卡子项目列表
            resources: 资源列表
            preparation_tasks: 准备任务列表
            variables: 求解器变量
            config: 配置参数
            
        Returns:
            目标函数表达式
        """
        pass
    
    def set_weights(self, weights: ObjectiveWeight) -> None:
        """
        设置目标权重
        
        Args:
            weights: 权重配置
        """
        self.weights = weights
    
    def add_objective_term(self, expression: cp_model.LinearExpr, weight: float) -> None:
        """
        添加目标项
        
        Args:
            expression: 线性表达式
            weight: 权重
        """
        self.objective_terms.append((expression, weight))
    
    def clear_objective_terms(self) -> None:
        """清空目标项"""
        self.objective_terms.clear()


class CPSATObjectiveBuilder(ObjectiveBuilder):
    """
    CP-SAT目标函数构建器
    """
    
    def build_objective(
        self,
        jobs: List[Job],
        resources: List[Resource],
        preparation_tasks: List[PreparationTask],
        variables: Dict[str, Any],
        config: Dict[str, Any]
    ) -> cp_model.LinearExpr:
        """
        构建CP-SAT目标函数
        """
        self.clear_objective_terms()
        
        # 获取变量
        task_starts = variables.get("task_starts", {})
        task_ends = variables.get("task_ends", {})
        resource_assignments = variables.get("resource_assignments", {})
        
        # 构建各个目标项
        if self.weights.makespan > 0:
            makespan_expr = self._build_makespan_objective(
                jobs, preparation_tasks, task_ends, config
            )
            if makespan_expr is not None:
                self.add_objective_term(makespan_expr, self.weights.makespan)
        
        if self.weights.cost > 0:
            cost_expr = self._build_cost_objective(
                jobs, resources, resource_assignments, task_starts, task_ends, config
            )
            if cost_expr is not None:
                self.add_objective_term(cost_expr, self.weights.cost)
        
        if self.weights.waiting > 0:
            waiting_expr = self._build_waiting_objective(
                jobs, preparation_tasks, task_starts, task_ends, config
            )
            if waiting_expr is not None:
                self.add_objective_term(waiting_expr, self.weights.waiting)
        
        if self.weights.switches > 0:
            switches_expr = self._build_switches_objective(
                jobs, preparation_tasks, resources, resource_assignments, config
            )
            if switches_expr is not None:
                self.add_objective_term(switches_expr, self.weights.switches)
        
        if self.weights.delays > 0:
            delays_expr = self._build_delays_objective(
                jobs, preparation_tasks, task_ends, config
            )
            if delays_expr is not None:
                self.add_objective_term(delays_expr, self.weights.delays)
        
        # 组合所有目标项
        if not self.objective_terms:
            raise ConfigurationError("No valid objective terms found")
        
        # 创建加权目标函数
        objective_expr = sum(
            int(weight * 1000) * expr  # 放大权重以避免浮点数问题
            for expr, weight in self.objective_terms
        )
        
        return objective_expr
    
    def _build_makespan_objective(
        self,
        jobs: List[Job],
        preparation_tasks: List[PreparationTask],
        task_ends: Dict[str, cp_model.IntVar],
        config: Dict[str, Any]
    ) -> Optional[cp_model.LinearExpr]:
        """
        构建最小化总完工时间目标
        """
        if not task_ends:
            return None
        
        # 创建makespan变量
        max_end_time = max(
            config.get("time_horizon_hours", 168) * 60,  # 默认一周，转换为分钟
            1440  # 至少一天
        )
        makespan_var = self.model.NewIntVar(0, max_end_time, "makespan")
        
        # makespan >= 所有任务的结束时间
        for task_id, end_var in task_ends.items():
            self.model.Add(makespan_var >= end_var)
        
        return makespan_var
    
    def _build_cost_objective(
        self,
        jobs: List[Job],
        resources: List[Resource],
        resource_assignments: Dict[str, Dict[str, cp_model.BoolVarT]],
        task_starts: Dict[str, cp_model.IntVar],
        task_ends: Dict[str, cp_model.IntVar],
        config: Dict[str, Any]
    ) -> Optional[cp_model.LinearExpr]:
        """
        构建最小化成本目标
        """
        cost_terms = []
        
        # 资源使用成本
        resource_by_id = {r.resource_id: r for r in resources}
        
        for resource_id, assignments in resource_assignments.items():
            resource = resource_by_id.get(resource_id)
            if not resource or not resource.hourly_cost:
                continue
            
            hourly_cost_cents = int(resource.hourly_cost * 100)  # 转换为分
            
            for task_id, assign_var in assignments.items():
                if task_id in task_starts and task_id in task_ends:
                    # 计算任务持续时间（分钟）
                    duration_minutes = task_ends[task_id] - task_starts[task_id]
                    
                    # 成本 = 分配变量 * 持续时间 * 小时成本 / 60
                    cost_term = assign_var * duration_minutes * hourly_cost_cents // 60
                    cost_terms.append(cost_term)
        
        if cost_terms:
            return sum(cost_terms)
        return None
    
    def _build_waiting_objective(
        self,
        jobs: List[Job],
        preparation_tasks: List[PreparationTask],
        task_starts: Dict[str, cp_model.IntVar],
        task_ends: Dict[str, cp_model.IntVar],
        config: Dict[str, Any]
    ) -> Optional[cp_model.LinearExpr]:
        """
        构建最小化等待时间目标
        """
        waiting_terms = []
        
        # 计算任务间的等待时间
        all_tasks = [(job.job_id, job.predecessor_jobs) for job in jobs]
        all_tasks.extend([(task.prep_id, task.dependencies) for task in preparation_tasks])
        
        for task_id, predecessors in all_tasks:
            if not predecessors or task_id not in task_starts:
                continue
            
            for pred_id in predecessors:
                if pred_id in task_ends:
                    # 等待时间 = 当前任务开始时间 - 前置任务结束时间
                    waiting_var = self.model.NewIntVar(0, 10080, f"waiting_{pred_id}_{task_id}")  # 最大一周
                    self.model.Add(waiting_var >= task_starts[task_id] - task_ends[pred_id])
                    waiting_terms.append(waiting_var)
        
        if waiting_terms:
            return sum(waiting_terms)
        return None
    
    def _build_switches_objective(
        self,
        jobs: List[Job],
        preparation_tasks: List[PreparationTask],
        resources: List[Resource],
        resource_assignments: Dict[str, Dict[str, cp_model.BoolVarT]],
        config: Dict[str, Any]
    ) -> Optional[cp_model.LinearExpr]:
        """
        构建最小化切换次数目标
        """
        switch_terms = []
        
        # 按区域分组任务
        tasks_by_area = {}
        
        # 收集工卡子项目的区域信息（从元数据中获取）
        for job in jobs:
            area = job.metadata.get("area", "default")
            if area not in tasks_by_area:
                tasks_by_area[area] = []
            tasks_by_area[area].append(job.job_id)
        
        # 收集准备任务的区域信息
        for task in preparation_tasks:
            area = task.area or "default"
            if area not in tasks_by_area:
                tasks_by_area[area] = []
            tasks_by_area[area].append(task.prep_id)
        
        # 为每个资源计算区域切换成本
        for resource_id, assignments in resource_assignments.items():
            if len(assignments) <= 1:
                continue
            
            # 按区域分组此资源的分配
            assignments_by_area = {}
            for task_id, assign_var in assignments.items():
                # 找到任务所在区域
                task_area = "default"
                for area, area_tasks in tasks_by_area.items():
                    if task_id in area_tasks:
                        task_area = area
                        break
                
                if task_area not in assignments_by_area:
                    assignments_by_area[task_area] = []
                assignments_by_area[task_area].append((task_id, assign_var))
            
            # 如果资源在多个区域有分配，则产生切换成本
            if len(assignments_by_area) > 1:
                # 简化处理：每个额外区域产生固定切换成本
                for area, area_assignments in assignments_by_area.items():
                    if len(area_assignments) > 0:
                        # 区域使用指示变量
                        area_used_var = self.model.new_bool_var(f"area_used_{resource_id}_{area}")
                        
                        # 如果区域中有任何分配，则区域被使用
                        area_assign_vars = [assign_var for _, assign_var in area_assignments]
                        self.model.Add(area_used_var <= sum(area_assign_vars))
                        self.model.Add(area_used_var * len(area_assign_vars) >= sum(area_assign_vars))
                        
                        switch_terms.append(area_used_var * 100)  # 固定切换成本
        
        if switch_terms:
            return sum(switch_terms)
        return None
    
    def _build_delays_objective(
        self,
        jobs: List[Job],
        preparation_tasks: List[PreparationTask],
        task_ends: Dict[str, cp_model.IntVar],
        config: Dict[str, Any]
    ) -> Optional[cp_model.LinearExpr]:
        """
        构建最小化延误目标
        """
        delay_terms = []
        
        # 工卡子项目的延误
        for job in jobs:
            if job.latest_finish and job.job_id in task_ends:
                latest_minutes = self._datetime_to_minutes(job.latest_finish, config)
                delay_var = self.model.NewIntVar(0, 10080, f"delay_{job.job_id}")  # 最大一周延误
                self.model.Add(delay_var >= task_ends[job.job_id] - latest_minutes)
                delay_terms.append(delay_var * 1000)  # 延误惩罚权重
        
        # 准备任务的延误
        for task in preparation_tasks:
            if task.latest_finish and task.prep_id in task_ends:
                latest_minutes = self._datetime_to_minutes(task.latest_finish, config)
                delay_var = self.model.NewIntVar(0, 10080, f"delay_{task.prep_id}")
                self.model.Add(delay_var >= task_ends[task.prep_id] - latest_minutes)
                delay_terms.append(delay_var * 1000)  # 延误惩罚权重
        
        if delay_terms:
            return sum(delay_terms)
        return None
    
    def _datetime_to_minutes(self, dt, config: Dict[str, Any]) -> int:
        """
        将datetime转换为相对于计划开始时间的分钟数
        """
        from datetime import datetime
        
        plan_start = config.get("plan_start_time", datetime.now())
        if isinstance(plan_start, str):
            plan_start = datetime.fromisoformat(plan_start.replace('Z', '+00:00'))
        
        delta = dt - plan_start
        return int(delta.total_seconds() / 60)
