#!/usr/bin/env python3
"""
优化的求解结果生成器

基于现有测试数据生成符合新标准的排程求解结果，包含：
- 标准化的数值格式
- 详细的资源分配信息
- 结构化的决策原因说明
- 完整的执行摘要和指标统计
"""

import json
import random
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Any, Optional
import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

def format_duration(hours: float) -> float:
    """格式化持续时间为2位小数"""
    return float(Decimal(str(hours)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

def format_cost(amount: float) -> float:
    """格式化成本为2位小数"""
    if amount == 0:
        return 0.00
    return float(Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

def format_percentage(value: float) -> float:
    """格式化百分比为1位小数"""
    return float(Decimal(str(value)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))

def format_datetime(dt: datetime) -> str:
    """格式化日期时间为标准格式"""
    return dt.strftime("%Y-%m-%dT%H:%M:%S")

class OptimizedSolutionGenerator:
    def __init__(self, test_data_path: str):
        """初始化生成器"""
        with open(test_data_path, 'r', encoding='utf-8') as f:
            self.test_data = json.load(f)
        
        # 解析测试数据
        self.work_packages = self.test_data['work_packages']
        self.jobs = self.test_data['jobs']
        self.resources = self.test_data['resources']
        
        # 创建资源查找字典
        self.resource_lookup = {r['resource_id']: r for r in self.resources}
        
        # 基准时间
        self.plan_start_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    
    def generate_optimized_solution(self) -> Dict[str, Any]:
        """生成优化的求解结果"""
        
        # 生成任务时间间隔
        task_intervals = self._generate_task_intervals()
        
        # 计算整体指标
        metrics = self._calculate_metrics(task_intervals)
        
        # 生成执行摘要
        execution_summary = self._generate_execution_summary(task_intervals, metrics)
        
        # 生成门禁状态
        gates = self._generate_gates()
        
        # 生成资源利用率
        resource_utilization = self._calculate_resource_utilization(task_intervals)
        
        # 构建完整的解决方案
        solution = {
            "plan_id": f"PLAN-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "request_id": self.test_data.get('schedule_request', {}).get('request_id', 'REQ-UNKNOWN'),
            "status": "optimal",
            "created_at": format_datetime(datetime.now()),
            "solve_time_seconds": format_duration(random.uniform(0.1, 0.5)),
            
            "execution_summary": execution_summary,
            "gates": gates,
            
            "schedule": {
                "task_intervals": task_intervals
            },
            
            "metrics": metrics,
            "resource_utilization": resource_utilization,
            
            "metadata": {
                "solver_status": "optimal",
                "solver_version": "CP-SAT 9.7",
                "constraints_count": len(self.jobs) * 5 + len(self.resources),
                "variables_count": len(self.jobs) * 3 + len(self.resources) * 2,
                "optimization_objectives": ["minimize_makespan", "minimize_cost", "maximize_utilization"]
            }
        }
        
        return solution
    
    def _generate_task_intervals(self) -> List[Dict[str, Any]]:
        """生成任务时间间隔，考虑前置任务约束"""
        intervals = []

        # 建立任务ID到任务的映射
        job_lookup = {job['job_id']: job for job in self.jobs}

        # 建立任务完成时间的映射
        task_completion_times = {}

        # 使用拓扑排序确定任务执行顺序
        sorted_jobs = self._topological_sort(self.jobs)

        for job in sorted_jobs:
            # 计算任务持续时间
            base_duration = job['base_duration_hours']
            duration_hours = format_duration(base_duration)

            # 计算考虑前置任务约束的开始时间
            start_time = self._calculate_earliest_start_time(job, task_completion_times)
            end_time = start_time + timedelta(hours=duration_hours)

            # 记录任务完成时间
            task_completion_times[job['job_id']] = end_time

            # 生成资源分配
            resource_assignments = self._generate_resource_assignments(job)

            # 计算成本分解
            cost_breakdown = self._calculate_cost_breakdown(resource_assignments, duration_hours)

            # 生成选择标准和约束状态
            selection_criteria = self._generate_selection_criteria(job, resource_assignments)
            constraint_status = self._generate_constraint_status(job, resource_assignments)

            # 检查前置任务约束状态
            predecessor_status = self._check_predecessor_constraints(job, task_completion_times)
            constraint_status.update(predecessor_status)

            # 生成选择摘要
            selection_summary = self._generate_selection_summary(selection_criteria)

            interval = {
                "task_id": job['job_id'],
                "task_name": job['name'],
                "work_package_id": job['work_package_id'],
                "task_type": "job",

                "start_time": format_datetime(start_time),
                "end_time": format_datetime(end_time),
                "duration_hours": duration_hours,
                "buffer_before_hours": format_duration(random.uniform(0.0, 0.5)),
                "buffer_after_hours": format_duration(random.uniform(0.0, 0.5)),

                "resource_assignments": resource_assignments,
                "cost_breakdown": cost_breakdown,

                "selection_summary": selection_summary,
                "selection_criteria": selection_criteria,
                "constraint_status": constraint_status,

                "status": "scheduled",
                "priority": self._get_work_package_priority(job['work_package_id']),
                "is_critical_path": self._is_on_critical_path(job, sorted_jobs),

                # 添加前置任务信息
                "predecessor_jobs": job.get('predecessor_jobs', []),
                "predecessor_constraints_met": predecessor_status.get('predecessor_constraints_met', True)
            }

            intervals.append(interval)

        return intervals

    def _topological_sort(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """使用拓扑排序确定任务执行顺序，处理前置任务约束"""
        # 建立任务映射
        job_map = {job['job_id']: job for job in jobs}

        # 计算入度
        in_degree = {job['job_id']: 0 for job in jobs}
        for job in jobs:
            for pred_id in job.get('predecessor_jobs', []):
                if pred_id in in_degree:
                    in_degree[job['job_id']] += 1

        # 找到入度为0的任务
        queue = [job_id for job_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            current_job_id = queue.pop(0)
            current_job = job_map[current_job_id]
            result.append(current_job)

            # 更新依赖当前任务的其他任务的入度
            for job in jobs:
                if current_job_id in job.get('predecessor_jobs', []):
                    in_degree[job['job_id']] -= 1
                    if in_degree[job['job_id']] == 0:
                        queue.append(job['job_id'])

        # 检查是否存在循环依赖
        if len(result) != len(jobs):
            print("⚠️  警告：检测到循环依赖，使用原始顺序")
            return jobs

        return result

    def _calculate_earliest_start_time(self, job: Dict[str, Any], task_completion_times: Dict[str, datetime]) -> datetime:
        """计算任务的最早开始时间，考虑前置任务约束"""
        predecessor_jobs = job.get('predecessor_jobs', [])

        if not predecessor_jobs:
            return self.plan_start_time

        # 找到所有前置任务的最晚完成时间
        latest_predecessor_end = self.plan_start_time
        for pred_id in predecessor_jobs:
            if pred_id in task_completion_times:
                pred_end_time = task_completion_times[pred_id]
                if pred_end_time > latest_predecessor_end:
                    latest_predecessor_end = pred_end_time

        # 添加一些缓冲时间
        buffer_hours = random.uniform(0.1, 0.5)
        return latest_predecessor_end + timedelta(hours=buffer_hours)

    def _check_predecessor_constraints(self, job: Dict[str, Any], task_completion_times: Dict[str, datetime]) -> Dict[str, bool]:
        """检查前置任务约束状态"""
        predecessor_jobs = job.get('predecessor_jobs', [])

        if not predecessor_jobs:
            return {"predecessor_constraints_met": True}

        # 检查所有前置任务是否都已完成
        all_predecessors_completed = True
        for pred_id in predecessor_jobs:
            if pred_id not in task_completion_times:
                all_predecessors_completed = False
                break

        return {
            "predecessor_constraints_met": all_predecessors_completed,
            "predecessor_count": len(predecessor_jobs),
            "predecessors_completed": len([p for p in predecessor_jobs if p in task_completion_times])
        }

    def _is_on_critical_path(self, job: Dict[str, Any], sorted_jobs: List[Dict[str, Any]]) -> bool:
        """判断任务是否在关键路径上"""
        # 简化的关键路径判断：有前置任务依赖的任务更可能在关键路径上
        predecessor_jobs = job.get('predecessor_jobs', [])

        if not predecessor_jobs:
            return random.choice([True, False])

        # 有多个前置任务的任务更可能在关键路径上
        if len(predecessor_jobs) > 1:
            return random.choice([True, True, False])  # 67% 概率
        else:
            return random.choice([True, False])  # 50% 概率

    def _generate_resource_assignments(self, job: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成资源分配信息"""
        assignments = []

        for req_resource in job['required_resources']:
            resource_id = req_resource['resource_id']
            resource = self.resource_lookup.get(resource_id)

            if not resource:
                continue

            assignment = {
                "resource_id": resource_id,
                "resource_type": resource['resource_type'],
                "resource_name": resource['name'],
                "quantity": req_resource['quantity']
            }

            # 根据资源类型添加特定信息
            if resource['resource_type'] == 'human':
                assignment.update({
                    "skill_match_score": format_percentage(random.uniform(0.8, 1.0)),
                    "hourly_cost": format_cost(resource.get('hourly_rate', random.uniform(80, 150))),
                    "total_cost": format_cost(assignment['quantity'] * resource.get('hourly_rate', 120) * job['base_duration_hours']),
                    "efficiency_factor": format_percentage(random.uniform(0.85, 1.15))
                })

            elif resource['resource_type'] == 'material':
                assignment.update({
                    "unit_cost": format_cost(resource.get('unit_cost', random.uniform(50, 500))),
                    "total_cost": format_cost(assignment['quantity'] * resource.get('unit_cost', 200)),
                    "criticality": resource.get('criticality', 'medium'),
                    "must_kit": resource.get('must_kit', False)
                })

            elif resource['resource_type'] == 'equipment':
                hourly_cost = resource.get('hourly_cost', random.uniform(100, 300))
                setup_cost = resource.get('setup_cost', random.uniform(50, 200))
                assignment.update({
                    "hourly_cost": format_cost(hourly_cost),
                    "total_cost": format_cost(hourly_cost * job['base_duration_hours'] + setup_cost),
                    "is_exclusive": resource.get('is_exclusive', True),
                    "setup_time_hours": format_duration(req_resource.get('setup_time_hours', random.uniform(0.5, 2.0)))
                })

            elif resource['resource_type'] == 'tool':
                assignment.update({
                    "calibration_valid": resource.get('calibration_due') and
                                       datetime.fromisoformat(resource['calibration_due'].replace('Z', '')) > datetime.now(),
                    "requires_certification": req_resource.get('requires_certification', False)
                })

            elif resource['resource_type'] == 'workspace':
                assignment.update({
                    "concurrent_capacity": resource.get('max_concurrent_jobs', 3),
                    "current_utilization": format_percentage(random.uniform(0.2, 0.8))
                })

            assignments.append(assignment)

        return assignments

    def _calculate_cost_breakdown(self, resource_assignments: List[Dict[str, Any]], duration_hours: float) -> Dict[str, float]:
        """计算成本分解"""
        labor_cost = 0.0
        material_cost = 0.0
        equipment_cost = 0.0

        for assignment in resource_assignments:
            cost = assignment.get('total_cost', 0.0)

            if assignment['resource_type'] == 'human':
                labor_cost += cost
            elif assignment['resource_type'] == 'material':
                material_cost += cost
            elif assignment['resource_type'] == 'equipment':
                equipment_cost += cost

        total_cost = labor_cost + material_cost + equipment_cost

        return {
            "labor_cost": format_cost(labor_cost if labor_cost > 0 else 0.00),
            "material_cost": format_cost(material_cost if material_cost > 0 else 0.00),
            "equipment_cost": format_cost(equipment_cost if equipment_cost > 0 else 0.00),
            "total_cost": format_cost(total_cost if total_cost > 0 else 0.00)
        }

    def _generate_selection_criteria(self, job: Dict[str, Any], resource_assignments: List[Dict[str, Any]]) -> Dict[str, float]:
        """生成选择标准"""
        # 计算技能匹配分数
        skill_scores = [a.get('skill_match_score', 0.9) for a in resource_assignments if 'skill_match_score' in a]
        skill_match_score = sum(skill_scores) / len(skill_scores) if skill_scores else 0.9

        return {
            "skill_match_score": format_percentage(skill_match_score),
            "cost_efficiency": format_percentage(random.uniform(0.75, 0.95)),
            "resource_availability": format_percentage(random.uniform(0.9, 1.0)),
            "time_optimality": format_percentage(random.uniform(0.85, 0.98))
        }

    def _generate_constraint_status(self, job: Dict[str, Any], resource_assignments: List[Dict[str, Any]]) -> Dict[str, bool]:
        """生成约束状态"""
        # 检查资质要求
        qualifications_met = True
        for req_qual in job.get('required_qualifications', []):
            # 简化检查：假设大部分情况下资质满足
            if random.random() < 0.1:  # 10%的概率不满足
                qualifications_met = False
                break

        # 检查材料充足性
        materials_sufficient = True
        for assignment in resource_assignments:
            if assignment['resource_type'] == 'material' and assignment.get('must_kit', False):
                # 检查齐套要求
                if random.random() < 0.05:  # 5%的概率不充足
                    materials_sufficient = False
                    break

        return {
            "qualifications_met": qualifications_met,
            "materials_sufficient": materials_sufficient,
            "equipment_available": random.choice([True, True, True, False]),  # 75%可用
            "time_feasible": True,
            "cost_within_budget": random.choice([True, True, False])  # 67%在预算内
        }

    def _generate_selection_summary(self, selection_criteria: Dict[str, float]) -> str:
        """生成选择摘要"""
        skill_score = selection_criteria['skill_match_score']
        cost_score = selection_criteria['cost_efficiency']

        if skill_score >= 0.9 and cost_score >= 0.9:
            return f"最佳匹配 (技能{skill_score:.0%} + 成本{cost_score:.0%})"
        elif skill_score >= 0.9:
            return f"技能优先 (匹配度{skill_score:.0%})"
        elif cost_score >= 0.9:
            return f"成本优化 (效率{cost_score:.0%})"
        else:
            return f"平衡选择 (技能{skill_score:.0%} + 成本{cost_score:.0%})"

    def _get_work_package_priority(self, work_package_id: str) -> str:
        """获取工作包优先级"""
        for wp in self.work_packages:
            if wp['work_package_id'] == work_package_id:
                return wp.get('priority', 'medium')
        return 'medium'

    def _generate_execution_summary(self, task_intervals: List[Dict[str, Any]], metrics: Dict[str, Any]) -> Dict[str, Any]:
        """生成执行摘要"""
        total_cost = sum(interval['cost_breakdown']['total_cost'] for interval in task_intervals)

        # 计算关键路径任务
        critical_path_tasks = [interval['task_id'] for interval in task_intervals if interval['is_critical_path']]

        return {
            "total_tasks": len(task_intervals),
            "makespan_hours": format_duration(metrics['time_metrics']['makespan_hours']),
            "total_cost": format_cost(total_cost),
            "resource_utilization_avg": format_percentage(metrics['resource_metrics']['human_utilization_avg']),
            "constraints_satisfied": all(
                interval['constraint_status']['qualifications_met'] and
                interval['constraint_status']['materials_sufficient']
                for interval in task_intervals
            ),
            "critical_path_tasks": critical_path_tasks[:3]  # 显示前3个关键路径任务
        }

    def _calculate_metrics(self, task_intervals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算整体指标"""
        if not task_intervals:
            return {}

        # 时间指标
        start_times = [datetime.fromisoformat(interval['start_time']) for interval in task_intervals]
        end_times = [datetime.fromisoformat(interval['end_time']) for interval in task_intervals]
        durations = [interval['duration_hours'] for interval in task_intervals]

        makespan_hours = (max(end_times) - min(start_times)).total_seconds() / 3600
        total_duration_hours = sum(durations)
        avg_task_duration = total_duration_hours / len(task_intervals)

        # 成本指标
        total_cost = sum(interval['cost_breakdown']['total_cost'] for interval in task_intervals)
        labor_cost = sum(interval['cost_breakdown']['labor_cost'] for interval in task_intervals)
        material_cost = sum(interval['cost_breakdown']['material_cost'] for interval in task_intervals)
        equipment_cost = sum(interval['cost_breakdown']['equipment_cost'] for interval in task_intervals)

        # 资源指标
        human_utilizations = []
        equipment_utilizations = []
        workspace_utilizations = []

        for interval in task_intervals:
            for assignment in interval['resource_assignments']:
                if assignment['resource_type'] == 'human':
                    human_utilizations.append(random.uniform(0.7, 0.9))
                elif assignment['resource_type'] == 'equipment':
                    equipment_utilizations.append(random.uniform(0.6, 0.85))
                elif assignment['resource_type'] == 'workspace':
                    workspace_utilizations.append(assignment.get('current_utilization', 0.5))

        return {
            "time_metrics": {
                "makespan_hours": format_duration(makespan_hours),
                "total_duration_hours": format_duration(total_duration_hours),
                "critical_path_length_hours": format_duration(makespan_hours),
                "average_task_duration_hours": format_duration(avg_task_duration)
            },
            "cost_metrics": {
                "total_cost": format_cost(total_cost),
                "labor_cost": format_cost(labor_cost),
                "material_cost": format_cost(material_cost),
                "equipment_cost": format_cost(equipment_cost),
                "cost_per_hour": format_cost(total_cost / makespan_hours if makespan_hours > 0 else 0)
            },
            "resource_metrics": {
                "total_resources_used": len(set(
                    assignment['resource_id']
                    for interval in task_intervals
                    for assignment in interval['resource_assignments']
                )),
                "human_utilization_avg": format_percentage(
                    sum(human_utilizations) / len(human_utilizations) if human_utilizations else 0.8
                ),
                "equipment_utilization_avg": format_percentage(
                    sum(equipment_utilizations) / len(equipment_utilizations) if equipment_utilizations else 0.75
                ),
                "workspace_utilization_avg": format_percentage(
                    sum(workspace_utilizations) / len(workspace_utilizations) if workspace_utilizations else 0.67
                )
            },
            "quality_metrics": {
                "constraints_satisfied": True,
                "optimization_score": format_percentage(random.uniform(0.85, 0.95)),
                "feasibility_margin": format_percentage(random.uniform(0.1, 0.2))
            }
        }

    def _generate_gates(self) -> List[Dict[str, Any]]:
        """生成门禁状态"""
        return [
            {
                "gate": "critical_tools_ready",
                "passed": True,
                "description": "关键工具准备完成"
            },
            {
                "gate": "materials_ready",
                "passed": True,
                "description": "航材齐套检查通过"
            },
            {
                "gate": "personnel_qualified",
                "passed": True,
                "description": "人员资质验证通过"
            },
            {
                "gate": "workspace_available",
                "passed": True,
                "description": "工位可用性确认"
            }
        ]

    def _calculate_resource_utilization(self, task_intervals: List[Dict[str, Any]]) -> Dict[str, float]:
        """计算资源利用率"""
        utilization = {}

        # 收集所有使用的资源
        resource_usage = {}
        for interval in task_intervals:
            for assignment in interval['resource_assignments']:
                resource_id = assignment['resource_id']
                if resource_id not in resource_usage:
                    resource_usage[resource_id] = []
                resource_usage[resource_id].append(interval['duration_hours'])

        # 计算每个资源的利用率
        for resource_id, durations in resource_usage.items():
            # 简化计算：基于使用时长和随机因子
            total_hours = sum(durations)
            base_utilization = min(total_hours / 8.0, 1.0)  # 假设8小时工作日
            utilization[resource_id] = format_percentage(base_utilization * random.uniform(0.8, 1.0))

        return utilization

def main():
    """主函数"""
    # 输入文件路径 - 使用复杂依赖关系的测试数据
    test_data_path = os.path.join(os.path.dirname(__file__), '..', '..', 'complex_enhanced_test_data.json')

    if not os.path.exists(test_data_path):
        print(f"❌ 测试数据文件不存在: {test_data_path}")
        return

    print("🔧 开始生成优化的求解结果...")

    # 创建生成器
    generator = OptimizedSolutionGenerator(test_data_path)

    # 生成优化的解决方案
    solution = generator.generate_optimized_solution()

    # 生成输出文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"optimized_solution_{timestamp}.json"
    output_path = os.path.join(os.path.dirname(__file__), '..', 'test_output', output_filename)

    # 保存结果
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(solution, f, indent=2, ensure_ascii=False)

    print(f"✅ 优化的求解结果已生成: {output_path}")

    # 输出统计信息
    print("\n📊 生成结果统计:")
    print(f"   计划ID: {solution['plan_id']}")
    print(f"   任务数量: {solution['execution_summary']['total_tasks']}")
    print(f"   总工期: {solution['execution_summary']['makespan_hours']} 小时")
    print(f"   总成本: ¥{solution['execution_summary']['total_cost']}")
    print(f"   平均资源利用率: {solution['execution_summary']['resource_utilization_avg']:.1%}")
    print(f"   约束满足: {'✅' if solution['execution_summary']['constraints_satisfied'] else '❌'}")

    # 验证数值格式
    print("\n🔍 数值格式验证:")
    sample_interval = solution['schedule']['task_intervals'][0]
    print(f"   持续时间格式: {sample_interval['duration_hours']} (保留2位小数)")
    print(f"   时间格式: {sample_interval['start_time']} (精确到秒)")
    print(f"   成本格式: {sample_interval['cost_breakdown']['total_cost']} (保留2位小数)")

    return output_path

if __name__ == "__main__":
    main()
