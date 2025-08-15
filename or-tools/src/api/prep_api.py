"""
准备阶段API (Preparation API)

提供准备阶段相关的RESTful API接口。
包括排程计划生成、事件处理、汇总查询、交接确认等功能。

主要端点：
- POST /prep/tasks/plan: 生成准备排程
- POST /prep/events/apply: 事件驱动重排
- GET /prep/summary: 准备态汇总
- POST /prep/handovers/confirm: 交接确认
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..services import (
    SchedulingService, SchedulingRequest, SchedulingResponse,
    EventService, ResourceService, GateService
)
# from ..schemas import request_schemas, response_schemas  # TODO: 实现schemas模块
from ..core.exceptions import (
    SchedulingError, EventProcessingError, ValidationError,
    ResourceConflictError, GateError
)


logger = logging.getLogger(__name__)

# 创建路由器
prep_router = APIRouter(prefix="/prep", tags=["preparation"])

# 服务实例（在实际应用中应该通过依赖注入）
scheduling_service = SchedulingService()
event_service = EventService()
resource_service = ResourceService()
gate_service = GateService()


class PlanRequest(BaseModel):
    """排程计划请求模型"""
    work_packages: List[Dict[str, Any]] = Field(..., description="工包列表")
    assets: List[Dict[str, Any]] = Field(..., description="工装设备列表")
    humans: List[Dict[str, Any]] = Field(..., description="人力资源列表")
    config: Dict[str, Any] = Field(default_factory=dict, description="配置参数")
    
    class Config:
        schema_extra = {
            "example": {
                "work_packages": [
                    {
                        "work_package_id": "WP-001",
                        "engine_id": "ENG-001",
                        "jobs": ["J-001", "J-002"],
                        "materials": [
                            {
                                "material_id": "M-001",
                                "must_kit": True,
                                "allow_partial": False,
                                "eta": "2025-08-15T12:00:00Z"
                            }
                        ]
                    }
                ],
                "assets": [
                    {
                        "asset_id": "CRANE-1",
                        "category": "hoist",
                        "is_critical": True,
                        "calendar": {}
                    }
                ],
                "humans": [
                    {
                        "employee_id": "E-001",
                        "qualifications": ["inspector"],
                        "availability_schedule": {}
                    }
                ],
                "config": {
                    "prep_window_days": 2,
                    "objective_template": "balanced",
                    "freeze_inprogress": True
                }
            }
        }


class EventRequest(BaseModel):
    """事件处理请求模型"""
    plan_id: str = Field(..., description="计划ID")
    events: List[Dict[str, Any]] = Field(..., description="事件列表")
    policy: str = Field("replan_unstarted", description="处理策略")
    
    class Config:
        schema_extra = {
            "example": {
                "plan_id": "PLAN-20250815-001",
                "events": [
                    {
                        "type": "eta_change",
                        "effective_time": "2025-08-15T10:00:00Z",
                        "payload": {
                            "material_id": "M-001",
                            "new_eta": "2025-08-15T16:00:00Z"
                        }
                    }
                ],
                "policy": "replan_unstarted"
            }
        }


class HandoverRequest(BaseModel):
    """交接确认请求模型"""
    plan_id: str = Field(..., description="计划ID")
    prep_id: str = Field(..., description="准备任务ID")
    evidence: Dict[str, Any] = Field(..., description="证据信息")
    
    class Config:
        schema_extra = {
            "example": {
                "plan_id": "PLAN-20250815-001",
                "prep_id": "P-001",
                "evidence": {
                    "handover_form": "https://storage.example.com/form123.pdf",
                    "photo": "https://storage.example.com/photo123.jpg",
                    "signature": {
                        "by": "E-001",
                        "time": "2025-08-15T10:00:00Z"
                    }
                }
            }
        }


@prep_router.post("/tasks/plan")
async def create_preparation_plan(request: PlanRequest) -> JSONResponse:
    """
    生成准备排程
    
    根据工包、资源和配置信息生成准备阶段的排程计划。
    """
    try:
        logger.info("Received preparation plan request")
        
        # 创建排程请求
        scheduling_request = SchedulingRequest(
            work_packages=request.work_packages,
            assets=request.assets,
            humans=request.humans,
            config=request.config
        )
        
        # 执行排程
        response = scheduling_service.create_schedule(scheduling_request)
        
        # 返回结果
        if response.error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.error
            )
        
        result = response.to_dict()
        
        logger.info(f"Successfully created preparation plan {response.plan_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result
        )
        
    except ValidationError as e:
        logger.error(f"Validation error in preparation plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation_error", "message": str(e)}
        )
    
    except SchedulingError as e:
        logger.error(f"Scheduling error in preparation plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.to_dict()
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in preparation plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "internal_error", "message": "Internal server error"}
        )


@prep_router.post("/events/apply")
async def apply_events(request: EventRequest) -> JSONResponse:
    """
    事件驱动重排
    
    应用外部事件并触发排程计划的动态调整。
    """
    try:
        logger.info(f"Applying events to plan {request.plan_id}")
        
        # 应用事件
        result = event_service.apply_events(
            plan_id=request.plan_id,
            events=request.events
        )
        
        logger.info(f"Successfully applied events to plan {request.plan_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result
        )
        
    except ValidationError as e:
        logger.error(f"Validation error in event application: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation_error", "message": str(e)}
        )
    
    except EventProcessingError as e:
        logger.error(f"Event processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.to_dict()
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in event application: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "internal_error", "message": "Internal server error"}
        )


@prep_router.get("/summary")
async def get_preparation_summary(
    plan_id: str,
    include_gates: bool = True,
    include_resources: bool = True
) -> JSONResponse:
    """
    准备态汇总
    
    获取准备阶段的汇总信息，包括门禁状态、资源利用率等。
    """
    try:
        logger.info(f"Getting preparation summary for plan {plan_id}")
        
        summary = {
            "plan_id": plan_id,
            "generated_at": datetime.now().isoformat()
        }
        
        # 添加门禁汇总
        if include_gates:
            # 这里应该从数据库或缓存中获取实际的门禁状态
            # 简化实现：返回示例数据
            gate_results = {}  # 实际应该调用 gate_service.check_all_gates()
            gate_summary = gate_service.get_gate_summary(plan_id, gate_results)
            summary["gates"] = gate_summary
        
        # 添加资源汇总
        if include_resources:
            # 这里应该从数据库或缓存中获取实际的排程和资源数据
            # 简化实现：返回示例数据
            schedule = None  # 实际应该获取排程计划
            resources = []   # 实际应该获取资源列表
            resource_summary = resource_service.get_resource_summary(
                plan_id, schedule, resources
            )
            summary["resources"] = resource_summary
        
        logger.info(f"Successfully generated preparation summary for plan {plan_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=summary
        )
        
    except Exception as e:
        logger.error(f"Error generating preparation summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "internal_error", "message": "Internal server error"}
        )


@prep_router.post("/handovers/confirm")
async def confirm_handover(request: HandoverRequest) -> JSONResponse:
    """
    交接确认
    
    确认准备任务的交接，更新门禁状态。
    """
    try:
        logger.info(f"Confirming handover for prep task {request.prep_id}")
        
        # 确认交接
        result = gate_service.confirm_handover(
            plan_id=request.plan_id,
            prep_id=request.prep_id,
            evidence=request.evidence
        )
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result
            )
        
        logger.info(f"Successfully confirmed handover for prep task {request.prep_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result
        )
        
    except ValidationError as e:
        logger.error(f"Validation error in handover confirmation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation_error", "message": str(e)}
        )
    
    except GateError as e:
        logger.error(f"Gate error in handover confirmation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.to_dict()
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in handover confirmation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "internal_error", "message": "Internal server error"}
        )


@prep_router.get("/health")
async def health_check() -> JSONResponse:
    """
    健康检查
    
    检查准备阶段API的健康状态。
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "service": "preparation_api",
            "timestamp": datetime.now().isoformat()
        }
    )
