"""
API接口层 (API Module)

实现智能排程系统的RESTful API接口。
提供标准化的HTTP接口，支持准备阶段排程、事件处理、配置管理等功能。

主要接口：
- prep_api: 准备阶段相关API
  - POST /prep/tasks/plan: 生成准备排程
  - POST /prep/events/apply: 事件驱动重排
  - GET /prep/summary: 准备态汇总
  - POST /prep/handovers/confirm: 交接确认

- config_api: 配置管理API
  - POST /config/priority-template:apply: 策略模板切换
  - POST /config/preemption:settings: 插单护栏设置

设计原则：
- RESTful: 遵循REST设计原则
- 异步支持: 支持异步请求处理
- 错误处理: 统一的错误响应格式
- 数据验证: 完整的请求/响应验证
- 文档生成: 自动生成API文档
"""

# API路由
from .prep_api import prep_router
from .config_api import config_router

# 中间件
from .middleware import (
    RequestLoggingMiddleware,
    PerformanceMonitoringMiddleware,
    setup_middleware,
    setup_cors_middleware,
    create_error_handler,
)

# 主应用
from .main import app, create_app

__all__ = [
    # API路由
    "prep_router",
    "config_router",
    # 中间件
    "RequestLoggingMiddleware",
    "PerformanceMonitoringMiddleware",
    "setup_middleware",
    "setup_cors_middleware",
    "create_error_handler",
    # 主应用
    "app",
    "create_app",
]
