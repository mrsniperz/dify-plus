#!/usr/bin/env python3
"""
增强版测试数据生成器 (Enhanced Test Data Generator)

生成包含完整资源类型的测试数据，包括：
- 人力资源 (Human Resources)
- 航材资源 (Materials)  
- 设备资源 (Equipment)
- 工具资源 (Tools)
- 工位资源 (Workspaces)

使用方法:
    python enhanced_test_data_generator.py
    python enhanced_test_data_generator.py --scenario complex
    python enhanced_test_data_generator.py --dependency-mode complex
    python enhanced_test_data_generator.py --output enhanced_test_data.json
"""

import json
import random
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List
from pathlib import Path


class EnhancedTestDataGenerator:
    """增强版测试数据生成器"""
    
    def __init__(self):
        self.material_types = [
            "发动机密封圈", "燃油喷嘴", "涡轮叶片", "压气机叶片", 
            "轴承", "齿轮", "管路接头", "传感器", "控制阀", "滤芯"
        ]
        
        self.equipment_types = [
            {"name": "发动机吊车", "type": "crane", "capacity": "5T"},
            {"name": "液压测试台", "type": "test_equipment", "capacity": "300bar"},
            {"name": "清洗设备", "type": "cleaning", "capacity": "超声波"},
            {"name": "烘干炉", "type": "heating", "capacity": "200°C"},
            {"name": "平衡机", "type": "balancing", "capacity": "动平衡"}
        ]
        
        self.tool_types = [
            "扭力扳手", "内窥镜", "测厚仪", "硬度计", "游标卡尺",
            "专用拆装工具", "密封胶枪", "压力表", "温度计", "振动仪"
        ]
        
        self.workspace_types = [
            {"name": "拆解工位", "capacity": 2, "area": "拆解区"},
            {"name": "清洗工位", "capacity": 1, "area": "清洗区"},
            {"name": "检查工位", "capacity": 3, "area": "检查区"},
            {"name": "装配工位", "capacity": 2, "area": "装配区"},
            {"name": "测试工位", "capacity": 1, "area": "测试区"}
        ]

    def generate_materials(self, num_materials: int = 10) -> List[Dict[str, Any]]:
        """生成航材资源"""
        materials = []
        
        for i in range(num_materials):
            material_name = random.choice(self.material_types)
            material = {
                "resource_id": f"MAT-{i+1:03d}",
                "resource_type": "material",
                "name": material_name,
                "description": f"用于发动机维修的{material_name}",
                "part_number": f"PN-{random.randint(10000, 99999)}",
                
                # 数量信息
                "total_quantity": random.randint(5, 50),
                "available_quantity": random.randint(1, 10),
                "required_quantity": random.randint(1, 5),
                
                # 齐套策略
                "must_kit": random.choice([True, False]),
                "allow_partial": random.choice([True, False]),
                
                # 时间信息
                "eta": (datetime.now() + timedelta(days=random.randint(-5, 10))).isoformat(),
                "lead_time_days": random.randint(1, 30),
                
                # 存储信息
                "storage_location": f"货架-{random.choice(['A', 'B', 'C'])}-{random.randint(1, 20):02d}",
                "qec_shelf_slot": f"{random.choice(['A', 'B', 'C'])}-{random.randint(1, 10):02d}-{random.randint(1, 20):02d}",
                
                # 成本信息
                "unit_cost": random.uniform(100.0, 5000.0),
                "criticality": random.choice(["high", "medium", "low"]),
                
                # 状态信息
                "is_ready": random.choice([True, False]),
                "is_kitted": random.choice([True, False]),
                "current_status": random.choice(["available", "reserved", "in_transit", "maintenance"])
            }
            materials.append(material)
        
        return materials

    def generate_equipment(self, num_equipment: int = 5) -> List[Dict[str, Any]]:
        """生成设备资源"""
        equipment_list = []
        
        for i in range(num_equipment):
            eq_info = random.choice(self.equipment_types)
            equipment = {
                "resource_id": f"EQP-{i+1:03d}",
                "resource_type": "equipment", 
                "name": eq_info["name"],
                "description": f"{eq_info['name']} - {eq_info['capacity']}",
                "model": f"Model-{random.randint(100, 999)}",
                "serial_number": f"SN-{random.randint(100000, 999999)}",
                "manufacturer": random.choice(["厂商A", "厂商B", "厂商C"]),
                
                # 容量信息
                "total_quantity": 1,
                "available_quantity": random.choice([0, 1]),
                "capacity_limits": {
                    "max_load": eq_info["capacity"],
                    "max_concurrent_jobs": 1
                },
                
                # 独占性
                "is_exclusive": True,
                "exclusive_group": f"EQP_GROUP_{eq_info['type'].upper()}",
                
                # 维护信息
                "last_maintenance": (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat(),
                "next_maintenance": (datetime.now() + timedelta(days=random.randint(30, 180))).isoformat(),
                "maintenance_interval_hours": random.randint(100, 1000),
                
                # 可用性
                "availability_schedule": {
                    "start_time": "06:00",
                    "end_time": "22:00", 
                    "working_days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
                },
                
                # 成本信息
                "hourly_cost": random.uniform(200.0, 1000.0),
                "setup_cost": random.uniform(50.0, 500.0),
                
                # 位置信息
                "location": f"车间{random.choice(['A', 'B', 'C'])}",
                "area": f"工位区域{random.randint(1, 5)}",
                
                # 状态信息
                "current_status": random.choice(["available", "busy", "maintenance", "unavailable"])
            }
            equipment_list.append(equipment)
        
        return equipment_list

    def generate_tools(self, num_tools: int = 8) -> List[Dict[str, Any]]:
        """生成工具资源"""
        tools = []
        
        for i in range(num_tools):
            tool_name = random.choice(self.tool_types)
            tool = {
                "resource_id": f"TOOL-{i+1:03d}",
                "resource_type": "tool",
                "name": tool_name,
                "description": f"专业维修用{tool_name}",
                "model": f"T-{random.randint(100, 999)}",
                
                # 数量信息
                "total_quantity": random.randint(1, 5),
                "available_quantity": random.randint(1, 3),
                
                # 校准信息
                "calibration_due": (datetime.now() + timedelta(days=random.randint(30, 365))).isoformat(),
                "calibration_interval_days": random.randint(90, 365),
                
                # 使用限制
                "max_concurrent_users": random.randint(1, 3),
                "requires_certification": random.choice([True, False]),
                
                # 成本信息
                "hourly_cost": random.uniform(10.0, 100.0),
                
                # 位置信息
                "storage_location": f"工具柜-{random.choice(['A', 'B', 'C'])}-{random.randint(1, 20)}",
                
                # 状态信息
                "current_status": random.choice(["available", "in_use", "calibration", "repair"])
            }
            tools.append(tool)
        
        return tools

    def generate_workspaces(self, num_workspaces: int = 5) -> List[Dict[str, Any]]:
        """生成工位资源"""
        workspaces = []
        
        for i, ws_info in enumerate(self.workspace_types[:num_workspaces]):
            workspace = {
                "resource_id": f"WS-{i+1:03d}",
                "resource_type": "workspace",
                "name": ws_info["name"],
                "description": f"{ws_info['name']} - 最大容量{ws_info['capacity']}个任务",
                
                # 容量信息
                "total_quantity": ws_info["capacity"],
                "available_quantity": random.randint(0, ws_info["capacity"]),
                "max_concurrent_jobs": ws_info["capacity"],
                
                # 位置信息
                "location": ws_info["area"],
                "area": ws_info["area"],
                
                # 设备配置
                "equipped_tools": [f"TOOL-{random.randint(1, 8):03d}" for _ in range(random.randint(1, 3))],
                "required_certifications": random.sample(["电气", "机械", "液压"], random.randint(1, 2)),
                
                # 可用性
                "availability_schedule": {
                    "start_time": "07:00",
                    "end_time": "19:00",
                    "working_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
                },
                
                # 成本信息
                "hourly_cost": random.uniform(50.0, 200.0),
                
                # 状态信息
                "current_status": random.choice(["available", "occupied", "maintenance"])
            }
            workspaces.append(workspace)
        
        return workspaces

    def generate_enhanced_jobs(self, work_packages: List[Dict], all_resources: Dict) -> List[Dict[str, Any]]:
        """生成增强版任务数据，包含完整的资源需求"""
        jobs = []

        for wp in work_packages:
            num_jobs = random.randint(2, 5)
            for j in range(num_jobs):
                # 生成资源需求
                required_resources = []

                # 添加航材需求
                if random.random() < 0.7:  # 70%的任务需要航材
                    material_count = random.randint(1, 3)
                    selected_materials = random.sample(all_resources["materials"],
                                                     min(material_count, len(all_resources["materials"])))
                    for mat in selected_materials:
                        required_resources.append({
                            "resource_id": mat["resource_id"],
                            "resource_type": "material",
                            "quantity": random.randint(1, mat["available_quantity"]),
                            "must_kit": mat["must_kit"],
                            "criticality": mat["criticality"]
                        })

                # 添加设备需求
                if random.random() < 0.5:  # 50%的任务需要设备
                    equipment = random.choice(all_resources["equipment"])
                    required_resources.append({
                        "resource_id": equipment["resource_id"],
                        "resource_type": "equipment",
                        "quantity": 1,
                        "exclusive": equipment["is_exclusive"],
                        "setup_time_hours": random.uniform(0.5, 2.0)
                    })

                # 添加工具需求
                tool_count = random.randint(1, 3)
                selected_tools = random.sample(all_resources["tools"],
                                             min(tool_count, len(all_resources["tools"])))
                for tool in selected_tools:
                    required_resources.append({
                        "resource_id": tool["resource_id"],
                        "resource_type": "tool",
                        "quantity": 1,
                        "requires_certification": tool["requires_certification"]
                    })

                # 添加工位需求
                workspace = random.choice(all_resources["workspaces"])
                required_resources.append({
                    "resource_id": workspace["resource_id"],
                    "resource_type": "workspace",
                    "quantity": 1,
                    "required_certifications": workspace["required_certifications"]
                })

                job = {
                    "job_id": f"{wp['work_package_id']}-JOB-{j+1:02d}",
                    "work_package_id": wp["work_package_id"],
                    "name": f"任务{j+1}",
                    "description": f"{wp['name']}的第{j+1}个任务",
                    "base_duration_hours": random.uniform(1.0, 8.0),

                    # 技能需求
                    "required_qualifications": random.sample(
                        ["电气", "机械", "液压", "燃油", "控制"],
                        random.randint(1, 3)
                    ),

                    # 增强的资源需求
                    "required_resources": required_resources,

                    # 依赖关系 (初始化为空，稍后根据dependency_mode设置)
                    "predecessor_jobs": [],

                    # 约束条件
                    "constraints": {
                        "max_parallel_resources": random.randint(2, 5),
                        "preferred_start_time": None,
                        "must_complete_by": wp["deadline"],
                        "allow_overtime": random.choice([True, False])
                    },

                    # 质量要求
                    "quality_requirements": {
                        "inspection_required": random.choice([True, False]),
                        "certification_level": random.choice(["standard", "enhanced", "critical"]),
                        "documentation_required": random.choice([True, False])
                    }
                }
                jobs.append(job)

        return jobs

    def _set_simple_dependencies(self, jobs: List[Dict[str, Any]]):
        """设置简单的顺序依赖关系"""
        # 按工作包分组
        wp_jobs = {}
        for job in jobs:
            wp_id = job['work_package_id']
            if wp_id not in wp_jobs:
                wp_jobs[wp_id] = []
            wp_jobs[wp_id].append(job)

        # 为每个工作包内的任务设置顺序依赖
        for wp_id, wp_job_list in wp_jobs.items():
            for i in range(1, len(wp_job_list)):
                wp_job_list[i]['predecessor_jobs'] = [wp_job_list[i-1]['job_id']]

    def _set_complex_dependencies(self, jobs: List[Dict[str, Any]]):
        """设置复杂的网络依赖关系"""
        # 按工作包分组
        wp_jobs = {}
        for job in jobs:
            wp_id = job['work_package_id']
            if wp_id not in wp_jobs:
                wp_jobs[wp_id] = []
            wp_jobs[wp_id].append(job)

        wp_list = list(wp_jobs.keys())

        # 为每个工作包设置不同的复杂依赖模式
        for i, (wp_id, wp_job_list) in enumerate(wp_jobs.items()):
            if len(wp_job_list) < 4:
                # 任务数量少，使用简单依赖
                self._create_sequential_dependencies(wp_job_list)
            else:
                # 任务数量多，使用复杂依赖模式
                if i % 3 == 0:
                    # 菱形依赖结构
                    self._create_diamond_dependencies(wp_job_list)
                elif i % 3 == 1:
                    # 并行分支合并结构
                    self._create_parallel_merge_dependencies(wp_job_list)
                else:
                    # 多前置任务结构
                    self._create_multi_predecessor_dependencies(wp_job_list)

        # 建立跨工作包依赖
        if len(wp_list) > 1:
            self._create_cross_package_dependencies(wp_jobs, wp_list)

    def _create_sequential_dependencies(self, jobs: List[Dict[str, Any]]):
        """创建顺序依赖关系"""
        for i in range(1, len(jobs)):
            jobs[i]['predecessor_jobs'] = [jobs[i-1]['job_id']]

    def _create_diamond_dependencies(self, jobs: List[Dict[str, Any]]):
        """创建菱形依赖结构: A -> B,C -> D"""
        if len(jobs) >= 4:
            # A -> B, A -> C
            jobs[1]['predecessor_jobs'] = [jobs[0]['job_id']]
            jobs[2]['predecessor_jobs'] = [jobs[0]['job_id']]
            # B,C -> D
            jobs[3]['predecessor_jobs'] = [jobs[1]['job_id'], jobs[2]['job_id']]
            # 剩余任务顺序依赖
            for i in range(4, len(jobs)):
                jobs[i]['predecessor_jobs'] = [jobs[i-1]['job_id']]

    def _create_parallel_merge_dependencies(self, jobs: List[Dict[str, Any]]):
        """创建并行分支合并结构"""
        if len(jobs) >= 4:
            mid = len(jobs) // 2
            # 前半部分并行
            # 后半部分依赖前半部分的多个任务
            merge_point = jobs[mid]
            merge_point['predecessor_jobs'] = [job['job_id'] for job in jobs[:mid]]
            # 剩余任务顺序依赖
            for i in range(mid + 1, len(jobs)):
                jobs[i]['predecessor_jobs'] = [jobs[i-1]['job_id']]

    def _create_multi_predecessor_dependencies(self, jobs: List[Dict[str, Any]]):
        """创建多前置任务依赖结构"""
        if len(jobs) >= 3:
            # 最后一个任务依赖前面所有任务
            jobs[-1]['predecessor_jobs'] = [job['job_id'] for job in jobs[:-1]]
            # 中间任务建立部分依赖
            for i in range(1, len(jobs) - 1):
                if i > 1:
                    jobs[i]['predecessor_jobs'] = [jobs[i-1]['job_id'], jobs[i-2]['job_id']]
                else:
                    jobs[i]['predecessor_jobs'] = [jobs[i-1]['job_id']]

    def _create_cross_package_dependencies(self, wp_jobs: Dict[str, List], wp_list: List[str]):
        """创建跨工作包依赖关系"""
        for i in range(1, len(wp_list)):
            current_wp_jobs = wp_jobs[wp_list[i]]
            prev_wp_jobs = wp_jobs[wp_list[i-1]]

            # 当前工作包的第一个任务依赖前一个工作包的最后一个任务
            if current_wp_jobs and prev_wp_jobs:
                current_wp_jobs[0]['predecessor_jobs'].append(prev_wp_jobs[-1]['job_id'])

    def generate_enhanced_test_data(self, scenario: str = "standard", dependency_mode: str = "simple") -> Dict[str, Any]:
        """生成增强版测试数据"""
        print(f"🔧 生成增强版测试数据 (场景: {scenario})...")

        # 根据场景调整数量
        if scenario == "simple":
            num_packages, num_materials, num_equipment = 2, 5, 3
        elif scenario == "complex":
            num_packages, num_materials, num_equipment = 5, 20, 8
        else:  # standard
            num_packages, num_materials, num_equipment = 3, 10, 5

        # 生成工作包
        work_packages = []
        for i in range(num_packages):
            package = {
                "work_package_id": f"WP-ENH-{i+1:03d}",
                "name": f"增强测试工作包{i+1}",
                "description": f"包含完整资源约束的第{i+1}个测试工作包",
                "priority": random.choice(["high", "medium", "low"]),
                "estimated_duration_hours": random.randint(16, 120),
                "deadline": (datetime.now() + timedelta(days=random.randint(7, 45))).isoformat(),
                "status": "pending",
                "engine_id": f"ENG-{i+1:03d}",
                "aircraft_tail": f"B-{random.randint(1000, 9999)}"
            }
            work_packages.append(package)

        # 生成所有类型的资源
        all_resources = {
            "materials": self.generate_materials(num_materials),
            "equipment": self.generate_equipment(num_equipment),
            "tools": self.generate_tools(8),
            "workspaces": self.generate_workspaces(5),
            "humans": self.generate_human_resources(5)
        }

        # 生成增强版任务
        jobs = self.generate_enhanced_jobs(work_packages, all_resources)

        # 根据dependency_mode设置依赖关系
        if dependency_mode == "simple":
            self._set_simple_dependencies(jobs)
        elif dependency_mode == "complex":
            self._set_complex_dependencies(jobs)

        # 合并所有资源
        all_resources_list = []
        for resource_type, resources in all_resources.items():
            all_resources_list.extend(resources)

        # 生成排程请求
        schedule_request = {
            "request_id": f"REQ-ENH-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "work_packages": work_packages,
            "jobs": jobs,
            "resources": all_resources_list,
            "constraints": {
                "plan_start_time": datetime.now().isoformat(),
                "plan_end_time": (datetime.now() + timedelta(days=60)).isoformat(),
                "max_working_hours_per_day": 8,
                "min_break_hours": 1,
                "max_overtime_hours_per_day": 4,
                "weekend_work_allowed": False,
                "resource_change_penalty": 100.0
            },
            "objectives": {
                "priority_template": "cost_optimized",
                "minimize_makespan": True,
                "maximize_resource_utilization": True,
                "minimize_total_cost": True,
                "minimize_material_waste": True
            }
        }

        return {
            "work_packages": work_packages,
            "jobs": jobs,
            "resources": all_resources_list,
            "materials": all_resources["materials"],
            "equipment": all_resources["equipment"],
            "tools": all_resources["tools"],
            "workspaces": all_resources["workspaces"],
            "humans": all_resources["humans"],
            "schedule_request": schedule_request,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "scenario": scenario,
                "generator_version": "1.0.0",
                "total_resources": len(all_resources_list),
                "resource_breakdown": {k: len(v) for k, v in all_resources.items()}
            }
        }

    def generate_human_resources(self, num_humans: int = 5) -> List[Dict[str, Any]]:
        """生成人力资源（保持与原有格式兼容）"""
        humans = []
        technician_names = ["张师傅", "李技师", "王工程师", "刘专家", "陈主管", "赵技师", "孙工", "周师傅"]

        for i in range(num_humans):
            name = technician_names[i] if i < len(technician_names) else f"技师{i+1}"
            human = {
                "resource_id": f"TECH-{i+1:03d}",
                "resource_type": "human",
                "employee_id": f"EMP-{i+1:03d}",
                "name": name,
                "qualifications": random.sample(
                    ["电气", "机械", "液压", "燃油", "控制"],
                    random.randint(2, 4)
                ),
                "skill_levels": {
                    skill: random.randint(1, 5)
                    for skill in ["电气", "机械", "液压", "燃油", "控制"]
                },
                "experience_years": random.uniform(1.0, 20.0),
                "performance_rating": random.uniform(3.0, 5.0),
                "availability": {
                    "start_time": "08:00",
                    "end_time": "18:00",
                    "working_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
                },
                "hourly_rate": random.uniform(50.0, 150.0),
                "max_overtime_hours": random.uniform(2.0, 6.0),
                "current_status": random.choice(["available", "busy", "on_leave"])
            }
            humans.append(human)

        return humans


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="增强版测试数据生成器")
    parser.add_argument(
        "--scenario",
        choices=["simple", "standard", "complex"],
        default="standard",
        help="测试场景复杂度"
    )
    parser.add_argument(
        "--output",
        default="enhanced_test_data.json",
        help="输出文件路径"
    )
    parser.add_argument(
        "--dependency-mode",
        choices=["simple", "complex"],
        default="simple",
        help="依赖关系复杂度: simple=顺序依赖, complex=复杂网络依赖"
    )

    args = parser.parse_args()

    print("🎯 增强版智能排程系统 - 测试数据生成器")
    print("=" * 60)

    # 创建生成器
    generator = EnhancedTestDataGenerator()

    # 生成测试数据
    test_data = generator.generate_enhanced_test_data(args.scenario, getattr(args, 'dependency_mode', 'simple'))

    # 保存到文件
    output_path = Path(args.output)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)

    # 输出统计信息
    print(f"✅ 增强版测试数据生成完成:")
    print(f"   场景复杂度: {args.scenario}")
    print(f"   工作包: {len(test_data['work_packages'])}个")
    print(f"   任务: {len(test_data['jobs'])}个")
    print(f"   总资源: {len(test_data['resources'])}个")
    print(f"     - 人力资源: {len(test_data['humans'])}个")
    print(f"     - 航材资源: {len(test_data['materials'])}个")
    print(f"     - 设备资源: {len(test_data['equipment'])}个")
    print(f"     - 工具资源: {len(test_data['tools'])}个")
    print(f"     - 工位资源: {len(test_data['workspaces'])}个")
    print(f"   数据已保存到: {output_path}")

    return 0


if __name__ == "__main__":
    exit(main())
