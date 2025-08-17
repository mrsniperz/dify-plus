#!/usr/bin/env python3
"""
API测试脚本 (API Test Script)

用于测试智能排程系统API接口的脚本。
包含模拟数据生成和接口测试功能。

使用方法:
    python test_api.py                    # 运行所有测试
    python test_api.py --endpoint health  # 测试特定接口
    python test_api.py --generate-data    # 生成测试数据
"""

import json
import requests
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any
import random


class APITester:
    """API测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def test_health(self) -> Dict[str, Any]:
        """测试健康检查接口"""
        print("🔍 测试健康检查接口...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            result = response.json()
            print(f"✅ 健康检查通过: {result['status']}")
            return result
        except Exception as e:
            print(f"❌ 健康检查失败: {e}")
            return {"error": str(e)}
    
    def test_root(self) -> Dict[str, Any]:
        """测试根路径接口"""
        print("🔍 测试根路径接口...")
        try:
            response = self.session.get(f"{self.base_url}/")
            response.raise_for_status()
            result = response.json()
            print(f"✅ 根路径访问成功: {result['name']}")
            return result
        except Exception as e:
            print(f"❌ 根路径访问失败: {e}")
            return {"error": str(e)}
    
    def test_info(self) -> Dict[str, Any]:
        """测试系统信息接口"""
        print("🔍 测试系统信息接口...")
        try:
            response = self.session.get(f"{self.base_url}/info")
            response.raise_for_status()
            result = response.json()
            print(f"✅ 系统信息获取成功: {result['system']['name']}")
            print(f"   功能特性: {len(result['features'])}个")
            return result
        except Exception as e:
            print(f"❌ 系统信息获取失败: {e}")
            return {"error": str(e)}
    
    def test_metrics(self) -> Dict[str, Any]:
        """测试性能指标接口"""
        print("🔍 测试性能指标接口...")
        try:
            response = self.session.get(f"{self.base_url}/metrics")
            response.raise_for_status()
            result = response.json()
            print(f"✅ 性能指标获取成功")
            if "metrics" in result:
                metrics = result["metrics"]
                print(f"   总请求数: {metrics.get('total_requests', 0)}")
                print(f"   平均响应时间: {metrics.get('average_response_time', 0):.3f}s")
            return result
        except Exception as e:
            print(f"❌ 性能指标获取失败: {e}")
            return {"error": str(e)}
    
    def test_docs(self) -> bool:
        """测试API文档接口"""
        print("🔍 测试API文档接口...")
        try:
            response = self.session.get(f"{self.base_url}/docs")
            response.raise_for_status()
            print(f"✅ API文档访问成功 (状态码: {response.status_code})")
            return True
        except Exception as e:
            print(f"❌ API文档访问失败: {e}")
            return False
    
    def test_openapi(self) -> Dict[str, Any]:
        """测试OpenAPI规范接口"""
        print("🔍 测试OpenAPI规范接口...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/openapi.json")
            response.raise_for_status()
            result = response.json()
            print(f"✅ OpenAPI规范获取成功")
            print(f"   API标题: {result.get('info', {}).get('title', 'Unknown')}")
            print(f"   API版本: {result.get('info', {}).get('version', 'Unknown')}")
            print(f"   接口数量: {len(result.get('paths', {}))}")
            return result
        except Exception as e:
            print(f"❌ OpenAPI规范获取失败: {e}")
            return {"error": str(e)}
    
    def generate_test_data(self) -> Dict[str, Any]:
        """生成测试数据"""
        print("🔧 生成测试数据...")
        
        # 生成工作包数据
        work_packages = []
        for i in range(3):
            package = {
                "work_package_id": f"WP-TEST-{i+1:03d}",
                "name": f"测试工作包{i+1}",
                "description": f"这是第{i+1}个测试工作包",
                "priority": random.choice(["high", "medium", "low"]),
                "estimated_duration_hours": random.randint(8, 72),
                "deadline": (datetime.now() + timedelta(days=random.randint(7, 30))).isoformat(),
                "status": "pending"
            }
            work_packages.append(package)
        
        # 生成任务数据
        jobs = []
        for wp in work_packages:
            num_jobs = random.randint(2, 5)
            for j in range(num_jobs):
                job = {
                    "job_id": f"{wp['work_package_id']}-JOB-{j+1:02d}",
                    "work_package_id": wp["work_package_id"],
                    "name": f"任务{j+1}",
                    "description": f"{wp['name']}的第{j+1}个任务",
                    "base_duration_hours": random.uniform(1.0, 8.0),
                    "required_qualifications": random.sample(
                        ["电气", "机械", "液压", "燃油", "控制"], 
                        random.randint(1, 3)
                    ),
                    "required_resources": [f"工具{k+1}" for k in range(random.randint(1, 3))],
                    "predecessor_jobs": [] if j == 0 else [f"{wp['work_package_id']}-JOB-{j:02d}"]
                }
                jobs.append(job)
        
        # 生成资源数据
        resources = []
        technician_names = ["张师傅", "李技师", "王工程师", "刘专家", "陈主管"]
        for i, name in enumerate(technician_names):
            resource = {
                "resource_id": f"TECH-{i+1:03d}",
                "employee_id": f"EMP-{i+1:03d}",
                "name": name,
                "qualifications": random.sample(
                    ["电气", "机械", "液压", "燃油", "控制"], 
                    random.randint(2, 4)
                ),
                "availability": {
                    "start_time": "08:00",
                    "end_time": "18:00",
                    "working_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
                },
                "hourly_rate": random.uniform(50.0, 150.0)
            }
            resources.append(resource)
        
        # 生成排程请求数据
        schedule_request = {
            "request_id": f"REQ-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "work_packages": work_packages,
            "jobs": jobs,
            "resources": resources,
            "constraints": {
                "plan_start_time": datetime.now().isoformat(),
                "plan_end_time": (datetime.now() + timedelta(days=30)).isoformat(),
                "max_working_hours_per_day": 8,
                "min_break_hours": 1
            },
            "objectives": {
                "priority_template": "balanced",
                "minimize_makespan": True,
                "maximize_resource_utilization": True
            }
        }
        
        test_data = {
            "work_packages": work_packages,
            "jobs": jobs,
            "resources": resources,
            "schedule_request": schedule_request
        }
        
        # 保存测试数据到文件
        with open("test_data.json", "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 测试数据生成完成:")
        print(f"   工作包: {len(work_packages)}个")
        print(f"   任务: {len(jobs)}个")
        print(f"   资源: {len(resources)}个")
        print(f"   数据已保存到: test_data.json")
        
        return test_data
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("🚀 开始运行API测试...")
        print("=" * 50)
        
        results = {}
        
        # 基础接口测试
        results["health"] = self.test_health()
        results["root"] = self.test_root()
        results["info"] = self.test_info()
        results["metrics"] = self.test_metrics()
        results["docs"] = self.test_docs()
        results["openapi"] = self.test_openapi()
        
        print("=" * 50)
        print("📊 测试结果汇总:")
        
        success_count = 0
        total_count = 0
        
        for test_name, result in results.items():
            total_count += 1
            if isinstance(result, dict) and "error" not in result:
                success_count += 1
                print(f"   ✅ {test_name}: 通过")
            elif isinstance(result, bool) and result:
                success_count += 1
                print(f"   ✅ {test_name}: 通过")
            else:
                print(f"   ❌ {test_name}: 失败")
        
        print(f"\n📈 总体结果: {success_count}/{total_count} 测试通过")
        
        if success_count == total_count:
            print("🎉 所有测试都通过了！API服务器运行正常。")
        else:
            print("⚠️  部分测试失败，请检查API服务器状态。")
        
        return results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="智能排程系统API测试工具")
    parser.add_argument(
        "--base-url", 
        default="http://localhost:8000",
        help="API服务器地址 (默认: http://localhost:8000)"
    )
    parser.add_argument(
        "--endpoint",
        choices=["health", "root", "info", "metrics", "docs", "openapi"],
        help="测试特定接口"
    )
    parser.add_argument(
        "--generate-data",
        action="store_true",
        help="生成测试数据"
    )
    
    args = parser.parse_args()
    
    tester = APITester(args.base_url)
    
    if args.generate_data:
        tester.generate_test_data()
    elif args.endpoint:
        method_name = f"test_{args.endpoint}"
        if hasattr(tester, method_name):
            getattr(tester, method_name)()
        else:
            print(f"❌ 未知的接口: {args.endpoint}")
    else:
        tester.run_all_tests()


if __name__ == "__main__":
    main()
