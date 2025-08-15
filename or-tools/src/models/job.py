"""
工卡子项目模型 (Job Models)

定义工卡子项目的数据模型，这是排程系统中最基础的原子任务单元。
每个Job对应工卡中一个具体的操作步骤，包含工时、资源需求、依赖关系等信息。

模型层次：
- Job: 基础工卡子项目模型
- JobCreate: 创建工卡子项目的请求模型
- JobUpdate: 更新工卡子项目的请求模型
- JobInDB: 数据库存储模型（包含额外的元数据）
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

from ..core.constants import TaskStatus


class JobPriority(str, Enum):
    """工卡子项目优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResourceRequirement(BaseModel):
    """资源需求模型"""
    resource_id: str = Field(..., description="资源ID")
    quantity: int = Field(1, ge=1, description="所需数量")
    is_critical: bool = Field(False, description="是否为关键资源")
    
    class Config:
        schema_extra = {
            "example": {
                "resource_id": "CRANE-1",
                "quantity": 1,
                "is_critical": True
            }
        }


class PerformanceFactor(BaseModel):
    """绩效因子模型"""
    employee_id: str = Field(..., description="员工ID")
    factor: float = Field(..., ge=0.1, le=2.0, description="绩效因子，<1表示更快，>1表示更慢")
    
    class Config:
        schema_extra = {
            "example": {
                "employee_id": "E-001",
                "factor": 0.9
            }
        }


class Job(BaseModel):
    """
    工卡子项目基础模型
    
    排程系统中最基础的原子任务，对应工卡中一个具体的操作步骤。
    """
    job_id: str = Field(..., description="工卡子项目唯一标识")
    work_card_id: str = Field(..., description="所属工卡ID")
    engine_id: str = Field(..., description="所属发动机ID")
    
    # 任务基本信息
    name: str = Field(..., description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    task_code: Optional[str] = Field(None, description="任务代码，如AMM TASK 71-51-43-400-001-A")
    
    # 工时和优先级
    base_duration_hours: float = Field(..., gt=0, description="基准工时（小时）")
    priority: JobPriority = Field(JobPriority.MEDIUM, description="任务优先级")
    
    # 资源需求
    required_resources: List[ResourceRequirement] = Field(
        default_factory=list, 
        description="所需资源清单"
    )
    required_qualifications: List[str] = Field(
        default_factory=list,
        description="所需资质清单"
    )
    
    # 依赖关系
    predecessor_jobs: List[str] = Field(
        default_factory=list,
        description="前置依赖的工卡子项目ID列表"
    )
    successor_jobs: List[str] = Field(
        default_factory=list,
        description="后续依赖的工卡子项目ID列表"
    )
    
    # 绩效因子
    performance_factors: List[PerformanceFactor] = Field(
        default_factory=list,
        description="员工绩效因子列表"
    )
    
    # 约束条件
    earliest_start: Optional[datetime] = Field(None, description="最早开始时间")
    latest_finish: Optional[datetime] = Field(None, description="最晚完成时间")
    fixed_start: Optional[datetime] = Field(None, description="固定开始时间")
    fixed_duration: Optional[float] = Field(None, gt=0, description="固定工时（小时）")
    
    # 状态信息
    status: TaskStatus = Field(TaskStatus.NOT_STARTED, description="任务状态")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")
    
    @validator('predecessor_jobs')
    def validate_no_self_dependency(cls, v, values):
        """验证不能依赖自己"""
        job_id = values.get('job_id')
        if job_id and job_id in v:
            raise ValueError(f"Job {job_id} cannot depend on itself")
        return v
    
    @validator('performance_factors')
    def validate_unique_employees(cls, v):
        """验证员工绩效因子唯一性"""
        employee_ids = [pf.employee_id for pf in v]
        if len(employee_ids) != len(set(employee_ids)):
            raise ValueError("Performance factors must have unique employee IDs")
        return v
    
    def get_effective_duration(self, employee_id: Optional[str] = None) -> float:
        """
        获取有效工时
        
        Args:
            employee_id: 执行员工ID，用于计算绩效调整后的工时
            
        Returns:
            有效工时（小时）
        """
        if self.fixed_duration:
            return self.fixed_duration
            
        base_duration = self.base_duration_hours
        
        if employee_id:
            # 查找员工绩效因子
            for pf in self.performance_factors:
                if pf.employee_id == employee_id:
                    return base_duration * pf.factor
                    
        return base_duration
    
    def has_resource_requirement(self, resource_id: str) -> bool:
        """
        检查是否需要特定资源
        
        Args:
            resource_id: 资源ID
            
        Returns:
            是否需要该资源
        """
        return any(req.resource_id == resource_id for req in self.required_resources)
    
    def get_resource_quantity(self, resource_id: str) -> int:
        """
        获取特定资源的需求数量
        
        Args:
            resource_id: 资源ID
            
        Returns:
            需求数量，如果不需要该资源则返回0
        """
        for req in self.required_resources:
            if req.resource_id == resource_id:
                return req.quantity
        return 0
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "job_id": "J-001",
                "work_card_id": "WC-001",
                "engine_id": "ENG-001",
                "name": "发动机拆卸检查",
                "description": "按照AMM手册进行发动机拆卸和初步检查",
                "task_code": "AMM TASK 71-51-43-400-001-A",
                "base_duration_hours": 4.0,
                "priority": "medium",
                "required_resources": [
                    {"resource_id": "CRANE-1", "quantity": 1, "is_critical": True},
                    {"resource_id": "TECH-001", "quantity": 2, "is_critical": False}
                ],
                "required_qualifications": ["inspector", "crane_operator"],
                "predecessor_jobs": [],
                "successor_jobs": ["J-002"],
                "performance_factors": [
                    {"employee_id": "E-001", "factor": 0.9}
                ],
                "status": "not_started"
            }
        }


class JobCreate(BaseModel):
    """创建工卡子项目的请求模型"""
    work_card_id: str = Field(..., description="所属工卡ID")
    engine_id: str = Field(..., description="所属发动机ID")
    name: str = Field(..., description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    task_code: Optional[str] = Field(None, description="任务代码")
    base_duration_hours: float = Field(..., gt=0, description="基准工时（小时）")
    priority: JobPriority = Field(JobPriority.MEDIUM, description="任务优先级")
    required_resources: List[ResourceRequirement] = Field(default_factory=list)
    required_qualifications: List[str] = Field(default_factory=list)
    predecessor_jobs: List[str] = Field(default_factory=list)
    performance_factors: List[PerformanceFactor] = Field(default_factory=list)
    earliest_start: Optional[datetime] = Field(None)
    latest_finish: Optional[datetime] = Field(None)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class JobUpdate(BaseModel):
    """更新工卡子项目的请求模型"""
    name: Optional[str] = Field(None, description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    base_duration_hours: Optional[float] = Field(None, gt=0, description="基准工时（小时）")
    priority: Optional[JobPriority] = Field(None, description="任务优先级")
    required_resources: Optional[List[ResourceRequirement]] = Field(None)
    required_qualifications: Optional[List[str]] = Field(None)
    predecessor_jobs: Optional[List[str]] = Field(None)
    performance_factors: Optional[List[PerformanceFactor]] = Field(None)
    earliest_start: Optional[datetime] = Field(None)
    latest_finish: Optional[datetime] = Field(None)
    status: Optional[TaskStatus] = Field(None, description="任务状态")
    metadata: Optional[Dict[str, Any]] = Field(None)


class JobInDB(Job):
    """数据库存储的工卡子项目模型"""
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    created_by: Optional[str] = Field(None, description="创建者")
    updated_by: Optional[str] = Field(None, description="更新者")
    version: int = Field(1, description="版本号")
    
    def update_timestamp(self):
        """更新时间戳"""
        self.updated_at = datetime.now()
        self.version += 1
