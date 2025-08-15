"""
配置管理层 (Config Module)

管理智能排程系统的配置参数和策略模板。
提供分层配置管理，支持默认配置、环境配置和运行时配置。

主要组件：
- settings: 应用设置和环境配置
- strategy_templates: 优先级策略模板定义
- solver_config: 求解器参数配置
- constraints_config: 约束参数配置

配置层次：
1. 默认配置: 系统内置的默认参数
2. 环境配置: 通过环境变量或配置文件设置
3. 运行时配置: 通过API动态调整的参数

设计原则：
- 分层管理: 支持多层次配置覆盖
- 类型安全: 配置参数类型验证
- 热更新: 支持运行时配置变更
- 模板化: 预设策略模板快速切换
"""

# 配置设置
from .settings import (
    Settings,
    DatabaseSettings,
    RedisSettings,
    SolverSettings,
    APISettings,
    LoggingSettings,
    SecuritySettings,
    BusinessSettings,
    get_settings,
    settings,
)

__all__ = [
    # 配置设置
    "Settings",
    "DatabaseSettings",
    "RedisSettings",
    "SolverSettings",
    "APISettings",
    "LoggingSettings",
    "SecuritySettings",
    "BusinessSettings",
    "get_settings",
    "settings",
]
