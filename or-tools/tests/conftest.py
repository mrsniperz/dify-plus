"""
pytest配置文件

定义测试的全局配置、夹具和工具函数。
提供测试数据生成、模拟对象创建等通用测试工具。
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import Mock

# 测试配置
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture
def sample_job_data() -> Dict[str, Any]:
    """
    示例工卡子项目数据
    
    Returns:
        包含示例Job数据的字典
    """
    return {
        "job_id": "J-001",
        "work_card_id": "WC-001",
        "engine_id": "ENG-001",
        "base_duration_hours": 4.0,
        "required_resources": [
            {"resource_id": "CRANE-1", "quantity": 1},
            {"resource_id": "TECH-001", "quantity": 1}
        ],
        "required_qualifications": ["inspector", "crane_operator"],
        "predecessor_jobs": []
    }


@pytest.fixture
def sample_resource_data() -> List[Dict[str, Any]]:
    """
    示例资源数据
    
    Returns:
        包含示例Resource数据的列表
    """
    return [
        {
            "resource_id": "CRANE-1",
            "resource_type": "equipment",
            "name": "行车1号",
            "quantity": 1,
            "calendar": {}
        },
        {
            "resource_id": "TECH-001",
            "resource_type": "human",
            "name": "技术员001",
            "employee_id": "E-001",
            "qualifications": ["inspector", "crane_operator"],
            "availability_schedule": {},
            "performance_factors": [
                {"job_type_id": "inspection", "factor": 0.9}
            ]
        }
    ]


@pytest.fixture
def sample_preparation_task_data() -> Dict[str, Any]:
    """
    示例准备任务数据
    
    Returns:
        包含示例PreparationTask数据的字典
    """
    return {
        "prep_id": "P-001",
        "engine_id": "ENG-001",
        "work_package_id": "WP-001",
        "type": "tool_allocation",
        "is_gate": True,
        "dependencies": [],
        "earliest_start": "2025-08-15T08:00:00Z",
        "latest_finish": "2025-08-15T18:00:00Z",
        "manual_eta": None,
        "required_assets": [{"asset_id": "CRANE-1", "quantity": 1}],
        "required_roles": ["supervisor"],
        "evidence_required": ["handover_form"],
        "area": "BAY-A",
        "duration_hours": 2.0
    }


@pytest.fixture
def mock_solver():
    """
    模拟求解器对象
    
    Returns:
        Mock求解器实例
    """
    solver = Mock()
    solver.solve.return_value = {
        "status": "optimal",
        "objective_value": 100.0,
        "solve_time": 1.5,
        "solution": {}
    }
    return solver


@pytest.fixture
def sample_plan_request() -> Dict[str, Any]:
    """
    示例排程计划请求数据
    
    Returns:
        包含示例PlanRequest数据的字典
    """
    return {
        "work_packages": [
            {
                "work_package_id": "WP-001",
                "engine_id": "ENG-001",
                "jobs": ["J-001", "J-002"],
                "materials": [
                    {
                        "material_id": "M-001",
                        "must_kit": True,
                        "allow_partial": False,
                        "eta": "2025-08-15T12:00:00Z"
                    }
                ]
            }
        ],
        "assets": [
            {
                "asset_id": "CRANE-1",
                "category": "hoist",
                "is_critical": True,
                "calendar": {}
            }
        ],
        "humans": [
            {
                "employee_id": "E-001",
                "qualifications": ["inspector"],
                "availability_schedule": {}
            }
        ],
        "config": {
            "prep_window_days": 2,
            "objective_template": "balanced",
            "freeze_inprogress": True
        }
    }


@pytest.fixture
def sample_event_data() -> Dict[str, Any]:
    """
    示例事件数据
    
    Returns:
        包含示例Event数据的字典
    """
    return {
        "event_id": "EV-001",
        "type": "eta_change",
        "effective_time": "2025-08-15T10:00:00Z",
        "payload": {
            "material_id": "M-001",
            "new_eta": "2025-08-15T16:00:00Z"
        },
        "policy": "replan_unstarted"
    }


@pytest.fixture
def time_utils():
    """
    时间工具函数集合
    
    Returns:
        包含时间处理工具函数的对象
    """
    class TimeUtils:
        @staticmethod
        def now() -> datetime:
            return datetime.now()
        
        @staticmethod
        def add_hours(dt: datetime, hours: float) -> datetime:
            return dt + timedelta(hours=hours)
        
        @staticmethod
        def format_iso(dt: datetime) -> str:
            return dt.isoformat() + "Z"
    
    return TimeUtils()


# 测试标记定义
def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "solver: marks tests that require OR-Tools solver"
    )


# 测试会话级别的设置
@pytest.fixture(scope="session")
def test_config():
    """
    测试配置
    
    Returns:
        测试配置字典
    """
    return {
        "test_mode": True,
        "log_level": "DEBUG",
        "solver_time_limit": 5,  # 测试时使用较短的求解时间
        "mock_external_services": True
    }
