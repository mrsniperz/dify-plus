"""
日志工具 (Logger Utils)

提供结构化日志记录功能，包括性能监控、错误追踪、业务日志等。

主要功能：
- 结构化日志记录
- 性能监控日志
- 错误追踪
- 业务事件日志
- 日志格式化
"""

import json
import time
import logging
import traceback
from typing import Dict, Any, Optional, Union
from datetime import datetime
from functools import wraps
from contextlib import contextmanager

from ..config.settings import get_settings


settings = get_settings()


class StructuredFormatter(logging.Formatter):
    """
    结构化日志格式化器
    
    将日志记录格式化为JSON格式，便于日志分析和监控。
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加额外的字段
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        
        if hasattr(record, 'operation'):
            log_data['operation'] = record.operation
        
        if hasattr(record, 'duration'):
            log_data['duration'] = record.duration
        
        if hasattr(record, 'extra_data'):
            log_data['extra_data'] = record.extra_data
        
        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_data, ensure_ascii=False)


class PerformanceLogger:
    """
    性能日志记录器
    
    专门用于记录性能相关的日志信息。
    """
    
    def __init__(self, logger_name: str = "performance"):
        self.logger = logging.getLogger(logger_name)
    
    def log_operation(
        self,
        operation: str,
        duration: float,
        success: bool = True,
        extra_data: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> None:
        """
        记录操作性能日志
        
        Args:
            operation: 操作名称
            duration: 执行时间（秒）
            success: 是否成功
            extra_data: 额外数据
            request_id: 请求ID
        """
        level = logging.INFO if success else logging.WARNING
        
        # 创建日志记录
        record = self.logger.makeRecord(
            name=self.logger.name,
            level=level,
            fn="",
            lno=0,
            msg=f"Operation {operation} {'completed' if success else 'failed'} in {duration:.3f}s",
            args=(),
            exc_info=None
        )
        
        # 添加额外字段
        record.operation = operation
        record.duration = duration
        record.success = success
        if extra_data:
            record.extra_data = extra_data
        if request_id:
            record.request_id = request_id
        
        self.logger.handle(record)
    
    def log_solver_stats(
        self,
        solver_name: str,
        solve_time: float,
        status: str,
        objective_value: Optional[float] = None,
        num_variables: Optional[int] = None,
        num_constraints: Optional[int] = None,
        request_id: Optional[str] = None
    ) -> None:
        """
        记录求解器统计信息
        
        Args:
            solver_name: 求解器名称
            solve_time: 求解时间
            status: 求解状态
            objective_value: 目标函数值
            num_variables: 变量数量
            num_constraints: 约束数量
            request_id: 请求ID
        """
        extra_data = {
            "solver_name": solver_name,
            "status": status,
            "objective_value": objective_value,
            "num_variables": num_variables,
            "num_constraints": num_constraints
        }
        
        self.log_operation(
            operation="solver_execution",
            duration=solve_time,
            success=status in ["optimal", "feasible"],
            extra_data=extra_data,
            request_id=request_id
        )


class BusinessLogger:
    """
    业务日志记录器
    
    专门用于记录业务相关的日志信息。
    """
    
    def __init__(self, logger_name: str = "business"):
        self.logger = logging.getLogger(logger_name)
    
    def log_schedule_created(
        self,
        plan_id: str,
        work_packages: int,
        tasks: int,
        resources: int,
        makespan_hours: float,
        request_id: Optional[str] = None
    ) -> None:
        """记录排程创建日志"""
        extra_data = {
            "plan_id": plan_id,
            "work_packages": work_packages,
            "tasks": tasks,
            "resources": resources,
            "makespan_hours": makespan_hours
        }
        
        record = self.logger.makeRecord(
            name=self.logger.name,
            level=logging.INFO,
            fn="",
            lno=0,
            msg=f"Schedule created: {plan_id}",
            args=(),
            exc_info=None
        )
        
        record.operation = "schedule_creation"
        record.extra_data = extra_data
        if request_id:
            record.request_id = request_id
        
        self.logger.handle(record)
    
    def log_event_processed(
        self,
        event_id: str,
        event_type: str,
        processing_time: float,
        success: bool,
        affected_tasks: int = 0,
        request_id: Optional[str] = None
    ) -> None:
        """记录事件处理日志"""
        extra_data = {
            "event_id": event_id,
            "event_type": event_type,
            "affected_tasks": affected_tasks
        }
        
        record = self.logger.makeRecord(
            name=self.logger.name,
            level=logging.INFO if success else logging.WARNING,
            fn="",
            lno=0,
            msg=f"Event {event_id} {'processed' if success else 'failed'}",
            args=(),
            exc_info=None
        )
        
        record.operation = "event_processing"
        record.duration = processing_time
        record.extra_data = extra_data
        if request_id:
            record.request_id = request_id
        
        self.logger.handle(record)
    
    def log_gate_check(
        self,
        gate_type: str,
        work_package_id: str,
        passed: bool,
        failed_conditions: Optional[list] = None,
        request_id: Optional[str] = None
    ) -> None:
        """记录门禁检查日志"""
        extra_data = {
            "gate_type": gate_type,
            "work_package_id": work_package_id,
            "passed": passed,
            "failed_conditions": failed_conditions or []
        }
        
        record = self.logger.makeRecord(
            name=self.logger.name,
            level=logging.INFO if passed else logging.WARNING,
            fn="",
            lno=0,
            msg=f"Gate check {gate_type}: {'PASSED' if passed else 'FAILED'}",
            args=(),
            exc_info=None
        )
        
        record.operation = "gate_check"
        record.extra_data = extra_data
        if request_id:
            record.request_id = request_id
        
        self.logger.handle(record)


def setup_logging() -> None:
    """
    设置日志配置
    
    根据配置文件设置日志格式、级别和输出目标。
    """
    # 获取日志配置
    log_config = settings.logging
    
    # 设置根日志级别
    logging.getLogger().setLevel(getattr(logging, log_config.log_level.upper()))
    
    # 创建格式化器
    if log_config.enable_json_logs:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(log_config.log_format)
    
    # 设置控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)
    
    # 设置文件处理器（如果配置了日志文件）
    if log_config.log_file:
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler(
            log_config.log_file,
            maxBytes=log_config.max_log_size,
            backupCount=log_config.backup_count
        )
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        日志记录器实例
    """
    return logging.getLogger(name)


def log_performance(operation: str):
    """
    性能监控装饰器
    
    自动记录函数执行时间。
    
    Args:
        operation: 操作名称
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            result = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                
                # 记录性能日志
                perf_logger = PerformanceLogger()
                perf_logger.log_operation(
                    operation=operation,
                    duration=duration,
                    success=success
                )
        
        return wrapper
    return decorator


@contextmanager
def log_operation(
    operation: str,
    logger: Optional[logging.Logger] = None,
    request_id: Optional[str] = None
):
    """
    操作日志上下文管理器
    
    自动记录操作的开始、结束和执行时间。
    
    Args:
        operation: 操作名称
        logger: 日志记录器
        request_id: 请求ID
    """
    if logger is None:
        logger = get_logger("operation")
    
    start_time = time.time()
    
    # 记录操作开始
    record = logger.makeRecord(
        name=logger.name,
        level=logging.INFO,
        fn="",
        lno=0,
        msg=f"Operation {operation} started",
        args=(),
        exc_info=None
    )
    record.operation = operation
    if request_id:
        record.request_id = request_id
    logger.handle(record)
    
    try:
        yield
        
        # 记录操作成功
        duration = time.time() - start_time
        record = logger.makeRecord(
            name=logger.name,
            level=logging.INFO,
            fn="",
            lno=0,
            msg=f"Operation {operation} completed successfully",
            args=(),
            exc_info=None
        )
        record.operation = operation
        record.duration = duration
        if request_id:
            record.request_id = request_id
        logger.handle(record)
        
    except Exception as e:
        # 记录操作失败
        duration = time.time() - start_time
        record = logger.makeRecord(
            name=logger.name,
            level=logging.ERROR,
            fn="",
            lno=0,
            msg=f"Operation {operation} failed: {str(e)}",
            args=(),
            exc_info=True
        )
        record.operation = operation
        record.duration = duration
        if request_id:
            record.request_id = request_id
        logger.handle(record)
        
        raise


# 全局日志记录器实例
performance_logger = PerformanceLogger()
business_logger = BusinessLogger()
