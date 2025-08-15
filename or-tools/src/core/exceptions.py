"""
异常定义模块 (Exceptions Module)

定义智能排程系统的自定义异常类层次结构。
提供详细的错误信息和调试支持，便于问题定位和处理。

异常层次结构：
- SchedulingError (基础异常)
  - SolverError (求解器相关异常)
  - ValidationError (数据验证异常)
  - ResourceConflictError (资源冲突异常)
  - ConstraintViolationError (约束违反异常)
  - ConfigurationError (配置错误异常)
  - GateError (门禁检查异常)
  - EventProcessingError (事件处理异常)
"""

from typing import Any, Dict, List, Optional


class SchedulingError(Exception):
    """
    智能排程系统基础异常类
    
    所有系统自定义异常的基类，提供统一的错误处理接口。
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """
        初始化异常
        
        Args:
            message: 错误消息
            error_code: 错误代码，用于API响应
            details: 详细错误信息字典
            cause: 引起此异常的原始异常
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__.upper()
        self.details = details or {}
        self.cause = cause
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，便于API响应"""
        result = {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "type": self.__class__.__name__,
            }
        }
        
        if self.details:
            result["error"]["details"] = self.details
            
        if self.cause:
            result["error"]["cause"] = str(self.cause)
            
        return result


class SolverError(SchedulingError):
    """
    求解器相关异常
    
    当OR-Tools求解器遇到问题时抛出，如求解失败、超时、内存不足等。
    """
    
    def __init__(
        self,
        message: str,
        solver_status: Optional[str] = None,
        solve_time: Optional[float] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if solver_status:
            details["solver_status"] = solver_status
        if solve_time is not None:
            details["solve_time_seconds"] = solve_time
            
        super().__init__(
            message=message,
            error_code="SOLVER_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


class ValidationError(SchedulingError):
    """
    数据验证异常
    
    当输入数据不符合预期格式或业务规则时抛出。
    """
    
    def __init__(
        self,
        message: str,
        field_errors: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if field_errors:
            details["field_errors"] = field_errors
            
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


class ResourceConflictError(SchedulingError):
    """
    资源冲突异常
    
    当资源分配出现冲突时抛出，如同一时间段多个任务争用同一资源。
    """
    
    def __init__(
        self,
        message: str,
        conflicting_resources: Optional[List[str]] = None,
        conflicting_tasks: Optional[List[str]] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if conflicting_resources:
            details["conflicting_resources"] = conflicting_resources
        if conflicting_tasks:
            details["conflicting_tasks"] = conflicting_tasks
            
        super().__init__(
            message=message,
            error_code="RESOURCE_CONFLICT",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


class ConstraintViolationError(SchedulingError):
    """
    约束违反异常
    
    当排程结果违反业务约束时抛出。
    """
    
    def __init__(
        self,
        message: str,
        violated_constraints: Optional[List[str]] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if violated_constraints:
            details["violated_constraints"] = violated_constraints
            
        super().__init__(
            message=message,
            error_code="CONSTRAINT_VIOLATION",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


class ConfigurationError(SchedulingError):
    """
    配置错误异常
    
    当系统配置不正确或缺失时抛出。
    """
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        details = kwargs.get("details", {})
        if config_key:
            details["config_key"] = config_key
            
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


class GateError(SchedulingError):
    """
    门禁检查异常
    
    当门禁检查失败时抛出。
    """
    
    def __init__(
        self,
        message: str,
        gate_type: Optional[str] = None,
        failed_conditions: Optional[List[str]] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if gate_type:
            details["gate_type"] = gate_type
        if failed_conditions:
            details["failed_conditions"] = failed_conditions
            
        super().__init__(
            message=message,
            error_code="GATE_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


class EventProcessingError(SchedulingError):
    """
    事件处理异常
    
    当处理外部事件时发生错误时抛出。
    """
    
    def __init__(
        self,
        message: str,
        event_type: Optional[str] = None,
        event_id: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if event_type:
            details["event_type"] = event_type
        if event_id:
            details["event_id"] = event_id
            
        super().__init__(
            message=message,
            error_code="EVENT_PROCESSING_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )
