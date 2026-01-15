---
name: python-coding
description: 在创建或编辑Python代码时使用此技能。它提供全面的编码标准、架构原则（第一性原理、DRY、KISS、SOLID、YAGNI）、命名约定、文档标准、错误处理、日志记录和代码结构指南。
---

# Python 编码标准

此技能为Python开发提供全面的编码标准和最佳实践。在编写任何Python代码时使用此技能，以确保一致性、可维护性和质量。

## 何时使用此技能

在以下情况下使用此技能：
- 创建新的Python模块或包
- 编写Python函数、类或脚本
- 重构现有Python代码
- 实现错误处理和日志记录
- 组织代码结构和导入
- 编写文档和注释
- 审查或改进代码质量

## 指导原则

在分析问题、设计技术架构和编写代码时，遵循以下基本原则：

### 分析和设计原则
- **第一性原理思维**：将问题分解为基本事实，从根本上构建解决方案
- 质疑假设，在提出解决方案之前理解根本原因

### 编码原则
- **DRY（不要重复自己）**：通过抽象和复用消除代码重复
- **KISS（保持简单，愚蠢）**：优先选择简单、直接的解决方案，而不是复杂的方案
- **SOLID 原则**：遵循面向对象设计原则以实现可维护的代码
- **YAGNI（你不会需要它）**：在必要之前不要添加功能

## 命名约定

始终遵循Python的标准命名约定：

### 变量
使用小写字母加下划线（snake_case）：
```python
user_name = "John"
total_count = 100
is_active = True
```

### 函数
使用小写字母加下划线（snake_case）：
```python
def get_user_info():
    pass

def validate_input(data):
    pass

def calculate_total_price(items):
    pass
```

### 类
使用驼峰命名法（CamelCase）：
```python
class UserService:
    pass

class DatabaseHandler:
    pass

class PaymentProcessor:
    pass
```

### 常量
使用大写字母加下划线：
```python
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30
API_BASE_URL = "https://api.example.com"
```

## 文档标准

### 文件头文档

包含包含模块信息的全面文件头：

```python
"""
模块名称: user_service
功能描述: 提供用户管理相关功能,包括用户注册、登录、信息修改等
创建日期: [YYYY-MM-DD]
作者: Sniperz
版本: v1.0.0
"""
```

### 函数文档

使用完整的参数和返回信息记录函数：

```python
def get_user_by_id(user_id, include_deleted=False):
    """
    根据用户ID获取用户信息

    Args:
        user_id (int): 用户唯一标识
        include_deleted (bool, optional): 是否包含已删除用户，默认为False

    Returns:
        dict: 用户信息字典，包含id、name、email等字段

    Raises:
        ValueError: 当user_id不是正整数时
        UserNotFoundError: 当用户不存在时
    """
    pass
```

### 类文档

记录类的目的和属性描述：

```python
class UserService:
    """
    用户服务类，提供用户相关的业务逻辑处理

    Attributes:
        db_connection (Connection): 数据库连接对象
        logger (Logger): 日志记录器
    """

    def __init__(self, db_connection):
        self.db_connection = db_connection
        self.logger = get_logger(__name__)
```

## 错误处理标准

### 使用特定的异常类型

捕获特定异常而不是捕获所有异常：

```python
# 推荐
try:
    result = process_data(data)
except ValueError as e:
    logger.error(f"数据格式错误: {e}")
except ConnectionError as e:
    logger.error(f"连接失败: {e}")

# 避免
try:
    result = process_data(data)
except Exception as e:  # 过于宽泛
    logger.error(f"错误: {e}")
```

### 提供有意义的错误消息

在错误消息中包含上下文和可操作的信息：

```python
# 推荐
raise ValueError(f"Invalid user_id: {user_id}. Expected positive integer.")

# 避免
raise ValueError("Invalid input")
```

### 使用上下文管理器

使用上下文管理器进行资源管理：

```python
# 推荐
with open('data.txt', 'r') as file:
    content = file.read()

# 避免
file = open('data.txt', 'r')
content = file.read()
file.close()  # 如果发生异常可能不会执行
```

### 记录异常

始终记录异常以便调试和监控：

```python
try:
    result = risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise
```

## 日志标准

### 使用适当的日志级别

为每条消息选择正确的日志级别：

```python
# DEBUG: 诊断问题的详细信息
logger.debug(f"处理请求参数: {params}")

# INFO: 一般信息性消息
logger.info(f"用户 {user_id} 登录成功")

# WARNING: 潜在有害情况的警告消息
logger.warning(f"配置文件缺失，使用默认值")

# ERROR: 可能仍允许应用程序继续运行的错误事件
logger.error(f"数据库连接失败: {e}")

# CRITICAL: 可能导致应用程序中止的非常严重的错误事件
logger.critical(f"无法加载关键配置，应用终止")
```


### 包含上下文信息

在日志消息中提供相关上下文：

```python
logger.info(
    f"Processing order {order_id} for user {user_id} "
    f"with {len(items)} items"
)
```

## 代码结构标准

### 导入组织

将导入分为三组，组之间用空行分隔：

```python
# 标准库
import os
import sys
import json
from datetime import datetime

# 第三方库
import requests
import pandas as pd
from sqlalchemy import create_engine

# 本地应用/库
from app.models import User
from app.utils.helpers import format_date
from app.services.auth import authenticate
```

### 类方法组织

以一致的顺序组织类方法：

```python
class DataProcessor:
    # 1. __init__ 方法
    def __init__(self, config):
        self.config = config
        self.data = None
        self._processed = False

    # 2. @property 方法
    @property
    def is_processed(self):
        return self._processed

    # 3. @classmethod 方法
    @classmethod
    def from_file(cls, filepath):
        config = load_config(filepath)
        return cls(config)

    # 4. 公共实例方法
    def process(self):
        if not self.data:
            raise ValueError("No data loaded")
        self.data = self._transform_data(self.data)
        self._processed = True
        return self.data

    def load_data(self, source):
        self.data = read_data(source)
        return self

    # 5. 私有方法（以 _ 开头）
    def _transform_data(self, data):
        # 数据转换逻辑
        return data

    def _validate_config(self):
        # 配置验证逻辑
        pass
```

## 代码质量要求

编写Python代码时，确保：

1. **类型提示**：为函数参数和返回值使用类型提示
2. **文档字符串**：为模块、类和函数提供全面的文档字符串
3. **一致性**：在整个代码中遵循一致的命名和格式
4. **简单性**：优先选择简单、可读的代码，而不是巧妙的解决方案
5. **可测试性**：编写易于测试和调试的代码
6. **安全性**：验证输入并适当处理敏感数据
7. **性能**：考虑性能影响，特别是对于循环和数据库查询
