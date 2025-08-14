# 智能排程功能 - 开发设计文档

## 1. 目标

本文档旨在为“智能排程功能”的开发提供技术设计和实施路径。目标是实现一个基于OR-Tools的、可扩展、可维护的调度引擎。

## 2. 技术选型

- **核心求解器**: Google OR-Tools `CP-SAT Solver`。它在处理带有复杂逻辑和组合约束的调度问题（Job Shop / Resource-Constrained Project Scheduling Problem）方面表现出色。
- **开发语言**: Python 3.x。
- **数据交换格式**: JSON。具备良好的可读性和跨平台兼容性。

## 3. 系统设计

### 3.1 数据建模 (Data Models)

我们将使用Python的Pydantic库或标准dataclass来定义清晰的数据模型，并与JSON格式进行映射。

- **`Job` (工卡子项目)**
  ```json
  {
    "job_id": "string",
    "work_card_id": "string",
    "engine_id": "string",
    "base_duration_hours": "float",
    "required_resources": [
      { "resource_id": "string", "quantity": "integer" }
    ],
    "required_qualifications": ["string"],
    "predecessor_jobs": ["string"]
  }
  ```

- **`Resource` (资源)**
  ```json
  {
    "resource_id": "string",
    "resource_type": "enum(human, tool, equipment, bay)",
    "name": "string",
    "quantity": "integer", // For non-human resources
    // For human resources:
    "employee_id": "string",
    "qualifications": ["string"],
    "availability_schedule": "object", // e.g., iCalendar format
    "performance_factors": [
      { "job_type_id": "string", "factor": "float" } // factor < 1 is faster
    ]
  }
  ```

### 3.2 求解器模型构建 (Solver-Side)

1.  **创建决策变量**: 
    - 为每个`Job`创建一个`IntervalVar`。其`start`, `end`, `duration`是求解器要决定的核心变量。
    - `duration`将受到执行该任务的`Human Resource`的`performance_factors`影响。
2.  **添加约束**:
    - **前置约束**: 使用`model.Add(job_a.EndExpr() <= job_b.StartExpr())`来表达。
    - **资源约束**: 
        - 对于独占性资源（如工位、特定检验员），使用`NoOverlap`约束。
        - 对于可累积资源（如具备同种资质的多个技术员），使用`Cumulative`约束。
3.  **定义优化目标**: 
    - **主要目标**: 最小化`makespan`，即所有任务的最晚结束时间 `model.Minimize(makespan_variable)`。
    - **次要目标（软约束）**: 可以通过在目标函数中增加惩罚项来实现，例如，为非最优人员分配任务增加一个小的成本项。

### 3.3 动态重调度 (Re-scheduling)

- **触发机制**: 监听外部事件，如“航材到货”、“人员请假”、“任务提前完成”等。
- **实现逻辑**: 
  1. 获取当前系统快照：哪些任务已完成，哪些正在进行中。
  2. 固定已完成任务的`end`时间和正在进行任务的`start`时间。
  3. 以这些固定变量为基础，对所有未开始的任务进行重新求解。
  4. 对比新旧计划，向用户展示变更和影响。

## 4. 开发里程碑

1.  **M1: 基础模型搭建**: 实现核心的数据结构和可以求解一个简化场景（单发动机、无人员绩效）的CP-SAT模型。
2.  **M2: 扩展模型**: 引入多发动机、多资源、人员资质和绩效系数。
3.  **M3: 动态重调度**: 实现动态重调度机制和相应的API接口。
4.  **M4: 集成与测试**: 与前端或其他后端服务进行集成，并编写单元测试和集成测试。
