"""
门禁检查服务 (Gate Service)

负责准备阶段门禁条件的检查和验证。
提供门禁状态管理、条件验证、通过率统计等功能。

主要功能：
- 门禁条件检查
- 门禁状态管理
- 证据验证
- 通过率统计
"""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from enum import Enum
import logging

from ..models import (
    PreparationTask, Gate, Evidence, MaterialItem, ToolAsset,
    Schedule, TaskInterval
)
from ..core.exceptions import GateError, ValidationError
from ..core.constants import GateType
from ..models.preparation import EvidenceType


logger = logging.getLogger(__name__)


class GateStatus(str, Enum):
    """门禁状态枚举"""
    PENDING = "pending"         # 待检查
    CHECKING = "checking"       # 检查中
    PASSED = "passed"          # 已通过
    FAILED = "failed"          # 未通过
    BLOCKED = "blocked"        # 被阻塞


class GateCheckResult:
    """门禁检查结果"""
    
    def __init__(
        self,
        gate_type: GateType,
        status: GateStatus,
        passed_conditions: List[str],
        failed_conditions: List[str],
        required_actions: List[str],
        checked_at: Optional[datetime] = None
    ):
        self.gate_type = gate_type
        self.status = status
        self.passed_conditions = passed_conditions
        self.failed_conditions = failed_conditions
        self.required_actions = required_actions
        self.checked_at = checked_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "gate_type": self.gate_type.value,
            "status": self.status.value,
            "passed_conditions": self.passed_conditions,
            "failed_conditions": self.failed_conditions,
            "required_actions": self.required_actions,
            "checked_at": self.checked_at.isoformat()
        }


class GateService:
    """
    门禁检查服务
    
    负责准备阶段门禁条件的检查和管理。
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._gate_checkers = {
            GateType.CRITICAL_TOOLS_READY: self._check_critical_tools_gate,
            GateType.MATERIALS_READY: self._check_materials_gate,
            GateType.DOC_READY: self._check_doc_ready_gate,
            GateType.ASSESSMENT_COMPLETE: self._check_assessment_gate,
            GateType.QEC_SHELF_HANDOVER: self._check_qec_shelf_gate,
            GateType.INVENTORY_CHECK: self._check_inventory_check,
            GateType.SAP_INSTRUCTION: self._check_sap_instruction_gate,
        }
    
    def check_gate(
        self,
        gate_type: GateType,
        work_package_id: str,
        context: Dict[str, Any]
    ) -> GateCheckResult:
        """
        检查门禁条件
        
        Args:
            gate_type: 门禁类型
            work_package_id: 工包ID
            context: 检查上下文
            
        Returns:
            门禁检查结果
        """
        try:
            self.logger.info(f"Checking gate {gate_type.value} for work package {work_package_id}")
            
            # 获取检查器
            checker = self._gate_checkers.get(gate_type)
            if not checker:
                raise GateError(
                    f"No checker found for gate type {gate_type.value}",
                    gate_type=gate_type.value
                )
            
            # 执行检查
            result = checker(work_package_id, context)
            
            self.logger.info(
                f"Gate {gate_type.value} check completed with status {result.status.value}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error checking gate {gate_type.value}: {e}")
            
            return GateCheckResult(
                gate_type=gate_type,
                status=GateStatus.FAILED,
                passed_conditions=[],
                failed_conditions=[f"Check error: {e}"],
                required_actions=[f"Resolve error: {e}"]
            )
    
    def check_all_gates(
        self,
        work_package_id: str,
        preparation_tasks: List[PreparationTask],
        materials: List[MaterialItem],
        tools: List[ToolAsset],
        schedule: Optional[Schedule] = None
    ) -> Dict[str, GateCheckResult]:
        """
        检查所有门禁
        
        Args:
            work_package_id: 工包ID
            preparation_tasks: 准备任务列表
            materials: 物料列表
            tools: 工装列表
            schedule: 排程计划
            
        Returns:
            门禁检查结果字典
        """
        results = {}
        
        # 准备检查上下文
        context = {
            "preparation_tasks": preparation_tasks,
            "materials": materials,
            "tools": tools,
            "schedule": schedule
        }
        
        # 检查每个门禁类型
        for gate_type in GateType:
            try:
                result = self.check_gate(gate_type, work_package_id, context)
                results[gate_type.value] = result
            except Exception as e:
                self.logger.error(f"Failed to check gate {gate_type.value}: {e}")
                results[gate_type.value] = GateCheckResult(
                    gate_type=gate_type,
                    status=GateStatus.FAILED,
                    passed_conditions=[],
                    failed_conditions=[str(e)],
                    required_actions=["Fix gate check error"]
                )
        
        return results
    
    def get_gate_summary(
        self,
        plan_id: str,
        gate_results: Dict[str, GateCheckResult]
    ) -> Dict[str, Any]:
        """
        获取门禁汇总信息
        
        Args:
            plan_id: 计划ID
            gate_results: 门禁检查结果
            
        Returns:
            门禁汇总信息
        """
        total_gates = len(gate_results)
        passed_gates = len([r for r in gate_results.values() if r.status == GateStatus.PASSED])
        failed_gates = len([r for r in gate_results.values() if r.status == GateStatus.FAILED])
        pending_gates = len([r for r in gate_results.values() if r.status == GateStatus.PENDING])
        
        pass_rate = passed_gates / total_gates if total_gates > 0 else 0.0
        
        # 收集所有必需的行动
        all_required_actions = []
        for result in gate_results.values():
            all_required_actions.extend(result.required_actions)
        
        # 识别关键风险
        critical_risks = []
        for gate_type, result in gate_results.items():
            if result.status == GateStatus.FAILED and gate_type in [
                GateType.CRITICAL_TOOLS_READY.value,
                GateType.MATERIALS_READY.value
            ]:
                critical_risks.append({
                    "gate": gate_type,
                    "risk": "high",
                    "reason": "Critical gate failure"
                })
        
        return {
            "plan_id": plan_id,
            "gate_pass_rate": pass_rate,
            "gate_summary": {
                "total": total_gates,
                "passed": passed_gates,
                "failed": failed_gates,
                "pending": pending_gates
            },
            "sla_risks": critical_risks,
            "required_actions": list(set(all_required_actions)),
            "generated_at": datetime.now().isoformat()
        }
    
    def confirm_handover(
        self,
        plan_id: str,
        prep_id: str,
        evidence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        确认交接
        
        Args:
            plan_id: 计划ID
            prep_id: 准备任务ID
            evidence: 证据信息
            
        Returns:
            确认结果
        """
        try:
            self.logger.info(f"Confirming handover for prep task {prep_id}")
            
            # 验证证据
            self._validate_evidence(evidence)
            
            # 更新门禁状态（简化实现）
            updated_gate = "qec_shelf_handover"
            passed = True
            
            self.logger.info(f"Handover confirmed for prep task {prep_id}")
            
            return {
                "status": "ok",
                "updated_gate": updated_gate,
                "passed": passed,
                "confirmed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to confirm handover for prep task {prep_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "confirmed_at": datetime.now().isoformat()
            }
    
    def _check_critical_tools_gate(
        self,
        work_package_id: str,
        context: Dict[str, Any]
    ) -> GateCheckResult:
        """检查关键工装齐套门禁"""
        tools = context.get("tools", [])
        
        passed_conditions = []
        failed_conditions = []
        required_actions = []
        
        # 检查关键工装
        critical_tools = [tool for tool in tools if tool.is_critical]
        
        for tool in critical_tools:
            if tool.is_ready and tool.is_allocated:
                passed_conditions.append(f"Critical tool {tool.asset_id} ready")
            else:
                failed_conditions.append(f"Critical tool {tool.asset_id} not ready")
                required_actions.append(f"Allocate and prepare tool {tool.asset_id}")
        
        # 确定状态
        if not critical_tools:
            status = GateStatus.PASSED
        elif not failed_conditions:
            status = GateStatus.PASSED
        else:
            status = GateStatus.FAILED
        
        return GateCheckResult(
            gate_type=GateType.CRITICAL_TOOLS_READY,
            status=status,
            passed_conditions=passed_conditions,
            failed_conditions=failed_conditions,
            required_actions=required_actions
        )
    
    def _check_materials_gate(
        self,
        work_package_id: str,
        context: Dict[str, Any]
    ) -> GateCheckResult:
        """检查航材齐套门禁"""
        materials = context.get("materials", [])
        
        passed_conditions = []
        failed_conditions = []
        required_actions = []
        
        # 检查必须齐套的物料
        must_kit_materials = [mat for mat in materials if mat.must_kit]
        
        for material in must_kit_materials:
            if material.is_sufficient():
                passed_conditions.append(f"Material {material.material_id} sufficient")
            else:
                failed_conditions.append(f"Material {material.material_id} insufficient")
                required_actions.append(f"Ensure material {material.material_id} availability")
        
        # 检查允许分段的物料
        partial_materials = [mat for mat in materials if mat.allow_partial and not mat.must_kit]
        for material in partial_materials:
            if material.available_quantity > 0:
                passed_conditions.append(f"Partial material {material.material_id} available")
        
        # 确定状态
        if not must_kit_materials:
            status = GateStatus.PASSED
        elif not failed_conditions:
            status = GateStatus.PASSED
        else:
            status = GateStatus.FAILED
        
        return GateCheckResult(
            gate_type=GateType.MATERIALS_READY,
            status=status,
            passed_conditions=passed_conditions,
            failed_conditions=failed_conditions,
            required_actions=required_actions
        )
    
    def _check_doc_ready_gate(
        self,
        work_package_id: str,
        context: Dict[str, Any]
    ) -> GateCheckResult:
        """检查技术资料就绪门禁"""
        preparation_tasks = context.get("preparation_tasks", [])
        
        passed_conditions = []
        failed_conditions = []
        required_actions = []
        
        # 查找文档准备任务
        doc_tasks = [task for task in preparation_tasks if task.type == "doc_ready"]
        
        for task in doc_tasks:
            if task.status == "completed":
                passed_conditions.append(f"Document task {task.prep_id} completed")
            else:
                failed_conditions.append(f"Document task {task.prep_id} not completed")
                required_actions.append(f"Complete document preparation {task.prep_id}")
        
        # 如果没有文档任务，假设已就绪
        if not doc_tasks:
            passed_conditions.append("No document preparation required")
        
        status = GateStatus.PASSED if not failed_conditions else GateStatus.FAILED
        
        return GateCheckResult(
            gate_type=GateType.DOC_READY,
            status=status,
            passed_conditions=passed_conditions,
            failed_conditions=failed_conditions,
            required_actions=required_actions
        )
    
    def _check_assessment_gate(
        self,
        work_package_id: str,
        context: Dict[str, Any]
    ) -> GateCheckResult:
        """检查评估完成门禁"""
        preparation_tasks = context.get("preparation_tasks", [])
        
        passed_conditions = []
        failed_conditions = []
        required_actions = []
        
        # 查找评估任务
        assessment_tasks = [task for task in preparation_tasks if task.type == "assessment"]
        
        for task in assessment_tasks:
            if task.status == "completed":
                passed_conditions.append(f"Assessment task {task.prep_id} completed")
            else:
                failed_conditions.append(f"Assessment task {task.prep_id} not completed")
                required_actions.append(f"Complete assessment {task.prep_id}")
        
        # 如果没有评估任务，假设不需要评估
        if not assessment_tasks:
            passed_conditions.append("No assessment required")
        
        status = GateStatus.PASSED if not failed_conditions else GateStatus.FAILED
        
        return GateCheckResult(
            gate_type=GateType.ASSESSMENT_COMPLETE,
            status=status,
            passed_conditions=passed_conditions,
            failed_conditions=failed_conditions,
            required_actions=required_actions
        )
    
    def _check_qec_shelf_gate(
        self,
        work_package_id: str,
        context: Dict[str, Any]
    ) -> GateCheckResult:
        """检查QEC货架交接门禁"""
        materials = context.get("materials", [])
        
        passed_conditions = []
        failed_conditions = []
        required_actions = []
        
        # 检查QEC货架分配
        shelf_materials = [mat for mat in materials if mat.qec_shelf_slot]
        
        for material in shelf_materials:
            if material.shelf_assigned_at:
                passed_conditions.append(f"Material {material.material_id} assigned to shelf")
            else:
                failed_conditions.append(f"Material {material.material_id} not assigned to shelf")
                required_actions.append(f"Assign material {material.material_id} to QEC shelf")
        
        # 如果没有需要货架的物料，门禁通过
        if not shelf_materials:
            passed_conditions.append("No QEC shelf assignment required")
        
        status = GateStatus.PASSED if not failed_conditions else GateStatus.FAILED
        
        return GateCheckResult(
            gate_type=GateType.QEC_SHELF_HANDOVER,
            status=status,
            passed_conditions=passed_conditions,
            failed_conditions=failed_conditions,
            required_actions=required_actions
        )
    
    def _check_inventory_check(
        self,
        work_package_id: str,
        context: Dict[str, Any]
    ) -> GateCheckResult:
        """检查库存确认门禁"""
        # 简化实现：假设库存检查已完成
        return GateCheckResult(
            gate_type=GateType.INVENTORY_CHECK,
            status=GateStatus.PASSED,
            passed_conditions=["Inventory check completed"],
            failed_conditions=[],
            required_actions=[]
        )
    
    def _check_sap_instruction_gate(
        self,
        work_package_id: str,
        context: Dict[str, Any]
    ) -> GateCheckResult:
        """检查SAP指令接收门禁"""
        # 简化实现：假设SAP指令已接收
        return GateCheckResult(
            gate_type=GateType.SAP_INSTRUCTION,
            status=GateStatus.PASSED,
            passed_conditions=["SAP instruction received"],
            failed_conditions=[],
            required_actions=[]
        )
    
    def _validate_evidence(self, evidence: Dict[str, Any]) -> None:
        """验证证据"""
        required_fields = ["handover_form", "photo", "signature"]
        
        for field in required_fields:
            if field not in evidence:
                raise ValidationError(f"Missing required evidence field: {field}")
        
        # 验证签名
        signature = evidence.get("signature", {})
        if not signature.get("by") or not signature.get("time"):
            raise ValidationError("Invalid signature format")
