#!/usr/bin/env python3
"""
智能排程系统主入口 (Main Entry Point)

基于Google OR-Tools CP-SAT的发动机QEC维修计划智能调度引擎。

使用方法:
    python main.py                    # 启动API服务器
    python main.py --help            # 显示帮助信息
    python main.py --config-check    # 检查配置
    python main.py --test-solver     # 测试求解器

环境变量:
    ENVIRONMENT: 运行环境 (development/testing/staging/production)
    DEBUG: 调试模式 (true/false)
    API_HOST: API服务器地址 (默认: 0.0.0.0)
    API_PORT: API服务器端口 (默认: 8000)
"""

import sys
import argparse
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import get_settings
from src.utils import setup_logging, get_logger
from src.api import create_app


def setup_argument_parser() -> argparse.ArgumentParser:
    """设置命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="智能排程系统 - 基于OR-Tools的发动机QEC维修计划智能调度引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                    # 启动API服务器
  python main.py --port 8080       # 在端口8080启动服务器
  python main.py --config-check    # 检查配置
  python main.py --test-solver     # 测试求解器
  python main.py --environment production  # 在生产环境启动

环境变量:
  ENVIRONMENT=development|testing|staging|production
  DEBUG=true|false
  API_HOST=0.0.0.0
  API_PORT=8000
  LOG_LEVEL=INFO|DEBUG|WARNING|ERROR
        """
    )
    
    # 服务器选项
    parser.add_argument(
        "--host",
        type=str,
        help="API服务器地址 (默认从配置获取)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        help="API服务器端口 (默认从配置获取)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="启用自动重载 (仅开发环境)"
    )
    
    # 环境选项
    parser.add_argument(
        "--environment",
        choices=["development", "testing", "staging", "production"],
        help="运行环境"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用调试模式"
    )
    
    # 工具选项
    parser.add_argument(
        "--config-check",
        action="store_true",
        help="检查配置并退出"
    )
    
    parser.add_argument(
        "--test-solver",
        action="store_true",
        help="测试求解器并退出"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="智能排程系统 v0.1.0"
    )
    
    return parser


def check_configuration() -> bool:
    """
    检查系统配置
    
    Returns:
        配置是否有效
    """
    try:
        settings = get_settings()
        logger = get_logger("config_check")
        
        logger.info("检查系统配置...")
        
        # 检查基本配置
        logger.info(f"应用名称: {settings.app_name}")
        logger.info(f"应用版本: {settings.app_version}")
        logger.info(f"运行环境: {settings.environment}")
        logger.info(f"调试模式: {settings.debug}")
        
        # 检查API配置
        api_config = settings.get_api_config()
        logger.info(f"API地址: {api_config['host']}:{api_config['port']}")
        logger.info(f"CORS源: {api_config['cors_origins']}")
        
        # 检查求解器配置
        solver_config = settings.get_solver_config()
        logger.info(f"默认求解器: {solver_config['default_solver']}")
        logger.info(f"求解时间限制: {solver_config['time_limit_seconds']}秒")
        logger.info(f"搜索工作线程: {solver_config['num_search_workers']}")
        
        # 检查业务配置
        business_config = settings.get_business_config()
        logger.info(f"默认策略模板: {business_config['default_priority_template']}")
        logger.info(f"准备窗口: {business_config['default_prep_window_days']}天")
        
        logger.info("✅ 配置检查通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 配置检查失败: {e}")
        return False


def test_solver() -> bool:
    """
    测试求解器
    
    Returns:
        求解器是否正常工作
    """
    try:
        from src.solvers import SolverFactory, SolverConfig
        from src.models import Job, HumanResource
        
        logger = get_logger("solver_test")
        logger.info("测试求解器...")
        
        # 创建测试数据
        jobs = [
            Job(
                job_id="TEST-001",
                work_card_id="WC-TEST",
                engine_id="ENG-TEST",
                name="测试任务1",
                base_duration_hours=2.0,
                required_resources=[],
                required_qualifications=[]
            ),
            Job(
                job_id="TEST-002",
                work_card_id="WC-TEST",
                engine_id="ENG-TEST",
                name="测试任务2",
                base_duration_hours=3.0,
                required_resources=[],
                required_qualifications=[],
                predecessor_jobs=["TEST-001"]
            )
        ]
        
        resources = [
            HumanResource(
                resource_id="TECH-TEST",
                employee_id="TECH-TEST",
                name="测试技师",
                qualifications=[]
            )
        ]
        
        # 创建求解器
        config = SolverConfig(time_limit_seconds=10.0)
        solver = SolverFactory.create_solver("cpsat", config)
        
        # 测试求解
        with solver:
            solver.add_jobs(jobs)
            solver.add_resources(resources)
            solver.add_constraints({"plan_start_time": "2025-08-15T08:00:00Z"})
            solver.set_objective({"priority_template": "balanced"})
            
            result = solver.solve()
            
            if result.is_successful():
                logger.info(f"✅ 求解器测试通过 - 状态: {result.status}, 求解时间: {result.solve_time_seconds:.3f}秒")
                return True
            else:
                logger.error(f"❌ 求解器测试失败 - 状态: {result.status}")
                return False
        
    except Exception as e:
        logger.error(f"❌ 求解器测试失败: {e}")
        return False


async def start_server(host: str, port: int, reload: bool = False) -> None:
    """
    启动API服务器
    
    Args:
        host: 服务器地址
        port: 服务器端口
        reload: 是否启用自动重载
    """
    import uvicorn
    
    logger = get_logger("server")
    logger.info(f"启动智能排程系统API服务器...")
    logger.info(f"地址: http://{host}:{port}")
    logger.info(f"文档: http://{host}:{port}/docs")
    
    # 创建应用
    app = create_app()
    
    # 启动服务器
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    await server.serve()


def main() -> int:
    """
    主函数
    
    Returns:
        退出代码 (0=成功, 1=失败)
    """
    # 解析命令行参数
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # 设置日志
    setup_logging()
    logger = get_logger("main")
    
    try:
        # 获取配置
        settings = get_settings()
        
        # 应用命令行参数覆盖
        if args.environment:
            settings.environment = args.environment
        if args.debug:
            settings.debug = True
        
        logger.info(f"智能排程系统启动 - 环境: {settings.environment}")
        
        # 配置检查
        if args.config_check:
            return 0 if check_configuration() else 1
        
        # 求解器测试
        if args.test_solver:
            return 0 if test_solver() else 1
        
        # 启动API服务器
        host = args.host or settings.api.host
        port = args.port or settings.api.port
        reload = args.reload and settings.is_development()
        
        # 运行服务器
        asyncio.run(start_server(host, port, reload))
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭...")
        return 0
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
