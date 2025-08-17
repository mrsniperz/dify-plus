#!/usr/bin/env python3
"""
前置任务约束验证器
验证求解结果中的前置任务约束是否正确生效
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any


class DependencyConstraintValidator:
    """前置任务约束验证器"""
    
    def __init__(self, solution_file: str):
        self.solution_file = solution_file
        self.solution_data = None
        self.task_intervals = []
        self.task_lookup = {}
        
    def load_solution(self) -> bool:
        """加载求解结果"""
        try:
            with open(self.solution_file, 'r', encoding='utf-8') as f:
                self.solution_data = json.load(f)
            
            self.task_intervals = self.solution_data.get('schedule', {}).get('task_intervals', [])
            self.task_lookup = {task['task_id']: task for task in self.task_intervals}
            
            print(f"✅ 成功加载求解结果: {len(self.task_intervals)} 个任务")
            return True
            
        except Exception as e:
            print(f"❌ 加载求解结果失败: {e}")
            return False
    
    def validate_predecessor_constraints(self) -> Dict[str, Any]:
        """验证前置任务约束"""
        print("\n🔍 验证前置任务约束...")
        
        validation_results = {
            "total_tasks": len(self.task_intervals),
            "tasks_with_predecessors": 0,
            "constraint_violations": [],
            "constraint_satisfied": 0,
            "validation_passed": True
        }
        
        for task in self.task_intervals:
            task_id = task['task_id']
            predecessor_jobs = task.get('predecessor_jobs', [])
            
            if not predecessor_jobs:
                continue
                
            validation_results["tasks_with_predecessors"] += 1
            
            # 解析任务开始时间
            task_start_time = datetime.fromisoformat(task['start_time'])
            
            # 检查每个前置任务
            for pred_id in predecessor_jobs:
                if pred_id not in self.task_lookup:
                    violation = {
                        "task_id": task_id,
                        "violation_type": "missing_predecessor",
                        "predecessor_id": pred_id,
                        "description": f"前置任务 {pred_id} 不存在"
                    }
                    validation_results["constraint_violations"].append(violation)
                    validation_results["validation_passed"] = False
                    continue
                
                pred_task = self.task_lookup[pred_id]
                pred_end_time = datetime.fromisoformat(pred_task['end_time'])
                
                # 检查时间约束：前置任务必须在当前任务开始前完成
                if pred_end_time > task_start_time:
                    violation = {
                        "task_id": task_id,
                        "violation_type": "time_constraint_violation",
                        "predecessor_id": pred_id,
                        "task_start": task['start_time'],
                        "predecessor_end": pred_task['end_time'],
                        "description": f"前置任务 {pred_id} 在当前任务 {task_id} 开始后才完成"
                    }
                    validation_results["constraint_violations"].append(violation)
                    validation_results["validation_passed"] = False
                else:
                    validation_results["constraint_satisfied"] += 1
        
        return validation_results
    
    def analyze_dependency_structure(self) -> Dict[str, Any]:
        """分析依赖关系结构"""
        print("\n📊 分析依赖关系结构...")
        
        analysis = {
            "dependency_patterns": {},
            "critical_path_analysis": {},
            "complexity_metrics": {}
        }
        
        # 统计依赖模式
        dependency_counts = {}
        for task in self.task_intervals:
            pred_count = len(task.get('predecessor_jobs', []))
            dependency_counts[pred_count] = dependency_counts.get(pred_count, 0) + 1
        
        analysis["dependency_patterns"] = dependency_counts
        
        # 关键路径分析
        critical_tasks = [t for t in self.task_intervals if t.get('is_critical_path', False)]
        analysis["critical_path_analysis"] = {
            "total_critical_tasks": len(critical_tasks),
            "critical_task_ratio": len(critical_tasks) / len(self.task_intervals) if self.task_intervals else 0
        }
        
        # 复杂度指标
        max_predecessors = max((len(t.get('predecessor_jobs', [])) for t in self.task_intervals), default=0)
        avg_predecessors = sum(len(t.get('predecessor_jobs', [])) for t in self.task_intervals) / len(self.task_intervals) if self.task_intervals else 0
        
        analysis["complexity_metrics"] = {
            "max_predecessors_per_task": max_predecessors,
            "average_predecessors_per_task": round(avg_predecessors, 2),
            "total_dependency_relationships": sum(len(t.get('predecessor_jobs', [])) for t in self.task_intervals)
        }
        
        return analysis
    
    def print_validation_report(self, validation_results: Dict[str, Any], analysis: Dict[str, Any]):
        """打印验证报告"""
        print("\n" + "="*60)
        print("📋 前置任务约束验证报告")
        print("="*60)
        
        # 基本统计
        print(f"📊 基本统计:")
        print(f"   总任务数: {validation_results['total_tasks']}")
        print(f"   有前置任务的任务数: {validation_results['tasks_with_predecessors']}")
        print(f"   约束满足数: {validation_results['constraint_satisfied']}")
        print(f"   约束违反数: {len(validation_results['constraint_violations'])}")
        
        # 验证结果
        if validation_results["validation_passed"]:
            print(f"\n✅ 验证结果: 所有前置任务约束均正确生效")
        else:
            print(f"\n❌ 验证结果: 发现 {len(validation_results['constraint_violations'])} 个约束违反")
            
            print(f"\n🚨 约束违反详情:")
            for i, violation in enumerate(validation_results['constraint_violations'][:5], 1):
                print(f"   {i}. {violation['description']}")
                if violation['violation_type'] == 'time_constraint_violation':
                    print(f"      任务开始: {violation['task_start']}")
                    print(f"      前置任务结束: {violation['predecessor_end']}")
        
        # 依赖关系分析
        print(f"\n📈 依赖关系分析:")
        print(f"   依赖模式分布:")
        for pred_count, task_count in analysis["dependency_patterns"].items():
            print(f"     {pred_count} 个前置任务: {task_count} 个任务")
        
        print(f"   复杂度指标:")
        metrics = analysis["complexity_metrics"]
        print(f"     最大前置任务数: {metrics['max_predecessors_per_task']}")
        print(f"     平均前置任务数: {metrics['average_predecessors_per_task']}")
        print(f"     总依赖关系数: {metrics['total_dependency_relationships']}")
        
        print(f"   关键路径分析:")
        critical = analysis["critical_path_analysis"]
        print(f"     关键路径任务数: {critical['total_critical_tasks']}")
        print(f"     关键路径比例: {critical['critical_task_ratio']:.1%}")


def main():
    """主函数"""
    # 查找最新的求解结果文件
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'test_output')
    solution_files = [f for f in os.listdir(output_dir) if f.startswith('optimized_solution_') and f.endswith('.json')]
    
    if not solution_files:
        print("❌ 未找到求解结果文件")
        return
    
    # 使用最新的文件
    latest_file = max(solution_files)
    solution_path = os.path.join(output_dir, latest_file)
    
    print(f"🔍 验证求解结果: {latest_file}")
    
    # 创建验证器
    validator = DependencyConstraintValidator(solution_path)
    
    # 加载求解结果
    if not validator.load_solution():
        return
    
    # 验证前置任务约束
    validation_results = validator.validate_predecessor_constraints()
    
    # 分析依赖关系结构
    analysis = validator.analyze_dependency_structure()
    
    # 打印报告
    validator.print_validation_report(validation_results, analysis)


if __name__ == "__main__":
    main()
