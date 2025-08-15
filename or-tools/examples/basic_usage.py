#!/usr/bin/env python3
"""
基础使用示例 (Basic Usage Examples)

演示如何使用智能排程系统的API和测试数据。

使用方法:
    python examples/basic_usage.py
"""

import json
import requests
import sys
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class SchedulingAPIClient:
    """智能排程系统API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def check_health(self) -> Dict[str, Any]:
        """检查系统健康状态"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            response = self.session.get(f"{self.base_url}/info")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        try:
            response = self.session.get(f"{self.base_url}/metrics")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}


def load_test_data() -> Dict[str, Any]:
    """加载测试数据"""
    test_data_path = project_root / "test_data.json"
    
    if not test_data_path.exists():
        print("❌ 测试数据文件不存在，请先运行: uv run python test_api.py --generate-data")
        return {}
    
    try:
        with open(test_data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 加载测试数据失败: {e}")
        return {}


def analyze_test_data(test_data: Dict[str, Any]) -> None:
    """分析测试数据"""
    if not test_data:
        return
    
    print("📊 测试数据分析:")
    print("=" * 50)
    
    # 分析工作包
    work_packages = test_data.get('work_packages', [])
    print(f"📦 工作包数量: {len(work_packages)}")
    
    if work_packages:
        priorities = {}
        total_hours = 0
        
        for wp in work_packages:
            priority = wp.get('priority', 'unknown')
            priorities[priority] = priorities.get(priority, 0) + 1
            total_hours += wp.get('estimated_duration_hours', 0)
        
        print(f"   优先级分布: {priorities}")
        print(f"   总预估工时: {total_hours}小时")
    
    # 分析任务
    jobs = test_data.get('jobs', [])
    print(f"\n🔧 任务数量: {len(jobs)}")
    
    if jobs:
        total_duration = sum(job.get('base_duration_hours', 0) for job in jobs)
        avg_duration = total_duration / len(jobs) if jobs else 0
        
        # 统计技能需求
        all_qualifications = []
        for job in jobs:
            all_qualifications.extend(job.get('required_qualifications', []))
        
        qualification_counts = {}
        for qual in all_qualifications:
            qualification_counts[qual] = qualification_counts.get(qual, 0) + 1
        
        print(f"   总任务工时: {total_duration:.1f}小时")
        print(f"   平均任务工时: {avg_duration:.1f}小时")
        print(f"   技能需求统计: {qualification_counts}")
    
    # 分析资源
    resources = test_data.get('resources', [])
    print(f"\n👥 资源数量: {len(resources)}")
    
    if resources:
        # 统计技能覆盖
        all_skills = set()
        for resource in resources:
            all_skills.update(resource.get('qualifications', []))
        
        print(f"   技能覆盖: {sorted(all_skills)}")
        print(f"   平均技能数: {sum(len(r.get('qualifications', [])) for r in resources) / len(resources):.1f}")


def demonstrate_api_usage() -> None:
    """演示API使用"""
    print("🚀 API使用演示:")
    print("=" * 50)
    
    client = SchedulingAPIClient()
    
    # 健康检查
    print("🔍 检查系统健康状态...")
    health = client.check_health()
    if "error" in health:
        print(f"❌ 健康检查失败: {health['error']}")
        print("💡 请确保API服务器正在运行: uv run python main.py")
        return
    else:
        print(f"✅ 系统状态: {health.get('status', 'unknown')}")
    
    # 系统信息
    print("\n📋 获取系统信息...")
    info = client.get_system_info()
    if "error" not in info:
        system = info.get('system', {})
        features = info.get('features', [])
        print(f"✅ 系统名称: {system.get('name', 'Unknown')}")
        print(f"   系统版本: {system.get('version', 'Unknown')}")
        print(f"   功能特性: {len(features)}个")
        for i, feature in enumerate(features[:3], 1):
            print(f"   {i}. {feature}")
        if len(features) > 3:
            print(f"   ... 还有{len(features) - 3}个功能")
    
    # 性能指标
    print("\n📊 获取性能指标...")
    metrics = client.get_metrics()
    if "error" not in metrics:
        metric_data = metrics.get('metrics', {})
        print(f"✅ 总请求数: {metric_data.get('total_requests', 0)}")
        print(f"   平均响应时间: {metric_data.get('average_response_time', 0):.3f}秒")
        print(f"   错误请求数: {metric_data.get('error_requests', 0)}")


def show_usage_tips() -> None:
    """显示使用提示"""
    print("\n💡 使用提示:")
    print("=" * 50)
    print("1. 启动API服务器:")
    print("   uv run python main.py")
    print()
    print("2. 生成测试数据:")
    print("   uv run python test_api.py --generate-data")
    print()
    print("3. 运行API测试:")
    print("   uv run python test_api.py")
    print()
    print("4. 查看API文档:")
    print("   http://localhost:8000/docs")
    print()
    print("5. 前端开发配置:")
    print("   API地址: http://localhost:8000")
    print("   支持CORS: localhost:3000, localhost:8080")


def main():
    """主函数"""
    print("🎯 智能排程系统 - 基础使用示例")
    print("=" * 60)
    
    # 演示API使用
    demonstrate_api_usage()
    
    # 加载和分析测试数据
    print("\n" + "=" * 60)
    test_data = load_test_data()
    analyze_test_data(test_data)
    
    # 显示使用提示
    print("\n" + "=" * 60)
    show_usage_tips()
    
    print("\n🎉 示例演示完成！")


if __name__ == "__main__":
    main()
