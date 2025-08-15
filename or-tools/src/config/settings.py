"""
应用设置 (Application Settings)

管理智能排程系统的配置参数和环境设置。
支持从环境变量、配置文件等多种来源加载配置。

主要功能：
- 环境变量配置
- 默认参数设置
- 配置验证
- 配置热更新
"""

import os
from typing import List, Dict, Any, Optional
from functools import lru_cache
from pydantic import Field, validator
from pydantic_settings import BaseSettings

from ..core.constants import PriorityTemplate, SystemConstants


class DatabaseSettings(BaseSettings):
    """数据库配置"""
    
    # 数据库连接
    database_url: str = Field(
        default="sqlite:///./scheduling.db",
        env="DATABASE_URL",
        description="数据库连接URL"
    )
    
    # 连接池配置
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    
    # 查询配置
    echo_sql: bool = Field(default=False, env="DB_ECHO_SQL")
    
    class Config:
        env_prefix = "DB_"


class RedisSettings(BaseSettings):
    """Redis配置"""
    
    # Redis连接
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL",
        description="Redis连接URL"
    )
    
    # 连接配置
    max_connections: int = Field(default=20, env="REDIS_MAX_CONNECTIONS")
    retry_on_timeout: bool = Field(default=True, env="REDIS_RETRY_ON_TIMEOUT")
    
    # 缓存配置
    default_ttl: int = Field(default=3600, env="REDIS_DEFAULT_TTL")
    
    class Config:
        env_prefix = "REDIS_"


class SolverSettings(BaseSettings):
    """求解器配置"""
    
    # 默认求解器
    default_solver: str = Field(default="cpsat", env="SOLVER_DEFAULT")
    
    # 时间限制
    default_time_limit: float = Field(
        default=SystemConstants.DEFAULT_SOLVE_TIME_LIMIT,
        env="SOLVER_TIME_LIMIT"
    )
    
    single_package_limit: float = Field(
        default=SystemConstants.SINGLE_PACKAGE_SOLVE_LIMIT,
        env="SOLVER_SINGLE_PACKAGE_LIMIT"
    )
    
    multi_package_limit: float = Field(
        default=SystemConstants.MULTI_PACKAGE_SOLVE_LIMIT,
        env="SOLVER_MULTI_PACKAGE_LIMIT"
    )
    
    # 并行配置
    max_workers: int = Field(default=4, env="SOLVER_MAX_WORKERS")
    enable_parallel: bool = Field(default=True, env="SOLVER_ENABLE_PARALLEL")
    
    # 日志配置
    log_search_progress: bool = Field(default=False, env="SOLVER_LOG_PROGRESS")
    
    class Config:
        env_prefix = "SOLVER_"


class APISettings(BaseSettings):
    """API配置"""
    
    # 服务器配置
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    
    # CORS配置
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080"
        ],
        env="API_CORS_ORIGINS"
    )
    
    # 请求限制
    max_request_size: int = Field(default=16 * 1024 * 1024, env="API_MAX_REQUEST_SIZE")  # 16MB
    request_timeout: int = Field(default=300, env="API_REQUEST_TIMEOUT")  # 5分钟
    
    # 分页配置
    default_page_size: int = Field(default=20, env="API_DEFAULT_PAGE_SIZE")
    max_page_size: int = Field(default=100, env="API_MAX_PAGE_SIZE")
    
    # 文档配置
    enable_docs: bool = Field(default=True, env="API_ENABLE_DOCS")
    docs_url: str = Field(default="/docs", env="API_DOCS_URL")
    
    class Config:
        env_prefix = "API_"


class LoggingSettings(BaseSettings):
    """日志配置"""
    
    # 日志级别
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # 日志格式
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # 日志文件
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    max_log_size: int = Field(default=100 * 1024 * 1024, env="LOG_MAX_SIZE")  # 100MB
    backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # 结构化日志
    enable_json_logs: bool = Field(default=False, env="LOG_ENABLE_JSON")
    
    class Config:
        env_prefix = "LOG_"


class SecuritySettings(BaseSettings):
    """安全配置"""
    
    # JWT配置
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="JWT_EXPIRE_MINUTES")
    
    # API密钥
    api_keys: List[str] = Field(default=[], env="API_KEYS")
    
    # 速率限制
    enable_rate_limiting: bool = Field(default=True, env="SECURITY_ENABLE_RATE_LIMITING")
    rate_limit_per_minute: int = Field(default=60, env="SECURITY_RATE_LIMIT_PER_MINUTE")
    
    class Config:
        env_prefix = "SECURITY_"


class BusinessSettings(BaseSettings):
    """业务配置"""
    
    # 默认策略模板
    default_priority_template: str = Field(
        default=PriorityTemplate.BALANCED.value,
        env="BUSINESS_DEFAULT_PRIORITY_TEMPLATE"
    )
    
    # 准备窗口
    default_prep_window_days: int = Field(
        default=SystemConstants.DEFAULT_PREP_WINDOW_DAYS,
        env="BUSINESS_DEFAULT_PREP_WINDOW_DAYS"
    )
    
    # 插单护栏
    max_preemptions_per_day: int = Field(
        default=SystemConstants.DEFAULT_MAX_PREEMPTIONS_PER_DAY,
        env="BUSINESS_MAX_PREEMPTIONS_PER_DAY"
    )
    
    max_preemption_hours: int = Field(
        default=SystemConstants.DEFAULT_MAX_PREEMPTION_HOURS,
        env="BUSINESS_MAX_PREEMPTION_HOURS"
    )
    
    # SLA配置
    sla_risk_threshold_hours: int = Field(
        default=SystemConstants.SLA_RISK_THRESHOLD_HOURS,
        env="BUSINESS_SLA_RISK_THRESHOLD_HOURS"
    )
    
    # 关键路径配置
    critical_path_delay_threshold_hours: int = Field(
        default=SystemConstants.CRITICAL_PATH_DELAY_THRESHOLD_HOURS,
        env="BUSINESS_CRITICAL_PATH_DELAY_THRESHOLD_HOURS"
    )
    
    @validator('default_priority_template')
    def validate_priority_template(cls, v):
        valid_templates = [t.value for t in PriorityTemplate]
        if v not in valid_templates:
            raise ValueError(f"Invalid priority template. Must be one of: {valid_templates}")
        return v
    
    class Config:
        env_prefix = "BUSINESS_"


class Settings(BaseSettings):
    """
    主配置类
    
    整合所有子配置模块。
    """
    
    # 环境配置
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # 应用信息
    app_name: str = Field(default="智能排程系统", env="APP_NAME")
    app_version: str = Field(default="0.1.0", env="APP_VERSION")
    
    # 子配置
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    solver: SolverSettings = SolverSettings()
    api: APISettings = APISettings()
    logging: LoggingSettings = LoggingSettings()
    security: SecuritySettings = SecuritySettings()
    business: BusinessSettings = BusinessSettings()
    
    @validator('environment')
    def validate_environment(cls, v):
        valid_envs = ['development', 'testing', 'staging', 'production']
        if v not in valid_envs:
            raise ValueError(f"Invalid environment. Must be one of: {valid_envs}")
        return v
    
    def is_development(self) -> bool:
        """检查是否为开发环境"""
        return self.environment == "development"
    
    def is_production(self) -> bool:
        """检查是否为生产环境"""
        return self.environment == "production"
    
    def is_testing(self) -> bool:
        """检查是否为测试环境"""
        return self.environment == "testing"
    
    def get_solver_config(self) -> Dict[str, Any]:
        """获取求解器配置字典"""
        return {
            "default_solver": self.solver.default_solver,
            "time_limit_seconds": self.solver.default_time_limit,
            "num_search_workers": self.solver.max_workers,
            "log_search_progress": self.solver.log_search_progress,
            "enable_parallel": self.solver.enable_parallel
        }
    
    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置字典"""
        return {
            "host": self.api.host,
            "port": self.api.port,
            "cors_origins": self.api.cors_origins,
            "enable_docs": self.api.enable_docs,
            "docs_url": self.api.docs_url,
            "max_request_size": self.api.max_request_size,
            "request_timeout": self.api.request_timeout
        }
    
    def get_business_config(self) -> Dict[str, Any]:
        """获取业务配置字典"""
        return {
            "default_priority_template": self.business.default_priority_template,
            "default_prep_window_days": self.business.default_prep_window_days,
            "max_preemptions_per_day": self.business.max_preemptions_per_day,
            "max_preemption_hours": self.business.max_preemption_hours,
            "sla_risk_threshold_hours": self.business.sla_risk_threshold_hours,
            "critical_path_delay_threshold_hours": self.business.critical_path_delay_threshold_hours
        }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    获取应用设置实例
    
    使用LRU缓存确保单例模式。
    
    Returns:
        设置实例
    """
    return Settings()


# 便捷访问
settings = get_settings()
