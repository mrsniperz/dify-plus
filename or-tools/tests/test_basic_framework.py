"""
基础框架测试 (Basic Framework Tests)

验证智能排程系统框架的基本功能和组件集成。

测试内容：
- 模型创建和验证
- 求解器基本功能
- 服务层接口
- API端点响应
"""

import pytest
from datetime import datetime, timedelta
from typing import List

from src.models import (
    Job, HumanResource, PhysicalResource, PreparationTask,
    Schedule, TaskInterval, ResourceAllocation
)
from src.solvers import SolverFactory, SolverConfig
from src.services import SchedulingService, SchedulingRequest
from src.core.constants import PriorityTemplate, TaskStatus
from src.utils import parse_datetime, validate_job_dependencies


class TestDataModels:
    """测试数据模型"""
    
    def test_job_model_creation(self):
        """测试工卡子项目模型创建"""
        job = Job(
            job_id="TEST-001",
            work_card_id="WC-001",
            engine_id="ENG-001",
            name="测试任务",
            base_duration_hours=4.0,
            required_resources=[],
            required_qualifications=[]
        )
        
        assert job.job_id == "TEST-001"
        assert job.base_duration_hours == 4.0
        assert job.status == TaskStatus.NOT_STARTED
    
    def test_human_resource_model(self):
        """测试人力资源模型"""
        resource = HumanResource(
            resource_id="TECH-001",
            employee_id="TECH-001",
            name="测试技师",
            qualifications=["inspector", "mechanic"]
        )
        
        assert resource.resource_id == "TECH-001"
        assert resource.has_qualification("inspector")
        assert not resource.has_qualification("pilot")
    
    def test_physical_resource_model(self):
        """测试物理资源模型"""
        resource = PhysicalResource(
            resource_id="CRANE-001",
            name="行车1号",
            is_exclusive=True,
            total_quantity=1
        )
        
        assert resource.resource_id == "CRANE-001"
        assert resource.is_exclusive
        assert resource.total_quantity == 1
    
    def test_preparation_task_model(self):
        """测试准备任务模型"""
        task = PreparationTask(
            prep_id="PREP-001",
            engine_id="ENG-001",
            work_package_id="WP-001",
            name="物料准备",
            type="material_kitting",
            duration_hours=2.0,
            is_gate=True
        )
        
        assert task.prep_id == "PREP-001"
        assert task.is_gate
        assert task.duration_hours == 2.0


class TestSolverFramework:
    """测试求解器框架"""
    
    def test_solver_factory(self):
        """测试求解器工厂"""
        config = SolverConfig(time_limit_seconds=10.0)
        solver = SolverFactory.create_solver("cpsat", config)
        
        assert solver is not None
        assert solver.config.time_limit_seconds == 10.0
    
    def test_solver_basic_workflow(self):
        """测试求解器基本工作流程"""
        # 创建测试数据
        jobs = [
            Job(
                job_id="J-001",
                work_card_id="WC-001",
                engine_id="ENG-001",
                name="任务1",
                base_duration_hours=2.0,
                required_resources=[],
                required_qualifications=[]
            ),
            Job(
                job_id="J-002",
                work_card_id="WC-001",
                engine_id="ENG-001",
                name="任务2",
                base_duration_hours=3.0,
                required_resources=[],
                required_qualifications=[],
                predecessor_jobs=["J-001"]
            )
        ]
        
        resources = [
            HumanResource(
                resource_id="TECH-001",
                employee_id="TECH-001",
                name="技师1",
                qualifications=[]
            )
        ]
        
        # 创建求解器
        config = SolverConfig(time_limit_seconds=5.0)
        solver = SolverFactory.create_solver("cpsat", config)
        
        # 测试求解器工作流程
        try:
            solver.initialize()
            solver.add_jobs(jobs)
            solver.add_resources(resources)
            solver.add_constraints({"plan_start_time": datetime.now()})
            solver.set_objective({"priority_template": "balanced"})
            
            # 验证输入
            is_valid, errors = solver.validate_input()
            assert is_valid, f"Input validation failed: {errors}"
            
            # 执行求解
            result = solver.solve()
            assert result is not None
            
        finally:
            solver.clear()


class TestServices:
    """测试服务层"""
    
    def test_scheduling_service_creation(self):
        """测试排程服务创建"""
        service = SchedulingService()
        assert service is not None
        assert service.solver_name == "cpsat"
    
    def test_scheduling_request_model(self):
        """测试排程请求模型"""
        request = SchedulingRequest(
            work_packages=[
                {
                    "work_package_id": "WP-001",
                    "engine_id": "ENG-001",
                    "jobs": ["J-001"],
                    "materials": []
                }
            ],
            assets=[
                {
                    "asset_id": "CRANE-001",
                    "category": "hoist",
                    "is_critical": True
                }
            ],
            humans=[
                {
                    "employee_id": "TECH-001",
                    "qualifications": ["inspector"]
                }
            ],
            config={
                "prep_window_days": 2,
                "objective_template": "balanced"
            }
        )
        
        assert request.work_packages[0]["work_package_id"] == "WP-001"
        assert request.config["prep_window_days"] == 2


class TestUtils:
    """测试工具函数"""
    
    def test_datetime_parsing(self):
        """测试日期时间解析"""
        dt_str = "2025-08-15T10:30:00Z"
        dt = parse_datetime(dt_str)
        
        assert dt.year == 2025
        assert dt.month == 8
        assert dt.day == 15
        assert dt.hour == 10
        assert dt.minute == 30
    
    def test_job_dependency_validation(self):
        """测试工卡依赖验证"""
        jobs = [
            Job(
                job_id="J-001",
                work_card_id="WC-001",
                engine_id="ENG-001",
                name="任务1",
                base_duration_hours=2.0,
                required_resources=[],
                required_qualifications=[]
            ),
            Job(
                job_id="J-002",
                work_card_id="WC-001",
                engine_id="ENG-001",
                name="任务2",
                base_duration_hours=3.0,
                required_resources=[],
                required_qualifications=[],
                predecessor_jobs=["J-001"]
            )
        ]
        
        is_valid, errors = validate_job_dependencies(jobs)
        assert is_valid
        assert len(errors) == 0
    
    def test_circular_dependency_detection(self):
        """测试循环依赖检测"""
        jobs = [
            Job(
                job_id="J-001",
                work_card_id="WC-001",
                engine_id="ENG-001",
                name="任务1",
                base_duration_hours=2.0,
                required_resources=[],
                required_qualifications=[],
                predecessor_jobs=["J-002"]  # 循环依赖
            ),
            Job(
                job_id="J-002",
                work_card_id="WC-001",
                engine_id="ENG-001",
                name="任务2",
                base_duration_hours=3.0,
                required_resources=[],
                required_qualifications=[],
                predecessor_jobs=["J-001"]  # 循环依赖
            )
        ]
        
        is_valid, errors = validate_job_dependencies(jobs)
        assert not is_valid
        assert len(errors) > 0
        assert "Circular dependency" in errors[0]


class TestIntegration:
    """集成测试"""
    
    def test_end_to_end_scheduling(self):
        """端到端排程测试"""
        # 创建排程服务
        service = SchedulingService()
        
        # 创建排程请求
        request = SchedulingRequest(
            work_packages=[
                {
                    "work_package_id": "WP-001",
                    "engine_id": "ENG-001",
                    "jobs": ["J-001"],
                    "materials": [
                        {
                            "material_id": "M-001",
                            "must_kit": True,
                            "allow_partial": False
                        }
                    ]
                }
            ],
            assets=[
                {
                    "asset_id": "CRANE-001",
                    "category": "hoist",
                    "is_critical": False
                }
            ],
            humans=[
                {
                    "employee_id": "TECH-001",
                    "qualifications": []
                }
            ],
            config={
                "prep_window_days": 1,
                "objective_template": "balanced",
                "solver": {
                    "time_limit_seconds": 5.0
                }
            }
        )
        
        # 执行排程
        response = service.create_schedule(request)
        
        # 验证响应
        assert response is not None
        assert response.plan_id is not None
        
        # 如果没有错误，验证排程结果
        if not response.error:
            assert response.schedule is not None
            assert response.makespan is not None
            assert len(response.preparation_tasks) >= 0
            assert len(response.gates) >= 0


if __name__ == "__main__":
    # 运行基本测试
    pytest.main([__file__, "-v"])
