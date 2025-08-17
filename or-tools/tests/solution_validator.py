#!/usr/bin/env python3
"""
求解结果验证器

验证优化后的求解结果是否符合新标准要求：
- 数值格式标准化
- 资源分配信息完整性
- 输出结构合规性
- 前端解析友好性
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any, Tuple

class SolutionValidator:
    def __init__(self, solution_path: str):
        """初始化验证器"""
        with open(solution_path, 'r', encoding='utf-8') as f:
            self.solution = json.load(f)
        
        self.errors = []
        self.warnings = []
        self.stats = {}
    
    def validate_all(self) -> Tuple[bool, Dict[str, Any]]:
        """执行完整验证"""
        print("🔍 开始验证求解结果格式...")
        
        # 验证基本结构
        self._validate_basic_structure()
        
        # 验证数值格式
        self._validate_numeric_formats()
        
        # 验证时间格式
        self._validate_datetime_formats()
        
        # 验证资源分配完整性
        self._validate_resource_assignments()
        
        # 验证决策信息
        self._validate_decision_information()
        
        # 验证指标一致性
        self._validate_metrics_consistency()
        
        # 生成验证报告
        return self._generate_report()
    
    def _validate_basic_structure(self):
        """验证基本结构"""
        required_fields = [
            'plan_id', 'request_id', 'status', 'created_at', 'solve_time_seconds',
            'execution_summary', 'gates', 'schedule', 'metrics', 'resource_utilization', 'metadata'
        ]
        
        for field in required_fields:
            if field not in self.solution:
                self.errors.append(f"缺少必需字段: {field}")
        
        # 验证执行摘要结构
        if 'execution_summary' in self.solution:
            summary_fields = ['total_tasks', 'makespan_hours', 'total_cost', 'resource_utilization_avg', 'constraints_satisfied']
            for field in summary_fields:
                if field not in self.solution['execution_summary']:
                    self.errors.append(f"执行摘要缺少字段: {field}")
    
    def _validate_numeric_formats(self):
        """验证数值格式"""
        # 检查持续时间格式（保留2位小数）
        duration_pattern = re.compile(r'^\d+\.\d{1,2}$')
        cost_pattern = re.compile(r'^\d+\.\d{1,2}$')
        percentage_pattern = re.compile(r'^0\.\d{1}$|^1\.0$')
        
        task_intervals = self.solution.get('schedule', {}).get('task_intervals', [])
        
        for i, interval in enumerate(task_intervals):
            # 验证持续时间格式
            duration = interval.get('duration_hours', 0)
            if isinstance(duration, (int, float)):
                duration_str = f"{duration:.2f}"
                if not duration_pattern.match(duration_str):
                    self.errors.append(f"任务{i+1}持续时间格式错误: {duration} (应为X.XX格式)")

            # 验证成本格式
            cost_breakdown = interval.get('cost_breakdown', {})
            for cost_type, cost_value in cost_breakdown.items():
                if isinstance(cost_value, (int, float)):
                    cost_str = f"{cost_value:.2f}"
                    if not cost_pattern.match(cost_str):
                        self.errors.append(f"任务{i+1}成本格式错误 ({cost_type}): {cost_value} (应为X.XX格式)")
            
            # 验证选择标准格式
            selection_criteria = interval.get('selection_criteria', {})
            for criteria, value in selection_criteria.items():
                value_str = str(value)
                if not percentage_pattern.match(value_str):
                    self.warnings.append(f"任务{i+1}选择标准格式建议优化 ({criteria}): {value_str}")
    
    def _validate_datetime_formats(self):
        """验证日期时间格式"""
        datetime_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$')
        
        # 验证顶级时间字段
        datetime_fields = ['created_at']
        for field in datetime_fields:
            if field in self.solution:
                dt_str = self.solution[field]
                if not datetime_pattern.match(dt_str):
                    self.errors.append(f"时间格式错误 ({field}): {dt_str} (应为YYYY-MM-DDTHH:MM:SS格式)")
        
        # 验证任务时间字段
        task_intervals = self.solution.get('schedule', {}).get('task_intervals', [])
        for i, interval in enumerate(task_intervals):
            for time_field in ['start_time', 'end_time']:
                if time_field in interval:
                    dt_str = interval[time_field]
                    if not datetime_pattern.match(dt_str):
                        self.errors.append(f"任务{i+1}时间格式错误 ({time_field}): {dt_str}")
    
    def _validate_resource_assignments(self):
        """验证资源分配完整性"""
        task_intervals = self.solution.get('schedule', {}).get('task_intervals', [])
        
        resource_types_found = set()
        total_assignments = 0
        
        for i, interval in enumerate(task_intervals):
            assignments = interval.get('resource_assignments', [])
            total_assignments += len(assignments)
            
            for j, assignment in enumerate(assignments):
                # 验证必需字段
                required_fields = ['resource_id', 'resource_type', 'resource_name', 'quantity']
                for field in required_fields:
                    if field not in assignment:
                        self.errors.append(f"任务{i+1}资源分配{j+1}缺少字段: {field}")
                
                resource_type = assignment.get('resource_type')
                if resource_type:
                    resource_types_found.add(resource_type)
                    
                    # 验证特定资源类型的字段
                    if resource_type == 'human':
                        if 'skill_match_score' not in assignment:
                            self.warnings.append(f"任务{i+1}人力资源缺少技能匹配分数")
                    elif resource_type == 'material':
                        if 'unit_cost' not in assignment:
                            self.warnings.append(f"任务{i+1}航材资源缺少单价信息")
                    elif resource_type == 'equipment':
                        if 'is_exclusive' not in assignment:
                            self.warnings.append(f"任务{i+1}设备资源缺少独占性信息")
        
        self.stats['resource_types_found'] = list(resource_types_found)
        self.stats['total_assignments'] = total_assignments
    
    def _validate_decision_information(self):
        """验证决策信息"""
        task_intervals = self.solution.get('schedule', {}).get('task_intervals', [])
        
        for i, interval in enumerate(task_intervals):
            # 验证选择摘要
            if 'selection_summary' not in interval:
                self.warnings.append(f"任务{i+1}缺少选择摘要")
            
            # 验证选择标准
            selection_criteria = interval.get('selection_criteria', {})
            expected_criteria = ['skill_match_score', 'cost_efficiency', 'resource_availability', 'time_optimality']
            for criteria in expected_criteria:
                if criteria not in selection_criteria:
                    self.warnings.append(f"任务{i+1}缺少选择标准: {criteria}")
            
            # 验证约束状态
            constraint_status = interval.get('constraint_status', {})
            expected_constraints = ['qualifications_met', 'materials_sufficient', 'equipment_available', 'time_feasible', 'cost_within_budget']
            for constraint in expected_constraints:
                if constraint not in constraint_status:
                    self.warnings.append(f"任务{i+1}缺少约束状态: {constraint}")
    
    def _validate_metrics_consistency(self):
        """验证指标一致性"""
        metrics = self.solution.get('metrics', {})
        execution_summary = self.solution.get('execution_summary', {})
        
        # 验证工期一致性
        metrics_makespan = metrics.get('time_metrics', {}).get('makespan_hours')
        summary_makespan = execution_summary.get('makespan_hours')
        
        if metrics_makespan != summary_makespan:
            self.errors.append(f"工期数据不一致: metrics={metrics_makespan}, summary={summary_makespan}")
        
        # 验证成本一致性
        metrics_cost = metrics.get('cost_metrics', {}).get('total_cost')
        summary_cost = execution_summary.get('total_cost')
        
        if metrics_cost != summary_cost:
            self.errors.append(f"成本数据不一致: metrics={metrics_cost}, summary={summary_cost}")
    
    def _generate_report(self) -> Tuple[bool, Dict[str, Any]]:
        """生成验证报告"""
        is_valid = len(self.errors) == 0
        
        report = {
            'is_valid': is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'stats': self.stats,
            'summary': {
                'total_errors': len(self.errors),
                'total_warnings': len(self.warnings),
                'validation_status': '✅ 通过' if is_valid else '❌ 失败'
            }
        }
        
        return is_valid, report

def main():
    """主函数"""
    import os
    import glob
    
    # 查找最新的优化求解结果文件
    pattern = os.path.join(os.path.dirname(__file__), 'optimized_solution_*.json')
    solution_files = glob.glob(pattern)
    
    if not solution_files:
        print("❌ 未找到优化求解结果文件")
        return
    
    # 选择最新的文件
    latest_file = max(solution_files, key=os.path.getctime)
    print(f"📁 验证文件: {os.path.basename(latest_file)}")
    
    # 执行验证
    validator = SolutionValidator(latest_file)
    is_valid, report = validator.validate_all()
    
    # 输出验证结果
    print(f"\n📊 验证结果: {report['summary']['validation_status']}")
    print(f"   错误数量: {report['summary']['total_errors']}")
    print(f"   警告数量: {report['summary']['total_warnings']}")
    
    if report['errors']:
        print("\n❌ 发现的错误:")
        for error in report['errors']:
            print(f"   • {error}")
    
    if report['warnings']:
        print("\n⚠️ 发现的警告:")
        for warning in report['warnings']:
            print(f"   • {warning}")
    
    print(f"\n📈 统计信息:")
    print(f"   资源类型覆盖: {', '.join(report['stats'].get('resource_types_found', []))}")
    print(f"   总资源分配数: {report['stats'].get('total_assignments', 0)}")
    
    return is_valid

if __name__ == "__main__":
    main()
