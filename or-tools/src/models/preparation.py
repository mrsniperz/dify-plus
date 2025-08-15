"""
准备阶段模型 (Preparation Models)

定义准备阶段相关的数据模型，包括准备任务、物料项、工装设备等。
准备阶段是维修计划的关键环节，需要精确建模以支持门禁检查和资源调配。

模型层次：
- PreparationTask: 准备任务模型
- MaterialItem: 物料项模型
- ToolAsset: 工装设备模型
- Gate: 门禁模型
- Evidence: 证据模型
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

from ..core.constants import (
    PreparationTaskType,
    GateType,
    TaskStatus,
    MaterialCriticality,
    AssetCategory
)


class EvidenceType(str, Enum):
    """证据类型枚举"""
    HANDOVER_FORM = "handover_form"     # 交接单
    PHOTO = "photo"                     # 照片
    SIGNATURE = "signature"             # 签名
    DOCUMENT = "document"               # 文档
    CHECKLIST = "checklist"             # 检查清单


class Evidence(BaseModel):
    """证据模型"""
    evidence_type: EvidenceType = Field(..., description="证据类型")
    content: str = Field(..., description="证据内容（URL、哈希值或文本）")
    submitted_by: str = Field(..., description="提交者")
    submitted_at: datetime = Field(default_factory=datetime.now, description="提交时间")
    verified: bool = Field(False, description="是否已验证")
    verified_by: Optional[str] = Field(None, description="验证者")
    verified_at: Optional[datetime] = Field(None, description="验证时间")
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "evidence_type": "handover_form",
                "content": "https://storage.example.com/handover/form123.pdf",
                "submitted_by": "E-001",
                "submitted_at": "2025-08-15T10:00:00Z",
                "verified": True,
                "verified_by": "E-002",
                "verified_at": "2025-08-15T10:30:00Z"
            }
        }


class Gate(BaseModel):
    """门禁模型"""
    gate_type: GateType = Field(..., description="门禁类型")
    name: str = Field(..., description="门禁名称")
    description: Optional[str] = Field(None, description="门禁描述")
    is_passed: bool = Field(False, description="是否通过")
    required_conditions: List[str] = Field(default_factory=list, description="必要条件")
    failed_conditions: List[str] = Field(default_factory=list, description="失败条件")
    passed_at: Optional[datetime] = Field(None, description="通过时间")
    checked_by: Optional[str] = Field(None, description="检查者")
    
    def check_condition(self, condition: str, passed: bool):
        """
        检查条件状态
        
        Args:
            condition: 条件名称
            passed: 是否通过
        """
        if passed:
            if condition in self.failed_conditions:
                self.failed_conditions.remove(condition)
        else:
            if condition not in self.failed_conditions:
                self.failed_conditions.append(condition)
        
        # 更新门禁状态
        self.is_passed = len(self.failed_conditions) == 0
        if self.is_passed and not self.passed_at:
            self.passed_at = datetime.now()
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "gate_type": "critical_tools_ready",
                "name": "关键工装齐套门禁",
                "description": "确保关键工装设备已到位",
                "is_passed": False,
                "required_conditions": ["crane_available", "sling_ready"],
                "failed_conditions": ["crane_available"],
                "passed_at": None,
                "checked_by": None
            }
        }


class MaterialItem(BaseModel):
    """物料项模型"""
    material_id: str = Field(..., description="物料ID")
    name: str = Field(..., description="物料名称")
    part_number: Optional[str] = Field(None, description="零件号")
    engine_id: str = Field(..., description="所属发动机ID")
    work_package_id: str = Field(..., description="所属工包ID")
    
    # 齐套策略
    must_kit: bool = Field(True, description="是否必须齐套")
    allow_partial: bool = Field(False, description="是否允许分段执行")
    
    # 数量信息
    required_quantity: int = Field(1, ge=1, description="需求数量")
    available_quantity: int = Field(0, ge=0, description="可用数量")
    
    # 时间信息
    eta: Optional[datetime] = Field(None, description="预计到货时间")
    actual_arrival: Optional[datetime] = Field(None, description="实际到货时间")
    
    # QEC货架信息
    qec_shelf_slot: Optional[str] = Field(None, description="QEC货架位置")
    shelf_assigned_at: Optional[datetime] = Field(None, description="货架分配时间")
    
    # 关键性
    criticality: MaterialCriticality = Field(MaterialCriticality.MEDIUM, description="关键性等级")
    
    # 状态
    is_ready: bool = Field(False, description="是否就绪")
    is_kitted: bool = Field(False, description="是否已配套")
    
    @validator('available_quantity')
    def validate_available_not_exceed_required(cls, v, values):
        """验证可用数量不超过需求数量"""
        required_quantity = values.get('required_quantity', 1)
        if v > required_quantity:
            raise ValueError("Available quantity cannot exceed required quantity")
        return v
    
    def is_sufficient(self) -> bool:
        """
        检查数量是否充足
        
        Returns:
            是否充足
        """
        if self.must_kit:
            return self.available_quantity >= self.required_quantity
        return self.available_quantity > 0
    
    def update_arrival(self, quantity: int, arrival_time: Optional[datetime] = None):
        """
        更新到货信息
        
        Args:
            quantity: 到货数量
            arrival_time: 到货时间，默认为当前时间
        """
        self.available_quantity = min(
            self.available_quantity + quantity,
            self.required_quantity
        )
        if not self.actual_arrival:
            self.actual_arrival = arrival_time or datetime.now()
        
        # 更新就绪状态
        self.is_ready = self.is_sufficient()
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "material_id": "M-001",
                "name": "发动机密封圈",
                "part_number": "PN-12345",
                "engine_id": "ENG-001",
                "work_package_id": "WP-001",
                "must_kit": True,
                "allow_partial": False,
                "required_quantity": 2,
                "available_quantity": 1,
                "eta": "2025-08-15T14:00:00Z",
                "qec_shelf_slot": "A-01-03",
                "criticality": "high",
                "is_ready": False,
                "is_kitted": False
            }
        }


class ToolAsset(BaseModel):
    """工装设备模型"""
    asset_id: str = Field(..., description="工装ID")
    name: str = Field(..., description="工装名称")
    category: AssetCategory = Field(..., description="工装类别")
    
    # 关键性
    is_critical: bool = Field(False, description="是否为关键工装")
    
    # 数量信息
    total_quantity: int = Field(1, ge=1, description="总数量")
    available_quantity: int = Field(1, ge=0, description="可用数量")
    
    # 位置信息
    current_location: Optional[str] = Field(None, description="当前位置")
    target_location: Optional[str] = Field(None, description="目标位置")
    
    # 调配信息
    allocation_eta: Optional[datetime] = Field(None, description="调配预计时间")
    allocated_at: Optional[datetime] = Field(None, description="实际调配时间")
    allocated_by: Optional[str] = Field(None, description="调配人员")
    
    # 独占性
    exclusive_group: Optional[str] = Field(None, description="独占组ID")
    
    # 日历和可用性
    calendar: Optional[Dict[str, Any]] = Field(default_factory=dict, description="可用时段")
    
    # 状态
    is_ready: bool = Field(False, description="是否就绪")
    is_allocated: bool = Field(False, description="是否已调配")
    
    @validator('available_quantity')
    def validate_available_not_exceed_total(cls, v, values):
        """验证可用数量不超过总数量"""
        total_quantity = values.get('total_quantity', 1)
        if v > total_quantity:
            raise ValueError("Available quantity cannot exceed total quantity")
        return v
    
    def allocate(self, quantity: int = 1, allocated_by: Optional[str] = None):
        """
        分配工装
        
        Args:
            quantity: 分配数量
            allocated_by: 分配人员
        """
        if quantity > self.available_quantity:
            raise ValueError(f"Cannot allocate {quantity}, only {self.available_quantity} available")
        
        self.available_quantity -= quantity
        self.is_allocated = True
        self.allocated_at = datetime.now()
        if allocated_by:
            self.allocated_by = allocated_by
        
        # 更新就绪状态
        self.is_ready = True
    
    def release(self, quantity: int = 1):
        """
        释放工装
        
        Args:
            quantity: 释放数量
        """
        self.available_quantity = min(
            self.available_quantity + quantity,
            self.total_quantity
        )
        
        if self.available_quantity == self.total_quantity:
            self.is_allocated = False
            self.allocated_at = None
            self.allocated_by = None
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "asset_id": "CRANE-1",
                "name": "行车1号",
                "category": "hoist",
                "is_critical": True,
                "total_quantity": 1,
                "available_quantity": 1,
                "current_location": "车间A",
                "target_location": "工位1",
                "allocation_eta": "2025-08-15T09:00:00Z",
                "exclusive_group": "CRANE_GROUP_A",
                "is_ready": False,
                "is_allocated": False
            }
        }


class PreparationTask(BaseModel):
    """
    准备任务模型
    
    定义准备阶段的具体任务，包括工装调配、物料配套、文档准备等。
    """
    prep_id: str = Field(..., description="准备任务ID")
    engine_id: str = Field(..., description="所属发动机ID")
    work_package_id: str = Field(..., description="所属工包ID")
    
    # 任务基本信息
    name: str = Field(..., description="任务名称")
    type: PreparationTaskType = Field(..., description="任务类型")
    description: Optional[str] = Field(None, description="任务描述")
    
    # 门禁属性
    is_gate: bool = Field(False, description="是否为门禁任务")
    gate: Optional[Gate] = Field(None, description="关联的门禁")
    
    # 依赖关系
    dependencies: List[str] = Field(default_factory=list, description="依赖的准备任务ID")
    
    # 时间约束
    earliest_start: Optional[datetime] = Field(None, description="最早开始时间")
    latest_finish: Optional[datetime] = Field(None, description="最晚完成时间")
    manual_eta: Optional[datetime] = Field(None, description="人工录入的预计时间")
    duration_hours: float = Field(1.0, gt=0, description="预计工时（小时）")
    
    # 资源需求
    required_assets: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="所需工装设备"
    )
    required_roles: List[str] = Field(default_factory=list, description="所需角色")
    
    # 证据要求
    evidence_required: List[EvidenceType] = Field(
        default_factory=list,
        description="所需证据类型"
    )
    submitted_evidence: List[Evidence] = Field(
        default_factory=list,
        description="已提交的证据"
    )
    
    # 位置信息
    area: Optional[str] = Field(None, description="执行区域")
    
    # 状态信息
    status: TaskStatus = Field(TaskStatus.NOT_STARTED, description="任务状态")
    
    # 执行信息
    assigned_to: Optional[str] = Field(None, description="分配给的人员")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")
    
    @validator('dependencies')
    def validate_no_self_dependency(cls, v, values):
        """验证不能依赖自己"""
        prep_id = values.get('prep_id')
        if prep_id and prep_id in v:
            raise ValueError(f"Preparation task {prep_id} cannot depend on itself")
        return v
    
    def submit_evidence(self, evidence: Evidence):
        """
        提交证据
        
        Args:
            evidence: 证据对象
        """
        self.submitted_evidence.append(evidence)
        
        # 检查是否所有必需证据都已提交
        submitted_types = {e.evidence_type for e in self.submitted_evidence if e.verified}
        required_types = set(self.evidence_required)
        
        if required_types.issubset(submitted_types):
            # 所有证据已提交，可以更新门禁状态
            if self.gate:
                self.gate.check_condition("evidence_complete", True)
    
    def start_task(self, assigned_to: Optional[str] = None):
        """
        开始任务
        
        Args:
            assigned_to: 分配给的人员
        """
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.now()
        if assigned_to:
            self.assigned_to = assigned_to
    
    def complete_task(self):
        """完成任务"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        
        # 更新门禁状态
        if self.gate:
            self.gate.check_condition("task_complete", True)
    
    def is_ready_to_start(self) -> bool:
        """
        检查是否可以开始
        
        Returns:
            是否可以开始
        """
        # 检查依赖任务是否完成（这里需要外部提供依赖任务状态）
        # 检查时间约束
        now = datetime.now()
        if self.earliest_start and now < self.earliest_start:
            return False
        
        return True
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "prep_id": "P-001",
                "engine_id": "ENG-001",
                "work_package_id": "WP-001",
                "name": "行车调配",
                "type": "tool_allocation",
                "description": "将行车1号调配到工位1",
                "is_gate": True,
                "dependencies": [],
                "earliest_start": "2025-08-15T08:00:00Z",
                "latest_finish": "2025-08-15T18:00:00Z",
                "duration_hours": 2.0,
                "required_assets": [{"asset_id": "CRANE-1", "quantity": 1}],
                "required_roles": ["supervisor"],
                "evidence_required": ["handover_form"],
                "area": "工位1",
                "status": "not_started"
            }
        }
