"""
排程服务 (Scheduling Service)

负责生成初始排程计划的核心业务逻辑。
协调求解器、约束构建、目标优化等组件，提供高层次的排程接口。

主要功能：
- 排程计划生成
- 多项目并行排程
- 约束验证和冲突检测
- 排程质量评估
"""

import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

from ..models import (
    Job, Resource, PreparationTask, Schedule, ScheduleMetrics,
    HumanResource, PhysicalResource
)
from ..solvers import SolverFactory, SolverConfig, SolverInterface
from ..core.exceptions import (
    SchedulingError, SolverError, ValidationError, 
    ResourceConflictError, ConstraintViolationError
)
from ..core.constants import PriorityTemplate, SolverStatus


logger = logging.getLogger(__name__)


class SchedulingRequest:
    """排程请求模型"""
    
    def __init__(
        self,
        work_packages: List[Dict[str, Any]],
        assets: List[Dict[str, Any]],
        humans: List[Dict[str, Any]],
        config: Dict[str, Any],
        request_id: Optional[str] = None
    ):
        """
        初始化排程请求
        
        Args:
            work_packages: 工包列表
            assets: 工装设备列表
            humans: 人力资源列表
            config: 配置参数
            request_id: 请求ID
        """
        self.request_id = request_id or str(uuid.uuid4())
        self.work_packages = work_packages
        self.assets = assets
        self.humans = humans
        self.config = config
        self.created_at = datetime.now()


class SchedulingResponse:
    """排程响应模型"""
    
    def __init__(
        self,
        plan_id: str,
        schedule: Optional[Schedule] = None,
        gates: Optional[List[Dict[str, Any]]] = None,
        preparation_tasks: Optional[List[Dict[str, Any]]] = None,
        makespan: Optional[str] = None,
        request_id: Optional[str] = None,
        error: Optional[Dict[str, Any]] = None
    ):
        """
        初始化排程响应
        
        Args:
            plan_id: 计划ID
            schedule: 排程计划
            gates: 门禁状态
            preparation_tasks: 准备任务
            makespan: 总完工时间
            request_id: 请求ID
            error: 错误信息
        """
        self.plan_id = plan_id
        self.schedule = schedule
        self.gates = gates or []
        self.preparation_tasks = preparation_tasks or []
        self.makespan = makespan
        self.request_id = request_id
        self.error = error
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "plan_id": self.plan_id,
            "request_id": self.request_id,
            "created_at": self.created_at.isoformat(),
        }
        
        if self.error:
            result["error"] = self.error
        else:
            result.update({
                "gates": self.gates,
                "preparation_tasks": self.preparation_tasks,
                "makespan": self.makespan,
            })
            
            if self.schedule:
                result["schedule"] = {
                    "task_intervals": [
                        {
                            "task_id": interval.task_id,
                            "task_type": interval.task_type,
                            "start": interval.start_time.isoformat(),
                            "end": interval.end_time.isoformat(),
                            "duration_hours": interval.duration_hours,
                            "assigned_resources": interval.assigned_resources,
                            "assigned_personnel": interval.assigned_personnel,
                        }
                        for interval in self.schedule.task_intervals
                    ],
                    "metrics": {
                        "makespan_hours": self.schedule.metrics.makespan_hours,
                        "total_duration_hours": self.schedule.metrics.total_duration_hours,
                        "average_utilization": self.schedule.metrics.average_utilization,
                        "solve_time_seconds": self.schedule.metrics.solve_time_seconds,
                        "solver_status": self.schedule.metrics.solver_status,
                    }
                }
        
        return result


class SchedulingService:
    """
    排程服务
    
    提供排程计划生成的核心业务逻辑。
    """
    
    def __init__(
        self,
        solver_name: str = "cpsat",
        default_config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化排程服务
        
        Args:
            solver_name: 求解器名称
            default_config: 默认配置
        """
        self.solver_name = solver_name
        self.default_config = default_config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def create_schedule(self, request: SchedulingRequest) -> SchedulingResponse:
        """
        创建排程计划
        
        Args:
            request: 排程请求
            
        Returns:
            排程响应
        """
        plan_id = f"PLAN-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{request.request_id[:8]}"
        
        try:
            self.logger.info(f"Starting schedule creation for plan {plan_id}")
            
            # 验证请求
            self._validate_request(request)
            
            # 解析输入数据
            jobs, resources, preparation_tasks = self._parse_request_data(request)
            
            # 验证业务规则
            self._validate_business_rules(jobs, resources, preparation_tasks)
            
            # 创建求解器
            solver = self._create_solver(request.config)
            
            # 执行排程
            schedule = self._execute_scheduling(
                solver, jobs, resources, preparation_tasks, request.config
            )
            
            # 生成门禁状态
            gates = self._generate_gate_status(preparation_tasks, schedule)
            
            # 生成准备任务列表
            prep_tasks = self._generate_preparation_tasks(preparation_tasks, schedule)
            
            # 计算makespan
            makespan = self._format_makespan(schedule.metrics.makespan_hours)
            
            self.logger.info(f"Successfully created schedule {plan_id}")
            
            return SchedulingResponse(
                plan_id=plan_id,
                schedule=schedule,
                gates=gates,
                preparation_tasks=prep_tasks,
                makespan=makespan,
                request_id=request.request_id
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create schedule {plan_id}: {e}")
            
            error_info = {
                "code": type(e).__name__,
                "message": str(e),
                "details": getattr(e, 'details', {}) if hasattr(e, 'details') else {}
            }
            
            return SchedulingResponse(
                plan_id=plan_id,
                request_id=request.request_id,
                error=error_info
            )
    
    def _validate_request(self, request: SchedulingRequest) -> None:
        """
        验证排程请求
        """
        if not request.work_packages:
            raise ValidationError("No work packages provided")
        
        if not request.assets and not request.humans:
            raise ValidationError("No resources provided")
        
        # 验证配置参数
        config = request.config
        if "prep_window_days" in config:
            if not isinstance(config["prep_window_days"], (int, float)) or config["prep_window_days"] <= 0:
                raise ValidationError("prep_window_days must be a positive number")
        
        if "objective_template" in config:
            if config["objective_template"] not in [t.value for t in PriorityTemplate]:
                raise ValidationError(f"Invalid objective_template: {config['objective_template']}")
    
    def _parse_request_data(
        self, 
        request: SchedulingRequest
    ) -> Tuple[List[Job], List[Resource], List[PreparationTask]]:
        """
        解析请求数据为内部模型
        """
        jobs = []
        resources = []
        preparation_tasks = []
        
        # 解析工包中的工卡子项目
        for wp in request.work_packages:
            work_package_id = wp["work_package_id"]
            engine_id = wp["engine_id"]
            
            # 检查是否有详细的任务信息
            job_details = wp.get("job_details", [])
            if job_details:
                # 使用详细的任务信息
                for job_data in job_details:
                    # 转换资源需求格式
                    required_resources = []
                    for resource_name in job_data.get('required_resources', []):
                        if isinstance(resource_name, str):
                            # 将字符串转换为ResourceRequirement对象
                            from ..models import ResourceRequirement
                            required_resources.append(ResourceRequirement(
                                resource_id=resource_name,
                                quantity=1,
                                is_critical=False
                            ))
                        else:
                            # 如果已经是正确格式，直接使用
                            required_resources.append(resource_name)

                    job = Job(
                        job_id=job_data.get('job_id'),
                        work_card_id=work_package_id,
                        engine_id=engine_id,
                        name=job_data.get('name', f"Job {job_data.get('job_id')}"),
                        base_duration_hours=job_data.get('base_duration_hours', 4.0),
                        required_resources=required_resources,
                        required_qualifications=job_data.get('required_qualifications', []),
                        predecessor_jobs=job_data.get('predecessor_jobs', [])
                    )
                    jobs.append(job)
            else:
                # 简化实现：创建示例Job
                for i, job_id in enumerate(wp.get("jobs", [])):
                    job = Job(
                        job_id=job_id,
                        work_card_id=work_package_id,
                        engine_id=engine_id,
                        name=f"Job {job_id}",
                        base_duration_hours=4.0,  # 默认4小时
                        required_resources=[],
                        required_qualifications=[]
                    )
                    jobs.append(job)
        
        # 解析工装设备
        for asset_data in request.assets:
            resource = PhysicalResource(
                resource_id=asset_data["asset_id"],
                name=asset_data.get("name", asset_data["asset_id"]),
                is_exclusive=asset_data.get("is_critical", False),
                exclusive_group=asset_data.get("exclusive_group")
            )
            resources.append(resource)
        
        # 解析人力资源
        for human_data in request.humans:
            resource = HumanResource(
                resource_id=human_data["employee_id"],
                employee_id=human_data["employee_id"],
                name=human_data.get("name", human_data["employee_id"]),
                qualifications=human_data.get("qualifications", [])
            )
            resources.append(resource)
        
        # 解析准备任务（从工包的materials等信息生成）
        for wp in request.work_packages:
            for material in wp.get("materials", []):
                task = PreparationTask(
                    prep_id=f"PREP-{material['material_id']}",
                    engine_id=wp["engine_id"],
                    work_package_id=wp["work_package_id"],
                    name=f"Prepare material {material['material_id']}",
                    type="material_kitting",
                    duration_hours=1.0,
                    is_gate=material.get("must_kit", False)
                )
                preparation_tasks.append(task)
        
        return jobs, resources, preparation_tasks
    
    def _validate_business_rules(
        self,
        jobs: List[Job],
        resources: List[Resource],
        preparation_tasks: List[PreparationTask]
    ) -> None:
        """
        验证业务规则
        """
        # 检查资源冲突
        exclusive_resources = {}
        for resource in resources:
            if isinstance(resource, PhysicalResource) and resource.is_exclusive:
                group = resource.exclusive_group or resource.resource_id
                if group in exclusive_resources:
                    raise ResourceConflictError(
                        f"Multiple exclusive resources in group {group}",
                        conflicting_resources=[exclusive_resources[group], resource.resource_id]
                    )
                exclusive_resources[group] = resource.resource_id
        
        # 检查任务依赖的循环引用
        self._check_circular_dependencies(jobs, preparation_tasks)
    
    def _check_circular_dependencies(
        self,
        jobs: List[Job],
        preparation_tasks: List[PreparationTask]
    ) -> None:
        """
        检查任务依赖的循环引用
        """
        # 构建依赖图
        dependencies = {}
        
        for job in jobs:
            dependencies[job.job_id] = job.predecessor_jobs
        
        for task in preparation_tasks:
            dependencies[task.prep_id] = task.dependencies
        
        # 使用DFS检测循环
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            if node in rec_stack:
                return True
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in dependencies.get(node, []):
                if has_cycle(neighbor):
                    return True
            
            rec_stack.remove(node)
            return False
        
        for task_id in dependencies:
            if task_id not in visited:
                if has_cycle(task_id):
                    raise ConstraintViolationError(
                        "Circular dependency detected in task dependencies",
                        violated_constraints=["no_circular_dependencies"]
                    )
    
    def _create_solver(self, config: Dict[str, Any]) -> SolverInterface:
        """
        创建求解器实例
        """
        # 合并配置
        solver_config_dict = {**self.default_config, **config.get("solver", {})}
        
        # 创建求解器配置
        solver_config = SolverConfig(
            time_limit_seconds=solver_config_dict.get("time_limit_seconds", 300.0),
            num_search_workers=solver_config_dict.get("num_search_workers", 1),
            log_search_progress=solver_config_dict.get("log_search_progress", False),
            random_seed=solver_config_dict.get("random_seed"),
            optimization_parameters=solver_config_dict.get("optimization_parameters", {})
        )
        
        # 创建求解器
        solver = SolverFactory.create_solver(self.solver_name, solver_config)
        solver.initialize()
        
        return solver
    
    def _execute_scheduling(
        self,
        solver: SolverInterface,
        jobs: List[Job],
        resources: List[Resource],
        preparation_tasks: List[PreparationTask],
        config: Dict[str, Any]
    ) -> Schedule:
        """
        执行排程求解
        """
        try:
            # 添加数据到求解器
            solver.add_jobs(jobs)
            solver.add_resources(resources)
            solver.add_preparation_tasks(preparation_tasks)
            
            # 设置约束
            constraints_config = {
                "plan_start_time": datetime.now(),
                "time_horizon_hours": config.get("prep_window_days", 2) * 24,
                "freeze_inprogress": config.get("freeze_inprogress", True)
            }
            solver.add_constraints(constraints_config)
            
            # 设置目标函数
            objective_config = {
                "priority_template": config.get("objective_template", "balanced"),
                "weights": config.get("weights", {}),
                "plan_id": f"PLAN-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                "plan_name": config.get("plan_name"),
                "plan_description": config.get("plan_description"),
                "metadata": config.get("metadata", {})
            }
            solver.set_objective(objective_config)
            
            # 执行求解
            result = solver.solve()
            
            if not result.is_successful():
                raise SolverError(
                    f"Solver failed with status {result.status}",
                    solver_status=result.status.value,
                    solve_time=result.solve_time_seconds
                )
            
            # 获取排程计划
            schedule = solver.get_schedule()
            if not schedule:
                raise SolverError("Failed to generate schedule from solver result")
            
            return schedule
            
        finally:
            solver.clear()
    
    def _generate_gate_status(
        self,
        preparation_tasks: List[PreparationTask],
        schedule: Schedule
    ) -> List[Dict[str, Any]]:
        """
        生成门禁状态
        """
        gates = []
        
        # 统计门禁任务
        gate_tasks = [task for task in preparation_tasks if task.is_gate]
        
        # 生成门禁状态
        gates.append({
            "gate": "critical_tools_ready",
            "passed": len([t for t in gate_tasks if t.type == "tool_allocation"]) == 0,
            "expected_time": datetime.now().isoformat() + "Z"
        })
        
        gates.append({
            "gate": "materials_ready", 
            "passed": len([t for t in gate_tasks if t.type == "material_kitting"]) == 0,
            "expected_time": datetime.now().isoformat() + "Z"
        })
        
        return gates
    
    def _generate_preparation_tasks(
        self,
        preparation_tasks: List[PreparationTask],
        schedule: Schedule
    ) -> List[Dict[str, Any]]:
        """
        生成准备任务列表
        """
        tasks = []
        
        for task in preparation_tasks:
            # 从排程中找到对应的时间间隔
            interval = schedule.get_task_interval(task.prep_id)
            
            task_dict = {
                "prep_id": task.prep_id,
                "type": task.type,
                "is_gate": task.is_gate,
                "engine_id": task.engine_id,
                "work_package_id": task.work_package_id,
                "required_assets": task.required_assets,
                "required_roles": task.required_roles,
                "area": task.area
            }
            
            if interval:
                task_dict.update({
                    "interval": {
                        "start": interval.start_time.isoformat() + "Z",
                        "end": interval.end_time.isoformat() + "Z"
                    }
                })
            
            tasks.append(task_dict)
        
        return tasks
    
    def _format_makespan(self, makespan_hours: float) -> str:
        """
        格式化总完工时间
        """
        hours = int(makespan_hours)
        minutes = int((makespan_hours - hours) * 60)
        return f"PT{hours}H{minutes}M" if minutes > 0 else f"PT{hours}H"
