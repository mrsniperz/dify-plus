"""
求解器接口 (Solver Interface)

定义求解器的抽象接口，提供统一的求解器API。
这个接口使得系统可以支持多种不同的求解器实现，便于扩展和测试。

接口设计原则：
- 抽象化：隐藏具体求解器的实现细节
- 可扩展：支持添加新的求解器类型
- 类型安全：完整的类型注解
- 异常处理：统一的错误处理机制
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from ..models import (
    Job, Resource, PreparationTask, Schedule, ScheduleMetrics
)
from ..core.exceptions import SolverError
from ..core.constants import SolverStatus


class SolverResult:
    """
    求解器结果类
    
    封装求解器的输出结果，包括求解状态、目标值、解决方案等。
    """
    
    def __init__(
        self,
        status: SolverStatus,
        objective_value: Optional[float] = None,
        solve_time_seconds: float = 0.0,
        solution: Optional[Dict[str, Any]] = None,
        statistics: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ):
        """
        初始化求解器结果
        
        Args:
            status: 求解状态
            objective_value: 目标函数值
            solve_time_seconds: 求解时间（秒）
            solution: 解决方案数据
            statistics: 求解统计信息
            error_message: 错误信息
        """
        self.status = status
        self.objective_value = objective_value
        self.solve_time_seconds = solve_time_seconds
        self.solution = solution or {}
        self.statistics = statistics or {}
        self.error_message = error_message
    
    def is_successful(self) -> bool:
        """检查求解是否成功"""
        return self.status in [SolverStatus.OPTIMAL, SolverStatus.FEASIBLE]
    
    def is_optimal(self) -> bool:
        """检查是否找到最优解"""
        return self.status == SolverStatus.OPTIMAL
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "status": self.status.value,
            "objective_value": self.objective_value,
            "solve_time_seconds": self.solve_time_seconds,
            "solution": self.solution,
            "statistics": self.statistics,
            "error_message": self.error_message,
            "is_successful": self.is_successful(),
            "is_optimal": self.is_optimal()
        }


class SolverConfig:
    """
    求解器配置类
    
    定义求解器的各种参数和选项。
    """
    
    def __init__(
        self,
        time_limit_seconds: float = 300.0,
        num_search_workers: int = 1,
        log_search_progress: bool = False,
        random_seed: Optional[int] = None,
        optimization_parameters: Optional[Dict[str, Any]] = None
    ):
        """
        初始化求解器配置
        
        Args:
            time_limit_seconds: 求解时间限制（秒）
            num_search_workers: 搜索工作线程数
            log_search_progress: 是否记录搜索进度
            random_seed: 随机种子
            optimization_parameters: 优化参数
        """
        self.time_limit_seconds = time_limit_seconds
        self.num_search_workers = num_search_workers
        self.log_search_progress = log_search_progress
        self.random_seed = random_seed
        self.optimization_parameters = optimization_parameters or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "time_limit_seconds": self.time_limit_seconds,
            "num_search_workers": self.num_search_workers,
            "log_search_progress": self.log_search_progress,
            "random_seed": self.random_seed,
            "optimization_parameters": self.optimization_parameters
        }


class SolverInterface(ABC):
    """
    求解器抽象接口
    
    定义所有求解器必须实现的方法。
    """
    
    def __init__(self, config: Optional[SolverConfig] = None):
        """
        初始化求解器
        
        Args:
            config: 求解器配置
        """
        self.config = config or SolverConfig()
        self._is_initialized = False
    
    @abstractmethod
    def initialize(self) -> None:
        """
        初始化求解器
        
        在使用求解器之前必须调用此方法。
        
        Raises:
            SolverError: 初始化失败时抛出
        """
        pass
    
    @abstractmethod
    def add_jobs(self, jobs: List[Job]) -> None:
        """
        添加工卡子项目
        
        Args:
            jobs: 工卡子项目列表
            
        Raises:
            SolverError: 添加失败时抛出
        """
        pass
    
    @abstractmethod
    def add_resources(self, resources: List[Resource]) -> None:
        """
        添加资源
        
        Args:
            resources: 资源列表
            
        Raises:
            SolverError: 添加失败时抛出
        """
        pass
    
    @abstractmethod
    def add_preparation_tasks(self, tasks: List[PreparationTask]) -> None:
        """
        添加准备任务
        
        Args:
            tasks: 准备任务列表
            
        Raises:
            SolverError: 添加失败时抛出
        """
        pass
    
    @abstractmethod
    def add_constraints(self, constraints: Dict[str, Any]) -> None:
        """
        添加约束条件
        
        Args:
            constraints: 约束条件字典
            
        Raises:
            SolverError: 添加失败时抛出
        """
        pass
    
    @abstractmethod
    def set_objective(self, objective_config: Dict[str, Any]) -> None:
        """
        设置目标函数
        
        Args:
            objective_config: 目标函数配置
            
        Raises:
            SolverError: 设置失败时抛出
        """
        pass
    
    @abstractmethod
    def solve(self) -> SolverResult:
        """
        执行求解
        
        Returns:
            求解结果
            
        Raises:
            SolverError: 求解失败时抛出
        """
        pass
    
    @abstractmethod
    def get_schedule(self) -> Optional[Schedule]:
        """
        获取排程计划
        
        Returns:
            排程计划，如果没有有效解则返回None
            
        Raises:
            SolverError: 获取失败时抛出
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """
        清空求解器状态
        
        清除所有已添加的任务、资源、约束等，重置求解器到初始状态。
        """
        pass
    
    def validate_input(self) -> Tuple[bool, List[str]]:
        """
        验证输入数据
        
        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []
        
        # 子类可以重写此方法添加特定的验证逻辑
        if not self._is_initialized:
            errors.append("Solver not initialized")
        
        return len(errors) == 0, errors
    
    def get_solver_info(self) -> Dict[str, Any]:
        """
        获取求解器信息
        
        Returns:
            求解器信息字典
        """
        return {
            "solver_type": self.__class__.__name__,
            "config": self.config.to_dict(),
            "is_initialized": self._is_initialized
        }
    
    def update_config(self, new_config: SolverConfig) -> None:
        """
        更新求解器配置
        
        Args:
            new_config: 新的配置
        """
        self.config = new_config
    
    def __enter__(self):
        """上下文管理器入口"""
        if not self._is_initialized:
            self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.clear()


class SolverFactory:
    """
    求解器工厂类
    
    负责创建和管理不同类型的求解器实例。
    """
    
    _solvers: Dict[str, type] = {}
    
    @classmethod
    def register_solver(cls, name: str, solver_class: type) -> None:
        """
        注册求解器类型
        
        Args:
            name: 求解器名称
            solver_class: 求解器类
        """
        if not issubclass(solver_class, SolverInterface):
            raise ValueError(f"Solver class {solver_class} must inherit from SolverInterface")
        cls._solvers[name] = solver_class
    
    @classmethod
    def create_solver(cls, name: str, config: Optional[SolverConfig] = None) -> SolverInterface:
        """
        创建求解器实例
        
        Args:
            name: 求解器名称
            config: 求解器配置
            
        Returns:
            求解器实例
            
        Raises:
            ValueError: 未知的求解器类型
        """
        if name not in cls._solvers:
            raise ValueError(f"Unknown solver type: {name}")
        
        solver_class = cls._solvers[name]
        return solver_class(config)
    
    @classmethod
    def list_solvers(cls) -> List[str]:
        """
        列出所有已注册的求解器类型
        
        Returns:
            求解器名称列表
        """
        return list(cls._solvers.keys())
    
    @classmethod
    def get_default_solver(cls, config: Optional[SolverConfig] = None) -> SolverInterface:
        """
        获取默认求解器
        
        Args:
            config: 求解器配置
            
        Returns:
            默认求解器实例
        """
        # 默认使用CP-SAT求解器
        return cls.create_solver("cpsat", config)
