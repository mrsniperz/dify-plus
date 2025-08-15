"""
时间处理工具 (Time Utils)

提供时间相关的工具函数，包括时间格式转换、时间窗计算、工作日历处理等。

主要功能：
- 时间格式转换
- 时间窗计算
- 工作日历处理
- 时区处理
- 持续时间计算
"""

import re
from datetime import datetime, timedelta, time, date
from typing import List, Tuple, Optional, Union
from zoneinfo import ZoneInfo
import calendar


# 时间格式常量
ISO_FORMAT = "%Y-%m-%dT%H:%M:%S"
ISO_FORMAT_WITH_TZ = "%Y-%m-%dT%H:%M:%S%z"
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def parse_datetime(dt_str: str, default_tz: str = "UTC") -> datetime:
    """
    解析日期时间字符串
    
    支持多种格式：
    - ISO 8601: 2025-08-15T10:30:00Z
    - ISO 8601 with timezone: 2025-08-15T10:30:00+08:00
    - Simple format: 2025-08-15 10:30:00
    
    Args:
        dt_str: 日期时间字符串
        default_tz: 默认时区
        
    Returns:
        解析后的datetime对象
        
    Raises:
        ValueError: 无法解析的时间格式
    """
    if not dt_str:
        raise ValueError("Empty datetime string")
    
    # 移除末尾的Z并添加UTC时区
    if dt_str.endswith('Z'):
        dt_str = dt_str[:-1] + '+00:00'
    
    # 尝试不同的格式
    formats = [
        "%Y-%m-%dT%H:%M:%S%z",      # ISO with timezone
        "%Y-%m-%dT%H:%M:%S",        # ISO without timezone
        "%Y-%m-%d %H:%M:%S",        # Simple format
        "%Y-%m-%d",                 # Date only
        "%H:%M:%S",                 # Time only
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(dt_str, fmt)
            
            # 如果没有时区信息，添加默认时区
            if dt.tzinfo is None:
                if fmt == "%H:%M:%S":
                    # 时间格式，使用今天的日期
                    today = datetime.now().date()
                    dt = datetime.combine(today, dt.time())
                dt = dt.replace(tzinfo=ZoneInfo(default_tz))
            
            return dt
            
        except ValueError:
            continue
    
    raise ValueError(f"Unable to parse datetime string: {dt_str}")


def format_datetime(dt: datetime, format_type: str = "iso") -> str:
    """
    格式化日期时间
    
    Args:
        dt: 日期时间对象
        format_type: 格式类型 (iso, simple, date, time)
        
    Returns:
        格式化后的字符串
    """
    if format_type == "iso":
        return dt.isoformat()
    elif format_type == "simple":
        return dt.strftime(DATETIME_FORMAT)
    elif format_type == "date":
        return dt.strftime(DATE_FORMAT)
    elif format_type == "time":
        return dt.strftime(TIME_FORMAT)
    else:
        return dt.isoformat()


def parse_duration(duration_str: str) -> timedelta:
    """
    解析持续时间字符串
    
    支持格式：
    - ISO 8601: PT4H30M (4小时30分钟)
    - Simple: 4h30m, 4.5h, 270m
    - Seconds: 16200s
    
    Args:
        duration_str: 持续时间字符串
        
    Returns:
        timedelta对象
        
    Raises:
        ValueError: 无法解析的持续时间格式
    """
    if not duration_str:
        raise ValueError("Empty duration string")
    
    duration_str = duration_str.strip().upper()
    
    # ISO 8601 格式: PT4H30M
    if duration_str.startswith('PT'):
        return _parse_iso_duration(duration_str)
    
    # 简单格式: 4h30m, 4.5h, 270m, 16200s
    return _parse_simple_duration(duration_str)


def _parse_iso_duration(duration_str: str) -> timedelta:
    """解析ISO 8601持续时间格式"""
    pattern = r'PT(?:(\d+(?:\.\d+)?)H)?(?:(\d+(?:\.\d+)?)M)?(?:(\d+(?:\.\d+)?)S)?'
    match = re.match(pattern, duration_str)
    
    if not match:
        raise ValueError(f"Invalid ISO duration format: {duration_str}")
    
    hours = float(match.group(1)) if match.group(1) else 0
    minutes = float(match.group(2)) if match.group(2) else 0
    seconds = float(match.group(3)) if match.group(3) else 0
    
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)


def _parse_simple_duration(duration_str: str) -> timedelta:
    """解析简单持续时间格式"""
    total_seconds = 0
    
    # 匹配小时: 4h, 4.5h
    hours_match = re.search(r'(\d+(?:\.\d+)?)H', duration_str)
    if hours_match:
        total_seconds += float(hours_match.group(1)) * 3600
    
    # 匹配分钟: 30m
    minutes_match = re.search(r'(\d+(?:\.\d+)?)M', duration_str)
    if minutes_match:
        total_seconds += float(minutes_match.group(1)) * 60
    
    # 匹配秒: 45s
    seconds_match = re.search(r'(\d+(?:\.\d+)?)S', duration_str)
    if seconds_match:
        total_seconds += float(seconds_match.group(1))
    
    # 如果没有匹配到任何单位，尝试解析为纯数字（假设为小时）
    if total_seconds == 0:
        try:
            total_seconds = float(duration_str) * 3600
        except ValueError:
            raise ValueError(f"Invalid duration format: {duration_str}")
    
    return timedelta(seconds=total_seconds)


def format_duration(td: timedelta, format_type: str = "iso") -> str:
    """
    格式化持续时间
    
    Args:
        td: timedelta对象
        format_type: 格式类型 (iso, simple, hours)
        
    Returns:
        格式化后的字符串
    """
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if format_type == "iso":
        parts = []
        if hours > 0:
            parts.append(f"{hours}H")
        if minutes > 0:
            parts.append(f"{minutes}M")
        if seconds > 0:
            parts.append(f"{seconds}S")
        return "PT" + "".join(parts) if parts else "PT0S"
    
    elif format_type == "simple":
        if hours > 0:
            return f"{hours}h{minutes}m" if minutes > 0 else f"{hours}h"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return f"{seconds}s"
    
    elif format_type == "hours":
        return f"{td.total_seconds() / 3600:.2f}h"
    
    else:
        return str(td)


def calculate_time_window(
    start_time: datetime,
    duration: Union[timedelta, float],
    buffer_before: float = 0.0,
    buffer_after: float = 0.0
) -> Tuple[datetime, datetime]:
    """
    计算时间窗
    
    Args:
        start_time: 开始时间
        duration: 持续时间（timedelta或小时数）
        buffer_before: 前置缓冲时间（小时）
        buffer_after: 后置缓冲时间（小时）
        
    Returns:
        (有效开始时间, 有效结束时间)
    """
    if isinstance(duration, (int, float)):
        duration = timedelta(hours=duration)
    
    end_time = start_time + duration
    
    effective_start = start_time - timedelta(hours=buffer_before)
    effective_end = end_time + timedelta(hours=buffer_after)
    
    return effective_start, effective_end


def is_working_time(
    dt: datetime,
    working_hours: List[Tuple[time, time]],
    working_days: List[int] = None,
    holidays: List[date] = None
) -> bool:
    """
    检查是否为工作时间
    
    Args:
        dt: 要检查的时间
        working_hours: 工作时间段列表 [(开始时间, 结束时间)]
        working_days: 工作日列表 (0=周一, 6=周日)，默认为周一到周五
        holidays: 节假日列表
        
    Returns:
        是否为工作时间
    """
    if working_days is None:
        working_days = [0, 1, 2, 3, 4]  # 周一到周五
    
    if holidays is None:
        holidays = []
    
    # 检查是否为节假日
    if dt.date() in holidays:
        return False
    
    # 检查是否为工作日
    if dt.weekday() not in working_days:
        return False
    
    # 检查是否在工作时间段内
    current_time = dt.time()
    for start_time, end_time in working_hours:
        if start_time <= current_time <= end_time:
            return True
    
    return False


def get_next_working_time(
    dt: datetime,
    working_hours: List[Tuple[time, time]],
    working_days: List[int] = None,
    holidays: List[date] = None
) -> datetime:
    """
    获取下一个工作时间
    
    Args:
        dt: 当前时间
        working_hours: 工作时间段列表
        working_days: 工作日列表
        holidays: 节假日列表
        
    Returns:
        下一个工作时间
    """
    if working_days is None:
        working_days = [0, 1, 2, 3, 4]
    
    if holidays is None:
        holidays = []
    
    # 如果当前就是工作时间，直接返回
    if is_working_time(dt, working_hours, working_days, holidays):
        return dt
    
    # 查找下一个工作时间
    current_dt = dt.replace(second=0, microsecond=0)
    
    # 最多查找30天
    for _ in range(30):
        # 检查当天是否为工作日且不是节假日
        if (current_dt.weekday() in working_days and 
            current_dt.date() not in holidays):
            
            # 查找当天的工作时间段
            for start_time, end_time in working_hours:
                work_start = current_dt.replace(
                    hour=start_time.hour,
                    minute=start_time.minute,
                    second=0,
                    microsecond=0
                )
                
                if current_dt <= work_start:
                    return work_start
        
        # 移动到下一天的开始
        current_dt = (current_dt + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    
    # 如果30天内都找不到工作时间，返回原时间
    return dt


def calculate_working_hours(
    start_time: datetime,
    end_time: datetime,
    working_hours: List[Tuple[time, time]],
    working_days: List[int] = None,
    holidays: List[date] = None
) -> float:
    """
    计算时间段内的工作小时数
    
    Args:
        start_time: 开始时间
        end_time: 结束时间
        working_hours: 工作时间段列表
        working_days: 工作日列表
        holidays: 节假日列表
        
    Returns:
        工作小时数
    """
    if working_days is None:
        working_days = [0, 1, 2, 3, 4]
    
    if holidays is None:
        holidays = []
    
    total_hours = 0.0
    current_date = start_time.date()
    end_date = end_time.date()
    
    while current_date <= end_date:
        # 检查是否为工作日且不是节假日
        if (current_date.weekday() in working_days and 
            current_date not in holidays):
            
            # 计算当天的工作时间
            for work_start_time, work_end_time in working_hours:
                # 当天工作时间段的开始和结束
                day_work_start = datetime.combine(current_date, work_start_time)
                day_work_end = datetime.combine(current_date, work_end_time)
                
                # 计算与指定时间段的交集
                actual_start = max(start_time, day_work_start)
                actual_end = min(end_time, day_work_end)
                
                if actual_start < actual_end:
                    hours = (actual_end - actual_start).total_seconds() / 3600
                    total_hours += hours
        
        current_date += timedelta(days=1)
    
    return total_hours


def get_business_days(
    start_date: date,
    end_date: date,
    working_days: List[int] = None,
    holidays: List[date] = None
) -> List[date]:
    """
    获取时间段内的工作日
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        working_days: 工作日列表
        holidays: 节假日列表
        
    Returns:
        工作日列表
    """
    if working_days is None:
        working_days = [0, 1, 2, 3, 4]
    
    if holidays is None:
        holidays = []
    
    business_days = []
    current_date = start_date
    
    while current_date <= end_date:
        if (current_date.weekday() in working_days and 
            current_date not in holidays):
            business_days.append(current_date)
        
        current_date += timedelta(days=1)
    
    return business_days


def add_business_days(
    start_date: date,
    days: int,
    working_days: List[int] = None,
    holidays: List[date] = None
) -> date:
    """
    添加工作日
    
    Args:
        start_date: 开始日期
        days: 要添加的工作日数
        working_days: 工作日列表
        holidays: 节假日列表
        
    Returns:
        添加工作日后的日期
    """
    if working_days is None:
        working_days = [0, 1, 2, 3, 4]
    
    if holidays is None:
        holidays = []
    
    current_date = start_date
    added_days = 0
    
    while added_days < days:
        current_date += timedelta(days=1)
        
        if (current_date.weekday() in working_days and 
            current_date not in holidays):
            added_days += 1
    
    return current_date
