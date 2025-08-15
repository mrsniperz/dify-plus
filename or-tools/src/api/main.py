"""
主应用文件 (Main Application)

智能排程系统的FastAPI主应用。
集成所有API路由、中间件和配置。

主要功能：
- 应用初始化和配置
- 路由注册
- 中间件设置
- 健康检查和监控
"""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from .prep_api import prep_router
from .config_api import config_router
from .middleware import setup_middleware
from ..core.constants import APIConstants


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    创建FastAPI应用实例
    
    Returns:
        配置好的FastAPI应用
    """
    # 创建应用
    app = FastAPI(
        title="智能排程系统 API",
        description="基于OR-Tools的发动机QEC维修计划智能调度引擎",
        version="0.1.0",
        docs_url=None,  # 禁用默认文档，使用自定义文档
        redoc_url=None,
        openapi_url=f"/api/{APIConstants.API_VERSION}/openapi.json"
    )
    
    # 设置中间件
    setup_middleware(app)
    
    # 注册路由
    register_routes(app)
    
    # 添加启动和关闭事件
    setup_events(app)
    
    logger.info("FastAPI application created successfully")
    
    return app


def register_routes(app: FastAPI) -> None:
    """
    注册所有API路由
    
    Args:
        app: FastAPI应用实例
    """
    # API版本前缀
    api_prefix = f"/api/{APIConstants.API_VERSION}"
    
    # 注册准备阶段API
    app.include_router(prep_router, prefix=api_prefix)
    
    # 注册配置管理API
    app.include_router(config_router, prefix=api_prefix)
    
    # 根路径
    @app.get("/")
    async def root():
        """根路径，返回API信息"""
        return {
            "name": "智能排程系统 API",
            "version": "0.1.0",
            "description": "基于OR-Tools的发动机QEC维修计划智能调度引擎",
            "api_version": APIConstants.API_VERSION,
            "timestamp": datetime.now().isoformat(),
            "docs_url": "/docs",
            "openapi_url": f"/api/{APIConstants.API_VERSION}/openapi.json"
        }
    
    # 健康检查
    @app.get("/health")
    async def health_check():
        """系统健康检查"""
        return {
            "status": "healthy",
            "service": "intelligent_scheduling_api",
            "version": "0.1.0",
            "timestamp": datetime.now().isoformat(),
            "uptime": "unknown"  # 实际应用中可以计算运行时间
        }
    
    # 系统信息
    @app.get("/info")
    async def system_info():
        """系统信息"""
        return {
            "system": {
                "name": "智能排程系统",
                "version": "0.1.0",
                "api_version": APIConstants.API_VERSION,
                "description": "基于OR-Tools的发动机QEC维修计划智能调度引擎"
            },
            "features": [
                "准备阶段智能排程",
                "事件驱动重排",
                "多项目并行优化",
                "门禁管理",
                "资源冲突检测",
                "策略模板切换"
            ],
            "endpoints": {
                "preparation": f"{api_prefix}/prep",
                "configuration": f"{api_prefix}/config",
                "documentation": "/docs",
                "health": "/health"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    # 性能指标
    @app.get("/metrics")
    async def get_metrics(request: Request):
        """获取性能指标"""
        try:
            # 从中间件获取性能指标
            performance_monitor = getattr(request.app.state, "performance_monitor", None)
            if performance_monitor:
                metrics = performance_monitor.get_metrics()
            else:
                metrics = {"error": "Performance monitoring not available"}
            
            return {
                "metrics": metrics,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error retrieving metrics: {e}")
            return {
                "error": "Failed to retrieve metrics",
                "timestamp": datetime.now().isoformat()
            }
    
    # 自定义文档页面
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        """自定义Swagger UI文档页面"""
        return get_swagger_ui_html(
            openapi_url=f"/api/{APIConstants.API_VERSION}/openapi.json",
            title="智能排程系统 API 文档",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        )
    
    logger.info("API routes registered successfully")


def setup_events(app: FastAPI) -> None:
    """
    设置应用启动和关闭事件
    
    Args:
        app: FastAPI应用实例
    """
    
    @app.on_event("startup")
    async def startup_event():
        """应用启动事件"""
        logger.info("智能排程系统 API 启动中...")
        
        # 初始化服务（如果需要）
        # 例如：数据库连接、缓存初始化等
        
        logger.info("智能排程系统 API 启动完成")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """应用关闭事件"""
        logger.info("智能排程系统 API 关闭中...")
        
        # 清理资源（如果需要）
        # 例如：关闭数据库连接、清理缓存等
        
        logger.info("智能排程系统 API 关闭完成")


def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """
    自定义OpenAPI规范
    
    Args:
        app: FastAPI应用实例
        
    Returns:
        自定义的OpenAPI规范
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="智能排程系统 API",
        version="0.1.0",
        description="""
        ## 智能排程系统 API
        
        基于Google OR-Tools CP-SAT求解器的发动机QEC维修计划智能调度引擎。
        
        ### 主要功能
        
        - **准备阶段智能排程**: 生成准备阶段的排程计划
        - **事件驱动重排**: 处理外部事件并动态调整排程
        - **门禁管理**: 验证准备阶段的门禁条件
        - **资源管理**: 管理资源分配和冲突检测
        - **配置管理**: 策略模板切换和参数配置
        
        ### API版本
        
        当前API版本: v1
        
        ### 认证
        
        目前API不需要认证，后续版本将添加认证机制。
        
        ### 错误处理
        
        所有API错误都返回统一格式的错误响应，包含错误代码、消息和详细信息。
        
        ### 性能
        
        - 单工包求解时间 ≤ 5秒
        - 多工包求解时间 ≤ 20秒
        - 支持并发请求处理
        """,
        routes=app.routes,
    )
    
    # 添加自定义信息
    openapi_schema["info"]["contact"] = {
        "name": "开发团队",
        "email": "dev@company.com"
    }
    
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
    
    # 添加服务器信息
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "开发环境"
        },
        {
            "url": "https://api.scheduling.company.com",
            "description": "生产环境"
        }
    ]
    
    # 添加标签描述
    openapi_schema["tags"] = [
        {
            "name": "preparation",
            "description": "准备阶段相关操作"
        },
        {
            "name": "configuration",
            "description": "系统配置管理"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# 创建应用实例
app = create_app()

# 设置自定义OpenAPI
app.openapi = lambda: custom_openapi(app)


if __name__ == "__main__":
    import uvicorn
    
    # 开发模式运行
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
