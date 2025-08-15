"""
工具函数库 (Utils Module)

提供智能排程系统的通用工具函数和助手类。
包含时间处理、数据验证、日志记录等基础功能。

主要工具：
- time_utils: 时间处理工具
  - 时间格式转换
  - 时间窗计算
  - 工作日历处理
  
- validators: 数据验证工具
  - 业务规则验证
  - 数据格式验证
  - 约束条件检查
  
- logger: 日志工具
  - 结构化日志记录
  - 性能监控
  - 错误追踪

设计原则：
- 通用性: 提供可复用的工具函数
- 高性能: 优化常用操作的性能
- 易用性: 简洁的API接口
- 可测试: 便于单元测试
"""

# 时间处理工具
from .time_utils import (
    parse_datetime,
    format_datetime,
    parse_duration,
    format_duration,
    calculate_time_window,
    is_working_time,
    get_next_working_time,
    calculate_working_hours,
    get_business_days,
    add_business_days,
)

# 数据验证工具
from .validators import (
    validate_job_dependencies,
    validate_resource_capacity,
    validate_time_constraints,
    validate_qualification_requirements,
    validate_exclusive_resources,
    validate_material_requirements,
    validate_work_package_structure,
    validate_api_request_format,
    validate_id_format,
    validate_datetime_format,
    validate_duration_format,
    validate_business_rules,
)

# 日志记录工具
from .logger import (
    setup_logging,
    get_logger,
    log_performance,
    log_operation,
    StructuredFormatter,
    PerformanceLogger,
    BusinessLogger,
    performance_logger,
    business_logger,
)

__all__ = [
    # 时间处理工具
    "parse_datetime",
    "format_datetime",
    "parse_duration",
    "format_duration",
    "calculate_time_window",
    "is_working_time",
    "get_next_working_time",
    "calculate_working_hours",
    "get_business_days",
    "add_business_days",
    # 数据验证工具
    "validate_job_dependencies",
    "validate_resource_capacity",
    "validate_time_constraints",
    "validate_qualification_requirements",
    "validate_exclusive_resources",
    "validate_material_requirements",
    "validate_work_package_structure",
    "validate_api_request_format",
    "validate_id_format",
    "validate_datetime_format",
    "validate_duration_format",
    "validate_business_rules",
    # 日志记录工具
    "setup_logging",
    "get_logger",
    "log_performance",
    "log_operation",
    "StructuredFormatter",
    "PerformanceLogger",
    "BusinessLogger",
    "performance_logger",
    "business_logger",
]
