"""
配置管理API (Configuration API)

提供系统配置管理的RESTful API接口。
包括策略模板切换、插单护栏设置、求解器参数配置等功能。

主要端点：
- POST /config/priority-template:apply: 策略模板切换
- POST /config/preemption:settings: 插单护栏设置
- GET /config/templates: 获取策略模板列表
- GET /config/current: 获取当前配置
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..core.constants import PriorityTemplate
from ..core.exceptions import ConfigurationError, ValidationError


logger = logging.getLogger(__name__)

# 创建路由器
config_router = APIRouter(prefix="/config", tags=["configuration"])


class PriorityTemplateRequest(BaseModel):
    """策略模板切换请求模型"""
    template: str = Field(..., description="策略模板名称")
    scope: Optional[Dict[str, Any]] = Field(None, description="应用范围")
    effective_time: Optional[datetime] = Field(None, description="生效时间")
    
    class Config:
        schema_extra = {
            "example": {
                "template": "protect_sla",
                "scope": {
                    "engines": ["ENG-001"],
                    "work_packages": ["WP-001"]
                },
                "effective_time": "2025-08-15T10:00:00Z"
            }
        }


class PreemptionSettingsRequest(BaseModel):
    """插单护栏设置请求模型"""
    max_preemptions_per_day: int = Field(..., ge=0, description="每日最大插单次数")
    max_preemption_hours: float = Field(..., ge=0, description="最大插单时长（小时）")
    priority_threshold: str = Field("high", description="插单优先级阈值")
    blackout_periods: List[Dict[str, str]] = Field(default_factory=list, description="禁止插单时段")
    
    class Config:
        schema_extra = {
            "example": {
                "max_preemptions_per_day": 2,
                "max_preemption_hours": 4.0,
                "priority_threshold": "high",
                "blackout_periods": [
                    {
                        "start": "22:00",
                        "end": "06:00",
                        "reason": "night_shift_protection"
                    }
                ]
            }
        }


class SolverConfigRequest(BaseModel):
    """求解器配置请求模型"""
    time_limit_seconds: float = Field(300.0, gt=0, description="求解时间限制（秒）")
    num_search_workers: int = Field(1, ge=1, description="搜索工作线程数")
    log_search_progress: bool = Field(False, description="是否记录搜索进度")
    optimization_parameters: Dict[str, Any] = Field(default_factory=dict, description="优化参数")
    
    class Config:
        schema_extra = {
            "example": {
                "time_limit_seconds": 300.0,
                "num_search_workers": 4,
                "log_search_progress": True,
                "optimization_parameters": {
                    "linearization_level": 2,
                    "cp_model_presolve": True
                }
            }
        }


# 全局配置存储（在实际应用中应该使用数据库或配置服务）
_current_config = {
    "priority_template": PriorityTemplate.BALANCED.value,
    "preemption_settings": {
        "max_preemptions_per_day": 2,
        "max_preemption_hours": 4.0,
        "priority_threshold": "high",
        "blackout_periods": []
    },
    "solver_config": {
        "time_limit_seconds": 300.0,
        "num_search_workers": 1,
        "log_search_progress": False,
        "optimization_parameters": {}
    },
    "last_updated": datetime.now().isoformat(),
    "updated_by": "system"
}


@config_router.post("/priority-template:apply")
async def apply_priority_template(request: PriorityTemplateRequest) -> JSONResponse:
    """
    策略模板切换
    
    切换优先级策略模板，影响后续的排程优化目标。
    """
    try:
        logger.info(f"Applying priority template: {request.template}")
        
        # 验证模板名称
        valid_templates = [t.value for t in PriorityTemplate]
        if request.template not in valid_templates:
            raise ValidationError(
                f"Invalid template '{request.template}'. "
                f"Valid templates: {', '.join(valid_templates)}"
            )
        
        # 更新配置
        _current_config["priority_template"] = request.template
        _current_config["last_updated"] = datetime.now().isoformat()
        _current_config["updated_by"] = "api_user"  # 实际应该从认证信息获取
        
        # 计算生效时间
        effective_time = request.effective_time or datetime.now()
        
        result = {
            "status": "success",
            "template": request.template,
            "scope": request.scope or {"global": True},
            "effective_time": effective_time.isoformat(),
            "applied_at": datetime.now().isoformat()
        }
        
        logger.info(f"Successfully applied priority template: {request.template}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result
        )
        
    except ValidationError as e:
        logger.error(f"Validation error in priority template application: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation_error", "message": str(e)}
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in priority template application: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "internal_error", "message": "Internal server error"}
        )


@config_router.post("/preemption:settings")
async def update_preemption_settings(request: PreemptionSettingsRequest) -> JSONResponse:
    """
    插单护栏设置
    
    更新插单机制的护栏参数，控制插单的频率和影响范围。
    """
    try:
        logger.info("Updating preemption settings")
        
        # 验证设置
        if request.max_preemptions_per_day > 10:
            raise ValidationError("Maximum preemptions per day cannot exceed 10")
        
        if request.max_preemption_hours > 24:
            raise ValidationError("Maximum preemption hours cannot exceed 24")
        
        # 验证优先级阈值
        valid_priorities = ["low", "medium", "high", "critical"]
        if request.priority_threshold not in valid_priorities:
            raise ValidationError(
                f"Invalid priority threshold '{request.priority_threshold}'. "
                f"Valid values: {', '.join(valid_priorities)}"
            )
        
        # 更新配置
        _current_config["preemption_settings"] = {
            "max_preemptions_per_day": request.max_preemptions_per_day,
            "max_preemption_hours": request.max_preemption_hours,
            "priority_threshold": request.priority_threshold,
            "blackout_periods": request.blackout_periods
        }
        _current_config["last_updated"] = datetime.now().isoformat()
        _current_config["updated_by"] = "api_user"
        
        result = {
            "status": "success",
            "settings": _current_config["preemption_settings"],
            "updated_at": datetime.now().isoformat()
        }
        
        logger.info("Successfully updated preemption settings")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result
        )
        
    except ValidationError as e:
        logger.error(f"Validation error in preemption settings update: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation_error", "message": str(e)}
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in preemption settings update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "internal_error", "message": "Internal server error"}
        )


@config_router.post("/solver:settings")
async def update_solver_settings(request: SolverConfigRequest) -> JSONResponse:
    """
    求解器配置更新
    
    更新求解器的参数配置，影响求解性能和质量。
    """
    try:
        logger.info("Updating solver settings")
        
        # 验证设置
        if request.time_limit_seconds > 3600:  # 最大1小时
            raise ValidationError("Time limit cannot exceed 3600 seconds")
        
        if request.num_search_workers > 16:  # 最大16个线程
            raise ValidationError("Number of search workers cannot exceed 16")
        
        # 更新配置
        _current_config["solver_config"] = {
            "time_limit_seconds": request.time_limit_seconds,
            "num_search_workers": request.num_search_workers,
            "log_search_progress": request.log_search_progress,
            "optimization_parameters": request.optimization_parameters
        }
        _current_config["last_updated"] = datetime.now().isoformat()
        _current_config["updated_by"] = "api_user"
        
        result = {
            "status": "success",
            "settings": _current_config["solver_config"],
            "updated_at": datetime.now().isoformat()
        }
        
        logger.info("Successfully updated solver settings")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result
        )
        
    except ValidationError as e:
        logger.error(f"Validation error in solver settings update: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation_error", "message": str(e)}
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in solver settings update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "internal_error", "message": "Internal server error"}
        )


@config_router.get("/templates")
async def get_priority_templates() -> JSONResponse:
    """
    获取策略模板列表
    
    返回所有可用的优先级策略模板及其描述。
    """
    try:
        templates = [
            {
                "name": PriorityTemplate.BALANCED.value,
                "display_name": "均衡公平型",
                "description": "平衡各种优化目标，适用于常规排程场景",
                "weights": {
                    "makespan": 1.0,
                    "cost": 0.3,
                    "utilization": 0.2,
                    "waiting": 0.4,
                    "delays": 0.6
                }
            },
            {
                "name": PriorityTemplate.PROTECT_SLA.value,
                "display_name": "保护SLA型",
                "description": "优先保护SLA承诺，最小化延误风险",
                "weights": {
                    "makespan": 2.0,
                    "cost": 0.1,
                    "utilization": 0.1,
                    "waiting": 0.2,
                    "delays": 1.0
                }
            },
            {
                "name": PriorityTemplate.COST_MIN.value,
                "display_name": "成本最小型",
                "description": "优先最小化成本，适用于成本敏感场景",
                "weights": {
                    "makespan": 0.5,
                    "cost": 1.0,
                    "utilization": 0.3,
                    "waiting": 0.1,
                    "delays": 0.3
                }
            }
        ]
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "templates": templates,
                "current_template": _current_config["priority_template"],
                "retrieved_at": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving priority templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "internal_error", "message": "Internal server error"}
        )


@config_router.get("/current")
async def get_current_config() -> JSONResponse:
    """
    获取当前配置
    
    返回系统当前的所有配置参数。
    """
    try:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "config": _current_config,
                "retrieved_at": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving current config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "internal_error", "message": "Internal server error"}
        )


@config_router.post("/reset")
async def reset_config() -> JSONResponse:
    """
    重置配置
    
    将所有配置重置为默认值。
    """
    try:
        logger.info("Resetting configuration to defaults")
        
        # 重置为默认配置
        global _current_config
        _current_config = {
            "priority_template": PriorityTemplate.BALANCED.value,
            "preemption_settings": {
                "max_preemptions_per_day": 2,
                "max_preemption_hours": 4.0,
                "priority_threshold": "high",
                "blackout_periods": []
            },
            "solver_config": {
                "time_limit_seconds": 300.0,
                "num_search_workers": 1,
                "log_search_progress": False,
                "optimization_parameters": {}
            },
            "last_updated": datetime.now().isoformat(),
            "updated_by": "api_user"
        }
        
        logger.info("Successfully reset configuration to defaults")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Configuration reset to defaults",
                "config": _current_config,
                "reset_at": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error resetting configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "internal_error", "message": "Internal server error"}
        )


@config_router.get("/health")
async def health_check() -> JSONResponse:
    """
    健康检查
    
    检查配置管理API的健康状态。
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "service": "configuration_api",
            "timestamp": datetime.now().isoformat()
        }
    )
