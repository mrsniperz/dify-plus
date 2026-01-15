---
name: fastapi-coding
description: 在创建或编辑FastAPI应用程序时使用此技能。它提供全面的编码标准、最佳实践和FastAPI开发约定，包括项目结构、API文档、依赖注入和错误处理。
---

# FastAPI 编码标准

此技能为FastAPI应用程序开发提供全面的编码标准和最佳实践。在创建新的FastAPI项目、添加API端点或重构现有FastAPI代码时使用此技能。

## 何时使用此技能

在以下情况下使用此技能：
- 从头开始创建新的FastAPI应用程序
- 向现有FastAPI项目添加新的API端点或路由
- 使用Pydantic实现请求/响应模型
- 设置依赖注入模式
- 配置中间件和CORS设置
- 使用OpenAPI编写API文档
- 在FastAPI中处理错误和异常
- 组织FastAPI项目结构

## 代码结构标准

### 导入组织

按以下顺序组织导入，每组之间用空行分隔：
1. 标准库导入
2. 第三方库导入
3. 本地应用/库导入

在每组内，按字母顺序排序导入。

**规则：**
- 避免通配符导入（`from module import *`）
- 对所有必需的模块使用显式导入
- 使用绝对导入而不是相对导入
- 将所有导入放在文件顶部

### 应用程序初始化

使用完整的元数据初始化FastAPI应用程序：

```python
app = FastAPI(
    title="API名称",
    description="API描述",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "Tag名称",
            "description": "Tag描述"
        }
    ]
)
```

### 中间件配置

显式配置CORS和其他中间件：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

## 文档标准

### 文件头注释

包含全面的文件头文档：

```python
"""
模块名称: service.py
功能描述: 用户服务模块，处理用户相关业务逻辑
创建日期: 2025-05-24
作者: Sniperz
版本: 1.0.0
"""
```

### 路由函数文档

使用完整信息记录路由函数：

```python
"""
功能描述: 创建航空翻译数据集合

Args:
    - importer: AviationTranslationImporter依赖实例

Returns:
    CreateCollectionResponse: 包含操作结果和消息的响应

Raises:
    HTTPException: 500 - 创建集合时出错
"""
```

### 模型类文档

使用属性描述记录Pydantic模型：

```python
"""
搜索请求模型

属性:
    - query_text: 要搜索的文本
    - search_type: 搜索类型(text_match/full_text)
    - limit: 返回结果数量限制
"""
```

### 代码块注释

添加注释以解释复杂逻辑：

```python
# 区域: 数据准备
# 目的: 将Excel数据转换为模型所需格式
```

## API 设计标准

### 路由装饰器

使用包含所有元数据的全面路由装饰器：

```python
@app.post(
    "/path",
    response_model=ResponseModel,
    tags=["Tag名称"],
    summary="简要描述",
    description="详细描述"
)
```

### 错误处理

一致地处理错误：
- 对所有HTTP错误使用 `HTTPException`
- 包含详细的错误消息
- 客户端错误使用 400
- 服务器错误使用 500

示例：
```python
from fastapi import HTTPException

try:
    result = process_data(data)
except ValueError as e:
    raise HTTPException(status_code=400, detail=f"Invalid data: {e}")
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Internal error: {e}")
```

## Pydantic 模型标准

### 模型定义要求

定义模型时包括：
- 继承自 `pydantic.BaseModel`
- 所有字段的显式类型提示
- 可选字段使用 `Optional`
- 适当的默认值

示例：
```python
from pydantic import BaseModel
from typing import Optional

class SearchRequest(BaseModel):
    query_text: str
    search_type: str = "text_match"
    limit: int = 5
```

## 依赖注入标准

### 依赖函数

创建带有清晰文档的依赖函数：

```python
from fastapi import Query

def get_importer(
    collection_name: str = Query(...),
    uri: str = Query(...)
):
    """依赖项函数说明"""
    return Importer(uri, collection_name)
```

### 在路由中使用依赖

使用 `Depends` 注入依赖：

```python
from fastapi import Depends

async def endpoint(importer: Importer = Depends(get_importer)):
    # 使用 importer
    pass
```

## 最佳实践

开发FastAPI应用程序时，遵循以下最佳实践：

1. **单一职责**：每个路由应专注于单一功能
2. **服务层**：将业务逻辑封装在单独的服务类中
3. **异常处理**：使用try-except块捕获和处理异常
4. **性能监控**：为重要操作添加执行时间统计
5. **资源清理**：使用后清理临时文件
6. **类型安全**：在整个代码库中一致使用类型提示
7. **验证**：利用Pydantic进行请求/响应验证
8. **文档**：确保所有端点在OpenAPI中都有良好的文档

## 项目文档要求

在开始任何FastAPI项目开发之前：
- 阅读并理解 `.cursor/docs` 目录中的所有文件
- 审查项目目标、功能架构和技术栈
- 确保清楚理解整体架构和实现方法
- 遵循文档中概述的开发计划
