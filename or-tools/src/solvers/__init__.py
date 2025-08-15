"""
求解器层 (Solvers Module)

实现基于Google OR-Tools CP-SAT的约束求解引擎。
提供抽象化的求解器接口，支持复杂的调度问题建模和求解。

主要组件：
- CPSATSolver: CP-SAT求解器实现
- ConstraintBuilder: 约束构建器，负责将业务规则转换为求解器约束
- ObjectiveBuilder: 目标函数构建器，定义优化目标
- SolutionParser: 解析器，将求解结果转换为业务对象
- SolverInterface: 求解器抽象接口，便于扩展其他求解器

设计原则：
- 抽象化：通过接口隔离具体求解器实现
- 可扩展：支持添加新的约束类型和目标函数
- 高性能：优化求解性能和内存使用
- 可观测：提供详细的求解状态和性能指标
"""

# 求解器接口和工厂
from .solver_interface import (
    SolverInterface,
    SolverResult,
    SolverConfig,
    SolverFactory,
)

# CP-SAT求解器实现
from .cpsat_solver import CPSATSolver

# 约束构建器
from .constraint_builder import (
    ConstraintBuilder,
    CPSATConstraintBuilder,
)

# 目标函数构建器
from .objective_builder import (
    ObjectiveBuilder,
    CPSATObjectiveBuilder,
    ObjectiveWeight,
    ObjectiveType,
)

# 解析器
from .solution_parser import (
    SolutionParser,
    CPSATSolutionParser,
)

__all__ = [
    # 求解器接口和工厂
    "SolverInterface",
    "SolverResult",
    "SolverConfig",
    "SolverFactory",
    # CP-SAT求解器
    "CPSATSolver",
    # 约束构建器
    "ConstraintBuilder",
    "CPSATConstraintBuilder",
    # 目标函数构建器
    "ObjectiveBuilder",
    "CPSATObjectiveBuilder",
    "ObjectiveWeight",
    "ObjectiveType",
    # 解析器
    "SolutionParser",
    "CPSATSolutionParser",
]
