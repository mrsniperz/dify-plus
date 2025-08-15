"""
资源模型 (Resource Models)

定义系统中各种资源的数据模型，包括人力资源和物理资源。
资源是排程系统中的核心约束要素，需要精确建模以支持复杂的资源分配和冲突检测。

模型层次：
- Resource: 基础资源模型
- HumanResource: 人力资源模型
- PhysicalResource: 物理资源模型
- ResourceAvailability: 资源可用性模型
- ResourceCalendar: 资源日历模型
"""

from datetime import datetime, time
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

from ..core.constants import ResourceType


class AvailabilityStatus(str, Enum):
    """可用性状态枚举"""
    AVAILABLE = "available"      # 可用
    BUSY = "busy"               # 忙碌
    MAINTENANCE = "maintenance"  # 维护中
    UNAVAILABLE = "unavailable" # 不可用


class ShiftType(str, Enum):
    """班次类型枚举"""
    DAY_SHIFT = "day_shift"     # 白班
    NIGHT_SHIFT = "night_shift" # 夜班
    OVERTIME = "overtime"       # 加班


class TimeSlot(BaseModel):
    """时间段模型"""
    start_time: time = Field(..., description="开始时间")
    end_time: time = Field(..., description="结束时间")
    
    @validator('end_time')
    def validate_end_after_start(cls, v, values):
        """验证结束时间在开始时间之后"""
        start_time = values.get('start_time')
        if start_time and v <= start_time:
            raise ValueError("End time must be after start time")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "start_time": "08:00:00",
                "end_time": "17:00:00"
            }
        }


class WorkingDay(BaseModel):
    """工作日模型"""
    day_of_week: int = Field(..., ge=0, le=6, description="星期几（0=周一，6=周日）")
    time_slots: List[TimeSlot] = Field(..., description="工作时间段")
    shift_type: ShiftType = Field(ShiftType.DAY_SHIFT, description="班次类型")
    
    class Config:
        schema_extra = {
            "example": {
                "day_of_week": 0,
                "time_slots": [
                    {"start_time": "08:00:00", "end_time": "12:00:00"},
                    {"start_time": "13:00:00", "end_time": "17:00:00"}
                ],
                "shift_type": "day_shift"
            }
        }


class ResourceCalendar(BaseModel):
    """资源日历模型"""
    calendar_id: str = Field(..., description="日历ID")
    name: str = Field(..., description="日历名称")
    working_days: List[WorkingDay] = Field(..., description="工作日配置")
    holidays: List[datetime] = Field(default_factory=list, description="节假日列表")
    special_working_days: List[datetime] = Field(default_factory=list, description="特殊工作日列表")
    
    def is_working_time(self, dt: datetime) -> bool:
        """
        检查指定时间是否为工作时间
        
        Args:
            dt: 要检查的时间
            
        Returns:
            是否为工作时间
        """
        # 检查是否为节假日
        if dt.date() in [h.date() for h in self.holidays]:
            return False
            
        # 检查是否为特殊工作日
        if dt.date() in [w.date() for w in self.special_working_days]:
            return True
            
        # 检查正常工作日
        day_of_week = dt.weekday()
        for working_day in self.working_days:
            if working_day.day_of_week == day_of_week:
                current_time = dt.time()
                for time_slot in working_day.time_slots:
                    if time_slot.start_time <= current_time <= time_slot.end_time:
                        return True
        return False
    
    class Config:
        schema_extra = {
            "example": {
                "calendar_id": "CAL-001",
                "name": "标准工作日历",
                "working_days": [
                    {
                        "day_of_week": 0,
                        "time_slots": [
                            {"start_time": "08:00:00", "end_time": "17:00:00"}
                        ],
                        "shift_type": "day_shift"
                    }
                ],
                "holidays": [],
                "special_working_days": []
            }
        }


class ResourceAvailability(BaseModel):
    """资源可用性模型"""
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    status: AvailabilityStatus = Field(..., description="可用性状态")
    reason: Optional[str] = Field(None, description="状态原因")
    
    @validator('end_time')
    def validate_end_after_start(cls, v, values):
        """验证结束时间在开始时间之后"""
        start_time = values.get('start_time')
        if start_time and v <= start_time:
            raise ValueError("End time must be after start time")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "start_time": "2025-08-15T08:00:00Z",
                "end_time": "2025-08-15T17:00:00Z",
                "status": "available",
                "reason": None
            }
        }


class Resource(BaseModel):
    """
    基础资源模型
    
    定义所有资源的通用属性和行为。
    """
    resource_id: str = Field(..., description="资源唯一标识")
    resource_type: ResourceType = Field(..., description="资源类型")
    name: str = Field(..., description="资源名称")
    description: Optional[str] = Field(None, description="资源描述")
    
    # 容量信息
    total_quantity: int = Field(1, ge=1, description="总数量")
    available_quantity: int = Field(1, ge=0, description="可用数量")
    
    # 可用性
    calendar: Optional[ResourceCalendar] = Field(None, description="资源日历")
    availability_periods: List[ResourceAvailability] = Field(
        default_factory=list,
        description="可用性时间段"
    )
    
    # 位置信息
    location: Optional[str] = Field(None, description="位置")
    area: Optional[str] = Field(None, description="区域")
    
    # 成本信息
    hourly_cost: Optional[float] = Field(None, ge=0, description="小时成本")
    setup_cost: Optional[float] = Field(None, ge=0, description="设置成本")
    
    # 状态信息
    is_active: bool = Field(True, description="是否激活")
    current_status: AvailabilityStatus = Field(AvailabilityStatus.AVAILABLE, description="当前状态")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")
    
    @validator('available_quantity')
    def validate_available_not_exceed_total(cls, v, values):
        """验证可用数量不超过总数量"""
        total_quantity = values.get('total_quantity', 1)
        if v > total_quantity:
            raise ValueError("Available quantity cannot exceed total quantity")
        return v
    
    def is_available_at(self, dt: datetime) -> bool:
        """
        检查在指定时间是否可用
        
        Args:
            dt: 要检查的时间
            
        Returns:
            是否可用
        """
        if not self.is_active:
            return False
            
        # 检查日历
        if self.calendar and not self.calendar.is_working_time(dt):
            return False
            
        # 检查可用性时间段
        for period in self.availability_periods:
            if period.start_time <= dt <= period.end_time:
                return period.status == AvailabilityStatus.AVAILABLE
                
        return self.current_status == AvailabilityStatus.AVAILABLE
    
    def get_available_quantity_at(self, dt: datetime) -> int:
        """
        获取在指定时间的可用数量
        
        Args:
            dt: 要检查的时间
            
        Returns:
            可用数量
        """
        if self.is_available_at(dt):
            return self.available_quantity
        return 0
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "resource_id": "CRANE-1",
                "resource_type": "equipment",
                "name": "行车1号",
                "description": "主要用于发动机吊装的行车设备",
                "total_quantity": 1,
                "available_quantity": 1,
                "location": "车间A",
                "area": "工位区域1",
                "hourly_cost": 100.0,
                "is_active": True,
                "current_status": "available"
            }
        }


class HumanResource(Resource):
    """
    人力资源模型
    
    扩展基础资源模型，添加人力资源特有的属性。
    """
    employee_id: str = Field(..., description="员工ID")
    qualifications: List[str] = Field(default_factory=list, description="资质列表")
    skill_levels: Dict[str, int] = Field(default_factory=dict, description="技能等级（1-5）")
    experience_years: Optional[float] = Field(None, ge=0, description="工作经验年数")
    
    # 绩效信息
    performance_rating: Optional[float] = Field(None, ge=1, le=5, description="绩效评级（1-5）")
    efficiency_factors: Dict[str, float] = Field(
        default_factory=dict,
        description="不同任务类型的效率因子"
    )
    
    # 排班信息
    shift_preferences: List[ShiftType] = Field(default_factory=list, description="班次偏好")
    max_overtime_hours: Optional[float] = Field(None, ge=0, description="最大加班小时数")
    
    def __init__(self, **data):
        # 确保人力资源类型正确
        data['resource_type'] = ResourceType.HUMAN
        super().__init__(**data)
    
    def has_qualification(self, qualification: str) -> bool:
        """
        检查是否具备特定资质
        
        Args:
            qualification: 资质名称
            
        Returns:
            是否具备该资质
        """
        return qualification in self.qualifications
    
    def get_skill_level(self, skill: str) -> int:
        """
        获取特定技能等级
        
        Args:
            skill: 技能名称
            
        Returns:
            技能等级（1-5），如果没有该技能则返回0
        """
        return self.skill_levels.get(skill, 0)
    
    def get_efficiency_factor(self, task_type: str) -> float:
        """
        获取特定任务类型的效率因子
        
        Args:
            task_type: 任务类型
            
        Returns:
            效率因子，默认为1.0
        """
        return self.efficiency_factors.get(task_type, 1.0)
    
    class Config:
        schema_extra = {
            "example": {
                "resource_id": "TECH-001",
                "resource_type": "human",
                "name": "技术员张三",
                "employee_id": "E-001",
                "qualifications": ["inspector", "crane_operator"],
                "skill_levels": {"inspection": 4, "maintenance": 3},
                "experience_years": 5.5,
                "performance_rating": 4.2,
                "efficiency_factors": {"inspection": 0.9, "maintenance": 1.1},
                "shift_preferences": ["day_shift"],
                "max_overtime_hours": 4.0,
                "is_active": True,
                "current_status": "available"
            }
        }


class PhysicalResource(Resource):
    """
    物理资源模型
    
    扩展基础资源模型，添加物理资源特有的属性。
    """
    # 设备信息
    model: Optional[str] = Field(None, description="型号")
    serial_number: Optional[str] = Field(None, description="序列号")
    manufacturer: Optional[str] = Field(None, description="制造商")
    
    # 技术规格
    specifications: Dict[str, Any] = Field(default_factory=dict, description="技术规格")
    capacity_limits: Dict[str, float] = Field(default_factory=dict, description="容量限制")
    
    # 维护信息
    last_maintenance: Optional[datetime] = Field(None, description="上次维护时间")
    next_maintenance: Optional[datetime] = Field(None, description="下次维护时间")
    maintenance_interval_hours: Optional[float] = Field(None, ge=0, description="维护间隔小时数")
    
    # 独占性
    is_exclusive: bool = Field(False, description="是否为独占资源")
    exclusive_group: Optional[str] = Field(None, description="独占组ID")
    
    def needs_maintenance(self) -> bool:
        """
        检查是否需要维护
        
        Returns:
            是否需要维护
        """
        if self.next_maintenance:
            return datetime.now() >= self.next_maintenance
        return False
    
    def is_in_exclusive_group(self, group_id: str) -> bool:
        """
        检查是否属于特定独占组
        
        Args:
            group_id: 独占组ID
            
        Returns:
            是否属于该独占组
        """
        return self.exclusive_group == group_id
    
    class Config:
        schema_extra = {
            "example": {
                "resource_id": "CRANE-1",
                "resource_type": "equipment",
                "name": "行车1号",
                "model": "QD-50T",
                "serial_number": "CR001",
                "manufacturer": "重工集团",
                "specifications": {"max_load": "50T", "span": "30m"},
                "capacity_limits": {"max_weight": 50000.0},
                "is_exclusive": True,
                "exclusive_group": "CRANE_GROUP_A",
                "is_active": True,
                "current_status": "available"
            }
        }
