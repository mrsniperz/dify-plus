"""
API中间件 (API Middleware)

提供API请求处理的中间件功能。
包括错误处理、请求日志、性能监控、CORS支持等。

主要功能：
- 统一错误处理
- 请求/响应日志
- 性能监控
- CORS支持
- 请求ID追踪
"""

import time
import uuid
import logging
from typing import Callable, Dict, Any
from datetime import datetime

from fastapi import Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from ..core.exceptions import (
    SchedulingError, SolverError, ValidationError,
    ResourceConflictError, ConstraintViolationError,
    EventProcessingError, GateError, ConfigurationError
)


logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    
    记录所有API请求和响应的详细信息。
    """
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: RequestResponseEndpoint
    ) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 记录请求开始
        start_time = time.time()
        
        # 获取客户端信息
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        logger.info(
            f"Request started - ID: {request_id}, "
            f"Method: {request.method}, "
            f"URL: {request.url}, "
            f"Client: {client_ip}, "
            f"User-Agent: {user_agent}"
        )
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            # 记录请求完成
            logger.info(
                f"Request completed - ID: {request_id}, "
                f"Status: {response.status_code}, "
                f"Process-Time: {process_time:.3f}s"
            )
            
            return response
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录请求错误
            logger.error(
                f"Request failed - ID: {request_id}, "
                f"Error: {str(e)}, "
                f"Process-Time: {process_time:.3f}s"
            )
            
            # 重新抛出异常，让错误处理器处理
            raise


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    性能监控中间件
    
    监控API性能指标，包括响应时间、吞吐量等。
    """
    
    def __init__(self, app, slow_request_threshold: float = 5.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
        self.request_metrics: Dict[str, Any] = {
            "total_requests": 0,
            "slow_requests": 0,
            "error_requests": 0,
            "average_response_time": 0.0
        }
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # 计算响应时间
            response_time = time.time() - start_time
            
            # 更新指标
            self._update_metrics(response_time, response.status_code)
            
            # 检查慢请求
            if response_time > self.slow_request_threshold:
                logger.warning(
                    f"Slow request detected - "
                    f"URL: {request.url}, "
                    f"Method: {request.method}, "
                    f"Response-Time: {response_time:.3f}s"
                )
            
            # 添加性能头
            response.headers["X-Response-Time"] = f"{response_time:.3f}"
            
            return response
            
        except Exception as e:
            # 更新错误指标
            response_time = time.time() - start_time
            self._update_metrics(response_time, 500, is_error=True)
            raise
    
    def _update_metrics(
        self, 
        response_time: float, 
        status_code: int, 
        is_error: bool = False
    ) -> None:
        """更新性能指标"""
        self.request_metrics["total_requests"] += 1
        
        if is_error or status_code >= 400:
            self.request_metrics["error_requests"] += 1
        
        if response_time > self.slow_request_threshold:
            self.request_metrics["slow_requests"] += 1
        
        # 更新平均响应时间（简化计算）
        total = self.request_metrics["total_requests"]
        current_avg = self.request_metrics["average_response_time"]
        self.request_metrics["average_response_time"] = (
            (current_avg * (total - 1) + response_time) / total
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self.request_metrics.copy()


def create_error_handler():
    """
    创建统一错误处理器
    
    处理所有类型的异常，返回统一格式的错误响应。
    """
    
    async def handle_scheduling_error(request: Request, exc: SchedulingError) -> JSONResponse:
        """处理排程错误"""
        logger.error(f"Scheduling error: {exc}")
        
        return JSONResponse(
            status_code=500,
            content=exc.to_dict(),
            headers={"X-Request-ID": getattr(request.state, "request_id", "unknown")}
        )
    
    async def handle_solver_error(request: Request, exc: SolverError) -> JSONResponse:
        """处理求解器错误"""
        logger.error(f"Solver error: {exc}")
        
        return JSONResponse(
            status_code=500,
            content=exc.to_dict(),
            headers={"X-Request-ID": getattr(request.state, "request_id", "unknown")}
        )
    
    async def handle_validation_error(request: Request, exc: ValidationError) -> JSONResponse:
        """处理验证错误"""
        logger.warning(f"Validation error: {exc}")
        
        return JSONResponse(
            status_code=400,
            content=exc.to_dict(),
            headers={"X-Request-ID": getattr(request.state, "request_id", "unknown")}
        )
    
    async def handle_resource_conflict_error(request: Request, exc: ResourceConflictError) -> JSONResponse:
        """处理资源冲突错误"""
        logger.warning(f"Resource conflict error: {exc}")
        
        return JSONResponse(
            status_code=409,
            content=exc.to_dict(),
            headers={"X-Request-ID": getattr(request.state, "request_id", "unknown")}
        )
    
    async def handle_constraint_violation_error(request: Request, exc: ConstraintViolationError) -> JSONResponse:
        """处理约束违反错误"""
        logger.warning(f"Constraint violation error: {exc}")
        
        return JSONResponse(
            status_code=422,
            content=exc.to_dict(),
            headers={"X-Request-ID": getattr(request.state, "request_id", "unknown")}
        )
    
    async def handle_event_processing_error(request: Request, exc: EventProcessingError) -> JSONResponse:
        """处理事件处理错误"""
        logger.error(f"Event processing error: {exc}")
        
        return JSONResponse(
            status_code=500,
            content=exc.to_dict(),
            headers={"X-Request-ID": getattr(request.state, "request_id", "unknown")}
        )
    
    async def handle_gate_error(request: Request, exc: GateError) -> JSONResponse:
        """处理门禁错误"""
        logger.warning(f"Gate error: {exc}")
        
        return JSONResponse(
            status_code=422,
            content=exc.to_dict(),
            headers={"X-Request-ID": getattr(request.state, "request_id", "unknown")}
        )
    
    async def handle_configuration_error(request: Request, exc: ConfigurationError) -> JSONResponse:
        """处理配置错误"""
        logger.error(f"Configuration error: {exc}")
        
        return JSONResponse(
            status_code=500,
            content=exc.to_dict(),
            headers={"X-Request-ID": getattr(request.state, "request_id", "unknown")}
        )
    
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        """处理HTTP异常"""
        logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "type": "HTTPException"
                }
            },
            headers={"X-Request-ID": getattr(request.state, "request_id", "unknown")}
        )
    
    async def handle_generic_exception(request: Request, exc: Exception) -> JSONResponse:
        """处理通用异常"""
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "type": "InternalServerError"
                }
            },
            headers={"X-Request-ID": getattr(request.state, "request_id", "unknown")}
        )
    
    return {
        SchedulingError: handle_scheduling_error,
        SolverError: handle_solver_error,
        ValidationError: handle_validation_error,
        ResourceConflictError: handle_resource_conflict_error,
        ConstraintViolationError: handle_constraint_violation_error,
        EventProcessingError: handle_event_processing_error,
        GateError: handle_gate_error,
        ConfigurationError: handle_configuration_error,
        HTTPException: handle_http_exception,
        Exception: handle_generic_exception,
    }


def setup_cors_middleware(app, allowed_origins: list = None):
    """
    设置CORS中间件
    
    Args:
        app: FastAPI应用实例
        allowed_origins: 允许的源列表
    """
    if allowed_origins is None:
        allowed_origins = [
            "http://localhost:3000",  # React开发服务器
            "http://localhost:8080",  # Vue开发服务器
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080",
        ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time", "X-Response-Time"]
    )


def setup_middleware(app):
    """
    设置所有中间件
    
    Args:
        app: FastAPI应用实例
    """
    # 设置CORS
    setup_cors_middleware(app)
    
    # 添加性能监控中间件
    performance_middleware = PerformanceMonitoringMiddleware(app)
    app.add_middleware(PerformanceMonitoringMiddleware)
    
    # 添加请求日志中间件
    app.add_middleware(RequestLoggingMiddleware)
    
    # 设置错误处理器
    error_handlers = create_error_handler()
    for exception_type, handler in error_handlers.items():
        app.add_exception_handler(exception_type, handler)
    
    # 存储性能监控实例，便于获取指标
    app.state.performance_monitor = performance_middleware
    
    logger.info("Middleware setup completed")
