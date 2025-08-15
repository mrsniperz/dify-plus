"""
数据验证工具 (Validators)

提供业务规则验证、数据格式验证、约束条件检查等功能。

主要功能：
- 业务规则验证
- 数据格式验证
- 约束条件检查
- 依赖关系验证
- 资源可用性验证
"""

import re
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timedelta

from ..models import Job, Resource, PreparationTask, HumanResource, PhysicalResource
from ..core.exceptions import ValidationError, ConstraintViolationError


def validate_job_dependencies(jobs: List[Job]) -> Tuple[bool, List[str]]:
    """
    验证工卡子项目的依赖关系
    
    检查：
    - 循环依赖
    - 无效依赖（依赖不存在的任务）
    - 自依赖
    
    Args:
        jobs: 工卡子项目列表
        
    Returns:
        (是否有效, 错误信息列表)
    """
    errors = []
    job_ids = {job.job_id for job in jobs}
    
    # 检查无效依赖
    for job in jobs:
        for pred_id in job.predecessor_jobs:
            if pred_id not in job_ids:
                errors.append(f"Job {job.job_id} depends on non-existent job {pred_id}")
        
        # 检查自依赖
        if job.job_id in job.predecessor_jobs:
            errors.append(f"Job {job.job_id} cannot depend on itself")
    
    # 检查循环依赖
    if not errors:  # 只有在没有无效依赖时才检查循环依赖
        cycle_errors = _check_circular_dependencies(jobs)
        errors.extend(cycle_errors)
    
    return len(errors) == 0, errors


def _check_circular_dependencies(jobs: List[Job]) -> List[str]:
    """检查循环依赖"""
    errors = []
    
    # 构建依赖图
    dependencies = {job.job_id: job.predecessor_jobs for job in jobs}
    
    # 使用DFS检测循环
    visited = set()
    rec_stack = set()
    
    def has_cycle(node, path):
        if node in rec_stack:
            cycle_path = path[path.index(node):] + [node]
            errors.append(f"Circular dependency detected: {' -> '.join(cycle_path)}")
            return True
        
        if node in visited:
            return False
        
        visited.add(node)
        rec_stack.add(node)
        
        for neighbor in dependencies.get(node, []):
            if has_cycle(neighbor, path + [node]):
                return True
        
        rec_stack.remove(node)
        return False
    
    for job_id in dependencies:
        if job_id not in visited:
            has_cycle(job_id, [])
    
    return errors


def validate_resource_capacity(
    resources: List[Resource],
    required_resources: Dict[str, int]
) -> Tuple[bool, List[str]]:
    """
    验证资源容量
    
    检查所需资源是否超过可用容量。
    
    Args:
        resources: 资源列表
        required_resources: 所需资源 {resource_id: quantity}
        
    Returns:
        (是否有效, 错误信息列表)
    """
    errors = []
    resource_dict = {r.resource_id: r for r in resources}
    
    for resource_id, required_qty in required_resources.items():
        if resource_id not in resource_dict:
            errors.append(f"Required resource {resource_id} not found")
            continue
        
        resource = resource_dict[resource_id]
        if required_qty > resource.total_quantity:
            errors.append(
                f"Required quantity {required_qty} exceeds available quantity "
                f"{resource.total_quantity} for resource {resource_id}"
            )
    
    return len(errors) == 0, errors


def validate_time_constraints(
    jobs: List[Job],
    preparation_tasks: List[PreparationTask],
    time_horizon_hours: float = 168.0
) -> Tuple[bool, List[str]]:
    """
    验证时间约束
    
    检查：
    - 时间窗的有效性
    - 固定时间的合理性
    - 工时的合理性
    
    Args:
        jobs: 工卡子项目列表
        preparation_tasks: 准备任务列表
        time_horizon_hours: 时间范围（小时）
        
    Returns:
        (是否有效, 错误信息列表)
    """
    errors = []
    now = datetime.now()
    max_time = now + timedelta(hours=time_horizon_hours)
    
    # 验证工卡子项目
    for job in jobs:
        # 检查工时
        if job.base_duration_hours <= 0:
            errors.append(f"Job {job.job_id} has invalid duration: {job.base_duration_hours}")
        
        if job.base_duration_hours > 24:
            errors.append(f"Job {job.job_id} duration too long: {job.base_duration_hours} hours")
        
        # 检查时间窗
        if job.earliest_start and job.latest_finish:
            if job.earliest_start >= job.latest_finish:
                errors.append(
                    f"Job {job.job_id} earliest start time is not before latest finish time"
                )
            
            # 检查时间窗是否足够容纳任务
            available_time = (job.latest_finish - job.earliest_start).total_seconds() / 3600
            if available_time < job.base_duration_hours:
                errors.append(
                    f"Job {job.job_id} time window ({available_time:.2f}h) "
                    f"is shorter than required duration ({job.base_duration_hours}h)"
                )
        
        # 检查固定时间
        if job.fixed_start:
            if job.fixed_start < now:
                errors.append(f"Job {job.job_id} fixed start time is in the past")
            
            if job.fixed_start > max_time:
                errors.append(f"Job {job.job_id} fixed start time is beyond time horizon")
    
    # 验证准备任务
    for task in preparation_tasks:
        if task.duration_hours <= 0:
            errors.append(f"Preparation task {task.prep_id} has invalid duration: {task.duration_hours}")
        
        if task.earliest_start and task.latest_finish:
            if task.earliest_start >= task.latest_finish:
                errors.append(
                    f"Preparation task {task.prep_id} earliest start time is not before latest finish time"
                )
    
    return len(errors) == 0, errors


def validate_qualification_requirements(
    jobs: List[Job],
    human_resources: List[HumanResource]
) -> Tuple[bool, List[str]]:
    """
    验证资质要求
    
    检查是否有足够的合格人员。
    
    Args:
        jobs: 工卡子项目列表
        human_resources: 人力资源列表
        
    Returns:
        (是否有效, 错误信息列表)
    """
    errors = []
    
    for job in jobs:
        if not job.required_qualifications:
            continue
        
        # 查找具备所需资质的人员
        qualified_personnel = []
        for hr in human_resources:
            if all(hr.has_qualification(qual) for qual in job.required_qualifications):
                qualified_personnel.append(hr.resource_id)
        
        if not qualified_personnel:
            errors.append(
                f"Job {job.job_id} requires qualifications {job.required_qualifications} "
                f"but no qualified personnel found"
            )
    
    return len(errors) == 0, errors


def validate_exclusive_resources(resources: List[Resource]) -> Tuple[bool, List[str]]:
    """
    验证独占资源配置
    
    检查独占资源组的配置是否合理。
    
    Args:
        resources: 资源列表
        
    Returns:
        (是否有效, 错误信息列表)
    """
    errors = []
    exclusive_groups = {}
    
    for resource in resources:
        if isinstance(resource, PhysicalResource) and resource.is_exclusive:
            group = resource.exclusive_group or resource.resource_id
            
            if group not in exclusive_groups:
                exclusive_groups[group] = []
            exclusive_groups[group].append(resource.resource_id)
    
    # 检查每个独占组
    for group, resource_ids in exclusive_groups.items():
        if len(resource_ids) > 1:
            errors.append(
                f"Exclusive group {group} contains multiple resources: {resource_ids}. "
                f"Exclusive resources should not share the same group."
            )
    
    return len(errors) == 0, errors


def validate_material_requirements(
    materials: List[Dict[str, Any]]
) -> Tuple[bool, List[str]]:
    """
    验证物料需求
    
    检查物料配置的合理性。
    
    Args:
        materials: 物料列表
        
    Returns:
        (是否有效, 错误信息列表)
    """
    errors = []
    
    for material in materials:
        material_id = material.get("material_id")
        if not material_id:
            errors.append("Material missing material_id")
            continue
        
        # 检查数量
        required_qty = material.get("required_quantity", 1)
        available_qty = material.get("available_quantity", 0)
        
        if required_qty <= 0:
            errors.append(f"Material {material_id} has invalid required quantity: {required_qty}")
        
        if available_qty < 0:
            errors.append(f"Material {material_id} has invalid available quantity: {available_qty}")
        
        # 检查齐套策略
        must_kit = material.get("must_kit", True)
        allow_partial = material.get("allow_partial", False)
        
        if must_kit and available_qty < required_qty:
            errors.append(
                f"Material {material_id} requires full kitting but insufficient quantity "
                f"(available: {available_qty}, required: {required_qty})"
            )
        
        # 检查ETA
        eta = material.get("eta")
        if eta:
            try:
                if isinstance(eta, str):
                    eta_dt = datetime.fromisoformat(eta.replace('Z', '+00:00'))
                    if eta_dt < datetime.now():
                        errors.append(f"Material {material_id} ETA is in the past")
            except ValueError:
                errors.append(f"Material {material_id} has invalid ETA format: {eta}")
    
    return len(errors) == 0, errors


def validate_work_package_structure(
    work_packages: List[Dict[str, Any]]
) -> Tuple[bool, List[str]]:
    """
    验证工包结构
    
    检查工包配置的完整性和合理性。
    
    Args:
        work_packages: 工包列表
        
    Returns:
        (是否有效, 错误信息列表)
    """
    errors = []
    work_package_ids = set()
    
    for wp in work_packages:
        wp_id = wp.get("work_package_id")
        if not wp_id:
            errors.append("Work package missing work_package_id")
            continue
        
        # 检查重复ID
        if wp_id in work_package_ids:
            errors.append(f"Duplicate work package ID: {wp_id}")
        work_package_ids.add(wp_id)
        
        # 检查发动机ID
        engine_id = wp.get("engine_id")
        if not engine_id:
            errors.append(f"Work package {wp_id} missing engine_id")
        
        # 检查工卡子项目
        jobs = wp.get("jobs", [])
        if not jobs:
            errors.append(f"Work package {wp_id} has no jobs")
        
        # 检查物料
        materials = wp.get("materials", [])
        material_errors = validate_material_requirements(materials)[1]
        errors.extend([f"Work package {wp_id}: {err}" for err in material_errors])
    
    return len(errors) == 0, errors


def validate_api_request_format(data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, List[str]]:
    """
    验证API请求格式
    
    检查必需字段和数据类型。
    
    Args:
        data: 请求数据
        required_fields: 必需字段列表
        
    Returns:
        (是否有效, 错误信息列表)
    """
    errors = []
    
    # 检查必需字段
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif data[field] is None:
            errors.append(f"Field {field} cannot be null")
    
    return len(errors) == 0, errors


def validate_id_format(id_value: str, id_type: str = "ID") -> bool:
    """
    验证ID格式
    
    检查ID是否符合命名规范。
    
    Args:
        id_value: ID值
        id_type: ID类型（用于错误信息）
        
    Returns:
        是否有效
    """
    if not id_value:
        return False
    
    # ID应该是字母数字和连字符的组合，长度在3-50之间
    pattern = r'^[A-Za-z0-9\-_]{3,50}$'
    return bool(re.match(pattern, id_value))


def validate_datetime_format(dt_str: str) -> bool:
    """
    验证日期时间格式
    
    Args:
        dt_str: 日期时间字符串
        
    Returns:
        是否有效
    """
    if not dt_str:
        return False
    
    try:
        # 尝试解析ISO格式
        if dt_str.endswith('Z'):
            datetime.fromisoformat(dt_str[:-1] + '+00:00')
        else:
            datetime.fromisoformat(dt_str)
        return True
    except ValueError:
        return False


def validate_duration_format(duration_str: str) -> bool:
    """
    验证持续时间格式
    
    Args:
        duration_str: 持续时间字符串
        
    Returns:
        是否有效
    """
    if not duration_str:
        return False
    
    # 支持ISO 8601格式 (PT4H30M) 和简单格式 (4h30m, 4.5h)
    iso_pattern = r'^PT(?:\d+(?:\.\d+)?H)?(?:\d+(?:\.\d+)?M)?(?:\d+(?:\.\d+)?S)?$'
    simple_pattern = r'^(?:\d+(?:\.\d+)?[hH])?(?:\d+(?:\.\d+)?[mM])?(?:\d+(?:\.\d+)?[sS])?$'
    number_pattern = r'^\d+(?:\.\d+)?$'
    
    return (bool(re.match(iso_pattern, duration_str.upper())) or
            bool(re.match(simple_pattern, duration_str)) or
            bool(re.match(number_pattern, duration_str)))


def validate_business_rules(
    jobs: List[Job],
    resources: List[Resource],
    preparation_tasks: List[PreparationTask],
    config: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    综合验证业务规则
    
    执行所有业务规则验证。
    
    Args:
        jobs: 工卡子项目列表
        resources: 资源列表
        preparation_tasks: 准备任务列表
        config: 配置参数
        
    Returns:
        (是否有效, 错误信息列表)
    """
    all_errors = []
    
    # 验证工卡子项目依赖
    is_valid, errors = validate_job_dependencies(jobs)
    all_errors.extend(errors)
    
    # 验证时间约束
    time_horizon = config.get("prep_window_days", 2) * 24
    is_valid, errors = validate_time_constraints(jobs, preparation_tasks, time_horizon)
    all_errors.extend(errors)
    
    # 验证人力资源资质
    human_resources = [r for r in resources if isinstance(r, HumanResource)]
    is_valid, errors = validate_qualification_requirements(jobs, human_resources)
    all_errors.extend(errors)
    
    # 验证独占资源
    is_valid, errors = validate_exclusive_resources(resources)
    all_errors.extend(errors)
    
    return len(all_errors) == 0, all_errors
