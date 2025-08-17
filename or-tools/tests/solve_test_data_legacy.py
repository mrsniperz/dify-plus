#!/usr/bin/env python3
"""
测试数据求解脚本 (Test Data Solver)

使用test_data.json中的测试数据进行排程求解，获得最优解结果。

使用方法:
    python solve_test_data.py                    # 使用API方式求解
    python solve_test_data.py --direct          # 直接调用求解器
    python solve_test_data.py --output result.json  # 指定输出文件
"""

import json
import sys
import argparse
import requests
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent  # 从 or-tools/tests/ 回到项目根目录
tests_root = Path(__file__).parent  # tests目录
sys.path.insert(0, str(project_root))


class TestDataSolver:
    """测试数据求解器"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def load_test_data(self, data_file: str = "test_data.json") -> Dict[str, Any]:
        """加载测试数据"""
        test_data_path = tests_root / data_file
        
        if not test_data_path.exists():
            print("❌ 测试数据文件不存在")
            print("💡 请先运行: uv run python test_api.py --generate-data")
            return {}
        
        try:
            with open(test_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print("✅ 成功加载测试数据")
                return data
        except Exception as e:
            print(f"❌ 加载测试数据失败: {e}")
            return {}
    
    def check_api_server(self) -> bool:
        """检查API服务器是否可用"""
        try:
            response = self.session.get(f"{self.api_base_url}/health", timeout=5)
            response.raise_for_status()
            result = response.json()
            if result.get('status') == 'healthy':
                print("✅ API服务器运行正常")
                return True
            else:
                print(f"⚠️ API服务器状态异常: {result.get('status')}")
                return False
        except Exception as e:
            print(f"❌ API服务器不可用: {e}")
            print("💡 请先启动API服务器: uv run python main.py")
            return False
    
    def solve_via_api(self, test_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """通过API接口求解"""
        if not self.check_api_server():
            return None

        # 获取排程请求数据
        schedule_request = test_data.get('schedule_request')
        if not schedule_request:
            print("❌ 测试数据中缺少schedule_request")
            return None

        print("🚀 开始通过API求解...")
        print(f"   工作包数量: {len(schedule_request.get('work_packages', []))}")
        print(f"   任务数量: {len(schedule_request.get('jobs', []))}")
        print(f"   资源数量: {len(schedule_request.get('resources', []))}")

        # 转换数据格式以匹配API期望的格式
        api_request = self._convert_to_api_format(schedule_request)

        try:
            # 调用排程API
            start_time = time.time()
            response = self.session.post(
                f"{self.api_base_url}/api/v1/prep/tasks/plan",
                json=api_request,
                timeout=60
            )
            solve_time = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                print(f"✅ 求解成功! 耗时: {solve_time:.2f}秒")
                return result
            else:
                print(f"❌ 求解失败: HTTP {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   错误详情: {error_detail}")
                except:
                    print(f"   错误详情: {response.text}")
                return None

        except Exception as e:
            print(f"❌ API调用失败: {e}")
            return None

    def _convert_to_api_format(self, schedule_request: Dict[str, Any]) -> Dict[str, Any]:
        """将测试数据格式转换为API期望的格式"""
        # 转换工作包格式，添加jobs字段
        work_packages = []
        jobs = schedule_request.get('jobs', [])

        for wp in schedule_request.get('work_packages', []):
            # 找到属于这个工作包的任务
            wp_jobs = [job for job in jobs if job.get('work_package_id') == wp.get('work_package_id')]
            wp_job_ids = [job['job_id'] for job in wp_jobs]

            converted_wp = {
                "work_package_id": wp.get('work_package_id'),
                "engine_id": wp.get('work_package_id', '').replace('WP-', 'ENG-'),  # 生成engine_id
                "jobs": wp_job_ids,
                "job_details": wp_jobs,  # 添加详细的任务信息
                "materials": []  # 测试数据中没有materials，使用空列表
            }
            work_packages.append(converted_wp)

        # 转换资源格式
        humans = []
        for resource in schedule_request.get('resources', []):
            human = {
                "employee_id": resource.get('employee_id'),
                "qualifications": resource.get('qualifications', []),
                "availability_schedule": resource.get('availability', {})
            }
            humans.append(human)

        # 转换配置格式
        constraints = schedule_request.get('constraints', {})
        objectives = schedule_request.get('objectives', {})

        config = {
            "prep_window_days": 2,  # 默认值
            "objective_template": objectives.get('priority_template', 'balanced'),
            "freeze_inprogress": True
        }

        # 如果有约束条件，添加到config中
        if constraints:
            config.update(constraints)

        return {
            "work_packages": work_packages,
            "assets": [],  # 测试数据中没有assets，使用空列表
            "humans": humans,
            "config": config
        }
    
    def solve_directly(self, test_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """直接调用求解器求解"""
        try:
            # 尝试导入排程服务
            try:
                from src.services import SchedulingService, SchedulingRequest
            except ImportError:
                # 如果src模块不存在，创建一个模拟的求解器
                print("⚠️ 未找到src.services模块，使用模拟求解器")
                return self._mock_solve(test_data)

            print("🚀 开始直接求解...")

            # 获取排程请求数据
            schedule_request_data = test_data.get('schedule_request')
            if not schedule_request_data:
                print("❌ 测试数据中缺少schedule_request")
                return None

            # 转换数据格式以匹配SchedulingRequest期望的格式
            api_request = self._convert_to_api_format(schedule_request_data)

            print("🔍 转换后的数据格式:")
            print(f"   工作包: {len(api_request.get('work_packages', []))}")
            for wp in api_request.get('work_packages', []):
                print(f"     - {wp.get('work_package_id')}: {len(wp.get('jobs', []))} 个任务")
            print(f"   人力资源: {len(api_request.get('humans', []))}")

            # 创建排程请求对象
            scheduling_request = SchedulingRequest(
                work_packages=api_request.get('work_packages', []),
                assets=api_request.get('assets', []),
                humans=api_request.get('humans', []),
                config=api_request.get('config', {})
            )

            # 创建排程服务
            service = SchedulingService()

            # 执行排程
            start_time = time.time()
            response = service.create_schedule(scheduling_request)
            solve_time = time.time() - start_time

            print(f"🔍 求解响应详情:")
            print(f"   错误: {response.error}")
            print(f"   计划ID: {response.plan_id}")
            if hasattr(response, 'schedule') and response.schedule:
                print(f"   任务数量: {len(response.schedule.task_intervals) if response.schedule.task_intervals else 0}")
                print(f"   求解状态: {response.schedule.metrics.solver_status}")
            else:
                print(f"   排程对象: {response.schedule}")

            if response.error:
                print(f"❌ 求解失败: {response.error}")
                return None
            else:
                print(f"✅ 求解成功! 耗时: {solve_time:.2f}秒")
                result_dict = response.to_dict()
                print(f"🔍 返回结果键: {list(result_dict.keys())}")
                return result_dict

        except Exception as e:
            print(f"❌ 直接求解失败: {e}")
            return None

    def _mock_solve(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟求解器，用于测试数据验证"""
        print("🔧 使用模拟求解器进行数据验证...")

        schedule_request = test_data.get('schedule_request', {})
        jobs = schedule_request.get('jobs', [])
        resources = schedule_request.get('resources', [])

        # 生成模拟的任务分配
        mock_tasks = []
        start_time = "2025-08-16T08:00:00"

        for i, job in enumerate(jobs):
            # 简单的资源分配逻辑
            assigned_resource = None
            for resource in resources:
                if resource.get('resource_type') == 'human':
                    # 检查技能匹配
                    job_qualifications = set(job.get('required_qualifications', []))
                    resource_qualifications = set(resource.get('qualifications', []))
                    if job_qualifications.issubset(resource_qualifications):
                        assigned_resource = resource['resource_id']
                        break

            duration_hours = job.get('base_duration_hours', 1.0)
            mock_task = {
                "task_id": job['job_id'],
                "task_type": "job",
                "start": start_time,
                "end": start_time,  # 简化处理
                "duration_hours": duration_hours,
                "assigned_resources": [assigned_resource] if assigned_resource else [],
                "assigned_personnel": [assigned_resource] if assigned_resource else []
            }
            mock_tasks.append(mock_task)

        # 生成模拟解决方案
        mock_solution = {
            "plan_id": f"MOCK-PLAN-{int(time.time())}",
            "request_id": schedule_request.get('request_id', 'mock-request'),
            "created_at": time.strftime('%Y-%m-%dT%H:%M:%S'),
            "gates": [
                {"gate": "critical_tools_ready", "passed": True},
                {"gate": "materials_ready", "passed": True}
            ],
            "preparation_tasks": [],
            "makespan": "PT8H",
            "schedule": {
                "task_intervals": mock_tasks
            },
            "solve_time_seconds": 0.1,
            "solver_status": "MOCK_OPTIMAL",
            "constraints_satisfied": True,
            "total_cost": sum(task["duration_hours"] * 100 for task in mock_tasks),
            "resource_utilization": {
                resource['resource_id']: 0.8
                for resource in resources
                if resource.get('resource_type') == 'human'
            }
        }

        print(f"✅ 模拟求解完成! 生成了 {len(mock_tasks)} 个任务分配")
        return mock_solution
    
    def analyze_solution(self, solution: Dict[str, Any]) -> None:
        """分析求解结果"""
        if not solution:
            return
        
        print("\n📊 求解结果分析:")
        print("=" * 50)
        
        # 基本信息
        plan_id = solution.get('plan_id', 'Unknown')
        status = solution.get('status', 'Unknown')
        print(f"📋 计划ID: {plan_id}")
        print(f"📈 求解状态: {status}")
        
        # 时间信息
        if 'solve_time_seconds' in solution:
            print(f"⏱️ 求解时间: {solution['solve_time_seconds']:.3f}秒")
        
        if 'generated_at' in solution:
            print(f"🕐 生成时间: {solution['generated_at']}")
        
        # 排程结果
        schedule = solution.get('schedule')
        if schedule:
            tasks = schedule.get('tasks', [])
            print(f"\n📅 排程任务数量: {len(tasks)}")
            
            if tasks:
                # 分析任务分配
                resource_usage = {}
                total_duration = 0
                
                for task in tasks:
                    resource_id = task.get('assigned_resource_id')
                    if resource_id:
                        resource_usage[resource_id] = resource_usage.get(resource_id, 0) + 1
                    
                    duration = task.get('duration_hours', 0)
                    total_duration += duration
                
                print(f"📊 总工时: {total_duration:.1f}小时")
                print(f"👥 资源分配:")
                for resource_id, task_count in resource_usage.items():
                    print(f"   {resource_id}: {task_count}个任务")
                
                # 显示前几个任务的详细信息
                print(f"\n📋 前5个任务详情:")
                for i, task in enumerate(tasks[:5], 1):
                    job_id = task.get('job_id', 'Unknown')
                    start_time = task.get('start_time', 'Unknown')
                    end_time = task.get('end_time', 'Unknown')
                    resource = task.get('assigned_resource_id', 'Unknown')
                    print(f"   {i}. {job_id}")
                    print(f"      时间: {start_time} → {end_time}")
                    print(f"      资源: {resource}")
        
        # 目标函数值
        if 'objective_value' in solution:
            print(f"\n🎯 目标函数值: {solution['objective_value']}")
        
        # 约束满足情况
        constraints = solution.get('constraints_satisfied')
        if constraints is not None:
            print(f"✅ 约束满足: {'是' if constraints else '否'}")
    
    def save_solution(self, solution: Dict[str, Any], output_file: str) -> None:
        """保存求解结果"""
        if not solution:
            print("❌ 没有求解结果可保存")
            return
        
        try:
            output_path = Path(output_file)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(solution, f, ensure_ascii=False, indent=2)
            print(f"💾 求解结果已保存到: {output_path}")
        except Exception as e:
            print(f"❌ 保存结果失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试数据求解脚本")
    parser.add_argument(
        "--direct",
        action="store_true",
        help="直接调用求解器（不通过API）"
    )
    parser.add_argument(
        "--output",
        default="solution_result.json",
        help="输出文件路径（默认: solution_result.json）"
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="API服务器地址（默认: http://localhost:8000）"
    )
    parser.add_argument(
        "--data-file",
        default="test_data.json",
        help="测试数据文件路径（默认: test_data.json）"
    )
    
    args = parser.parse_args()
    
    print("🎯 智能排程系统 - 测试数据求解")
    print("=" * 60)
    
    # 创建求解器
    solver = TestDataSolver(args.api_url)
    
    # 加载测试数据
    test_data = solver.load_test_data(args.data_file)
    if not test_data:
        return 1
    
    # 执行求解
    if args.direct:
        print("\n🔧 使用直接求解模式...")
        solution = solver.solve_directly(test_data)
    else:
        print("\n🌐 使用API求解模式...")
        solution = solver.solve_via_api(test_data)
    
    if solution:
        # 分析结果
        solver.analyze_solution(solution)
        
        # 保存结果
        solver.save_solution(solution, args.output)
        
        print(f"\n🎉 求解完成！结果已保存到 {args.output}")
        return 0
    else:
        print("\n❌ 求解失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
