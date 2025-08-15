"""
CP-SAT求解器 (CP-SAT Solver)

基于Google OR-Tools CP-SAT的具体求解器实现。
提供完整的约束求解功能，支持复杂的调度问题建模和求解。

主要功能：
- 任务和资源建模
- 约束条件构建
- 目标函数优化
- 求解结果解析
"""

import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from ortools.sat.python import cp_model

from .solver_interface import SolverInterface, SolverResult, SolverConfig
from .constraint_builder import CPSATConstraintBuilder
from .objective_builder import CPSATObjectiveBuilder, ObjectiveWeight
from .solution_parser import CPSATSolutionParser

from ..models import Job, Resource, PreparationTask, Schedule
from ..core.exceptions import SolverError
from ..core.constants import SolverStatus, PriorityTemplate


class CPSATSolver(SolverInterface):
    """
    CP-SAT求解器实现
    
    基于Google OR-Tools CP-SAT求解器的智能排程求解器。
    """
    
    def __init__(self, config: Optional[SolverConfig] = None):
        """
        初始化CP-SAT求解器
        
        Args:
            config: 求解器配置
        """
        super().__init__(config)
        
        # CP-SAT模型和求解器
        self.model: Optional[cp_model.CpModel] = None
        self.solver: Optional[cp_model.CpSolver] = None
        
        # 组件
        self.constraint_builder: Optional[CPSATConstraintBuilder] = None
        self.objective_builder: Optional[CPSATObjectiveBuilder] = None
        self.solution_parser: Optional[CPSATSolutionParser] = None
        
        # 数据存储
        self.jobs: List[Job] = []
        self.resources: List[Resource] = []
        self.preparation_tasks: List[PreparationTask] = []
        self.constraints_config: Dict[str, Any] = {}
        self.objective_config: Dict[str, Any] = {}
        
        # 求解结果
        self.last_result: Optional[SolverResult] = None
        self.variables: Dict[str, Any] = {}
    
    def initialize(self) -> None:
        """
        初始化求解器
        """
        try:
            # 创建CP-SAT模型
            self.model = cp_model.CpModel()
            
            # 创建求解器
            self.solver = cp_model.CpSolver()
            
            # 设置求解器参数
            self._configure_solver()
            
            # 创建组件
            self.constraint_builder = CPSATConstraintBuilder(self.model)
            self.objective_builder = CPSATObjectiveBuilder(self.model)
            self.solution_parser = CPSATSolutionParser()
            
            self._is_initialized = True
            
        except Exception as e:
            raise SolverError(f"Failed to initialize CP-SAT solver: {e}")
    
    def add_jobs(self, jobs: List[Job]) -> None:
        """
        添加工卡子项目
        """
        if not self._is_initialized:
            raise SolverError("Solver not initialized")
        
        self.jobs.extend(jobs)
    
    def add_resources(self, resources: List[Resource]) -> None:
        """
        添加资源
        """
        if not self._is_initialized:
            raise SolverError("Solver not initialized")
        
        self.resources.extend(resources)
    
    def add_preparation_tasks(self, tasks: List[PreparationTask]) -> None:
        """
        添加准备任务
        """
        if not self._is_initialized:
            raise SolverError("Solver not initialized")
        
        self.preparation_tasks.extend(tasks)
    
    def add_constraints(self, constraints: Dict[str, Any]) -> None:
        """
        添加约束条件
        """
        if not self._is_initialized:
            raise SolverError("Solver not initialized")
        
        self.constraints_config.update(constraints)
    
    def set_objective(self, objective_config: Dict[str, Any]) -> None:
        """
        设置目标函数
        """
        if not self._is_initialized:
            raise SolverError("Solver not initialized")
        
        self.objective_config = objective_config
    
    def solve(self) -> SolverResult:
        """
        执行求解
        """
        if not self._is_initialized:
            raise SolverError("Solver not initialized")
        
        if not self.model or not self.solver:
            raise SolverError("Model or solver not properly initialized")
        
        try:
            # 验证输入
            is_valid, errors = self.validate_input()
            if not is_valid:
                raise SolverError(f"Input validation failed: {'; '.join(errors)}")
            
            # 构建约束
            self._build_constraints()
            
            # 构建目标函数
            self._build_objective()
            
            # 执行求解
            start_time = time.time()
            status = self.solver.Solve(self.model)
            solve_time = time.time() - start_time
            
            # 转换求解状态
            solver_status = self._convert_status(status)
            
            # 获取目标值
            objective_value = None
            if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
                objective_value = self.solver.ObjectiveValue()
            
            # 获取统计信息
            statistics = {
                "num_branches": self.solver.NumBranches(),
                "num_conflicts": self.solver.NumConflicts(),
                "wall_time": self.solver.WallTime(),
                "user_time": self.solver.UserTime()
            }
            
            # 创建求解结果
            self.last_result = SolverResult(
                status=solver_status,
                objective_value=objective_value,
                solve_time_seconds=solve_time,
                solution=self._extract_solution() if status in [cp_model.OPTIMAL, cp_model.FEASIBLE] else None,
                statistics=statistics
            )
            
            return self.last_result
            
        except Exception as e:
            error_msg = f"Solve failed: {e}"
            self.last_result = SolverResult(
                status=SolverStatus.ABNORMAL,
                solve_time_seconds=0.0,
                error_message=error_msg
            )
            raise SolverError(error_msg)
    
    def get_schedule(self) -> Optional[Schedule]:
        """
        获取排程计划
        """
        if not self.last_result or not self.last_result.is_successful():
            return None
        
        if not self.solution_parser:
            raise SolverError("Solution parser not initialized")
        
        try:
            # 准备配置
            config = {
                "plan_start_time": self.constraints_config.get("plan_start_time", datetime.now()),
                "time_horizon_hours": self.constraints_config.get("time_horizon_hours", 168),
                "plan_id": self.objective_config.get("plan_id"),
                "plan_name": self.objective_config.get("plan_name"),
                "plan_description": self.objective_config.get("plan_description"),
                "solver_config": self.config.to_dict(),
                "metadata": self.objective_config.get("metadata", {}),
                "cp_solver": self.solver  # 传入CP-SAT求解器对象
            }
            
            # 解析排程计划
            schedule = self.solution_parser.parse_solution(
                self.last_result,
                self.jobs,
                self.resources,
                self.preparation_tasks,
                self.variables,
                config
            )
            
            return schedule
            
        except Exception as e:
            raise SolverError(f"Failed to parse schedule: {e}")
    
    def clear(self) -> None:
        """
        清空求解器状态
        """
        self.jobs.clear()
        self.resources.clear()
        self.preparation_tasks.clear()
        self.constraints_config.clear()
        self.objective_config.clear()
        self.variables.clear()
        self.last_result = None
        
        if self._is_initialized:
            self.model = cp_model.CpModel()
            self.constraint_builder = CPSATConstraintBuilder(self.model)
            self.objective_builder = CPSATObjectiveBuilder(self.model)
    
    def validate_input(self) -> tuple[bool, List[str]]:
        """
        验证输入数据
        """
        is_valid, errors = super().validate_input()
        
        # 检查是否有任务
        if not self.jobs and not self.preparation_tasks:
            errors.append("No jobs or preparation tasks provided")
        
        # 检查是否有资源
        if not self.resources:
            errors.append("No resources provided")
        
        # 检查任务依赖的有效性
        all_task_ids = set(job.job_id for job in self.jobs)
        all_task_ids.update(task.prep_id for task in self.preparation_tasks)
        
        for job in self.jobs:
            for pred_id in job.predecessor_jobs:
                if pred_id not in all_task_ids:
                    errors.append(f"Job {job.job_id} depends on unknown task {pred_id}")
        
        for task in self.preparation_tasks:
            for dep_id in task.dependencies:
                if dep_id not in all_task_ids:
                    errors.append(f"Preparation task {task.prep_id} depends on unknown task {dep_id}")
        
        return len(errors) == 0, errors
    
    def _configure_solver(self) -> None:
        """
        配置求解器参数
        """
        if not self.solver:
            return
        
        # 设置时间限制
        self.solver.parameters.max_time_in_seconds = self.config.time_limit_seconds
        
        # 设置搜索工作线程数
        self.solver.parameters.num_search_workers = self.config.num_search_workers
        
        # 设置日志级别
        if self.config.log_search_progress:
            self.solver.parameters.log_search_progress = True
        
        # 设置随机种子
        if self.config.random_seed is not None:
            self.solver.parameters.random_seed = self.config.random_seed
        
        # 应用其他优化参数
        for param, value in self.config.optimization_parameters.items():
            if hasattr(self.solver.parameters, param):
                setattr(self.solver.parameters, param, value)
    
    def _build_constraints(self) -> None:
        """
        构建约束条件
        """
        if not self.constraint_builder:
            raise SolverError("Constraint builder not initialized")
        
        # 构建约束并获取变量
        self.variables = self.constraint_builder.build_constraints(
            self.jobs,
            self.resources,
            self.preparation_tasks,
            self.constraints_config
        )
    
    def _build_objective(self) -> None:
        """
        构建目标函数
        """
        if not self.objective_builder:
            raise SolverError("Objective builder not initialized")
        
        # 设置目标权重
        template = self.objective_config.get("priority_template", PriorityTemplate.BALANCED)
        weights = ObjectiveWeight.from_template(template)
        
        # 应用自定义权重覆盖
        custom_weights = self.objective_config.get("weights", {})
        for attr, value in custom_weights.items():
            if hasattr(weights, attr):
                setattr(weights, attr, value)
        
        self.objective_builder.set_weights(weights)
        
        # 构建目标函数
        objective_expr = self.objective_builder.build_objective(
            self.jobs,
            self.resources,
            self.preparation_tasks,
            self.variables,
            self.constraints_config
        )
        
        # 设置目标函数（最小化）
        self.model.Minimize(objective_expr)
    
    def _convert_status(self, cp_status: int) -> SolverStatus:
        """
        转换CP-SAT状态到系统状态
        """
        status_mapping = {
            cp_model.OPTIMAL: SolverStatus.OPTIMAL,
            cp_model.FEASIBLE: SolverStatus.FEASIBLE,
            cp_model.INFEASIBLE: SolverStatus.INFEASIBLE,
            cp_model.MODEL_INVALID: SolverStatus.MODEL_INVALID,
        }
        
        return status_mapping.get(cp_status, SolverStatus.UNKNOWN)
    
    def _extract_solution(self) -> Dict[str, Any]:
        """
        提取求解结果数据
        """
        solution = {}
        
        # 提取任务开始时间
        task_starts = self.variables.get("task_starts", {})
        for task_id, start_var in task_starts.items():
            solution[f"start_{task_id}"] = self.solver.Value(start_var)
        
        # 提取任务结束时间
        task_ends = self.variables.get("task_ends", {})
        for task_id, end_var in task_ends.items():
            solution[f"end_{task_id}"] = self.solver.Value(end_var)
        
        # 提取资源分配
        resource_assignments = self.variables.get("resource_assignments", {})
        for resource_id, assignments in resource_assignments.items():
            for task_id, assign_var in assignments.items():
                solution[f"assign_{resource_id}_{task_id}"] = self.solver.Value(assign_var)
        
        return solution


# 注册CP-SAT求解器到工厂
from .solver_interface import SolverFactory
SolverFactory.register_solver("cpsat", CPSATSolver)
