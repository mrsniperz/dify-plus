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

## 5. 准备阶段（Preparation）技术设计

### 5.1 数据模型扩展

- **`PreparationTask`**（准备子项）
  ```json
  {
    "prep_id": "string",
    "engine_id": "string",
    "work_package_id": "string",
    "type": "enum(tool_allocation, material_kitting, doc_ready, assessment, shelf_handover, inventory_check, hoist_prep)",
    "is_gate": true,
    "dependencies": ["prep_id"],
    "earliest_start": "datetime",
    "latest_finish": "datetime|null",
    "manual_eta": "datetime|null",  // 人工录入ETA
    "required_assets": [{"asset_id": "string", "quantity": 1}],
    "required_roles": ["inspector", "monitor", "supervisor"],
    "evidence_required": ["handover_form", "photo", "signature"],
    "area": "string",   // 区域/工位
    "duration_hours": "float"
  }
  ```

- **`MaterialItem`**（准备物料项）
  ```json
  {
    "material_id": "string",
    "engine_id": "string",
    "must_kit": true,           // 必须齐套
    "allow_partial": false,     // 是否允许分段
    "eta": "datetime|null",
    "qec_shelf_slot": "string",
    "criticality": "enum(high, medium, low)"
  }
  ```

- **`ToolAsset`**（工装/设备）
  ```json
  {
    "asset_id": "string",
    "category": "enum(hoist, sling, stand, other)",
    "is_critical": true,
    "quantity": 1,
    "calendar": {},             // 可用时段
    "exclusive_group": "string" // 行车/工位独占组
  }
  ```

- **`Event`**（准备事件）
  ```json
  {
    "event_id": "string",
    "type": "enum(eta_change, sap_update, weather, third_party_ack)",
    "payload": {},
    "effective_time": "datetime",
    "scope": {"engines": ["string"], "prep_ids": ["string"]},
    "policy": "enum(replan_unstarted, rolling_window)"
  }
  ```

### 5.2 约束建模（准备门禁与资源）

- **门禁布尔约束**：
  - 关键工装齐套（`ToolAsset.is_critical`）→ 未齐套则禁止工包开工；
  - 航材齐套策略：`must_kit` 必须全部到位；`allow_partial` 允许先行不受影响子项；
  - 技术资料与评估完成（`doc_ready/assessment`）为开工前置；
  - QEC货架交接与库存确认完成为前置。
- **时间窗**：`start(prep) >= max(manual_eta, earliest_start)`；可设置 `latest_finish` 软/硬约束。
- **资源独占与累积**：
  - 行车/工位/独特检验员 → `NoOverlap`；
  - 资质分组人员池 → `Cumulative`；
  - 区域/工位切换成本 → `TransitionTimes` 或显式`setup/teardown`。
- **可选区段**：允许用 `OptionalIntervalVar` 表达条件性/分段性准备项。

### 5.3 目标函数（准备阶段）

采用分层或加权：
1) 门禁与SLA合规（违约强惩罚）；
2) 最小化准备等待时长（ETA驱动）；
3) 最小化行车/工位/区域切换；
4) 连续性与偏好（可选）。

## 6. 多项目并行最优排程（准备阶段）

- **全局资源池**：对行车、工位、关键工装与特定人员建立共享池；
- **跨项目优先级**：根据SLA风险、紧急程度、关键路径暴露度设定权重；
- **冲突消解策略**：优先保护高优/临近SLA项目，提供让位建议与影响评估；
- **批处理**：在不违反门禁前提下，支持同区域/同工装的批量准备，减少切换；
- **公平性**：可选“最小化最大延误”以避免长期压制低优先级项目。

## 7. 动态重排 API（准备域）

- `POST /prep/tasks/plan`：输入工包与资源/物料快照，生成准备排程与门禁清单。
- `POST /prep/events/apply`：应用ETA变更/第三方确认等事件并触发局部重排。
- `GET /prep/summary`：返回门禁通过率、预计准备完成时间、SLA风险。
- `POST /prep/handovers/confirm`：提交QEC货架交接/台账证据，更新状态并触发依赖推进。

### 7.1 插单策略（Preemption with Audit）

- **触发条件**（建议，可配置）：
  - SLA缓冲≤12小时 / 紧急任务标记 / 关键路径预计延误>2小时。
- **执行逻辑**：
  1) 固定在制与已完成的区间；
  2) 在共享资源池内为高优项目插入区间，必要时抢占低优项目未开始/可中断的准备子项；
  3) 为被抢占项目生成“让位说明与影响评估”，并注入“恢复计划”（恢复窗口与提升优先级）。
- **护栏**（可配置）：
  - 单项目每日最多被抢占N次（默认2）；
  - 单次抢占最长M小时（默认4）；
  - 抢占后恢复期内提升优先级或加权（避免饥饿）。
- **审计字段**：
  - `preemption_reason`、`impacted_tasks`、`delay_minutes`、`recovery_plan`、`expected_recovery_time`、`approver`、`timestamp`。

### 7.2 优先级策略模板（Priority Templates）

- **模板**：
  1) 保护SLA型：强惩罚SLA违约，二级优化等待时长；
  2) 均衡公平型：最小化最大延误，适度控制切换成本；
  3) 成本最小型：切换/占用/加班成本权重更高。
- **实现**：目标函数权重集预设 + 配置API热切换；灰度发布（对部分项目生效），结合KPI监控回滚。

## 8. 集成点与时序

- **SAP**：指令拉取（≤1个工作日SLA）、准备完成后允许开工的状态同步；
- **仓储**：库存快照、航材到货ETA、QEC货架交接；
- **工具管理**：工装占用/归还、临时台账创建；
- **第三方**：客户代表/监修确认节点事件回传。

## 9. 测试与验收（准备阶段场景）

- 关键工装缺口阻断与解除；非关键仅阻断子项；
- 人工ETA延后/提前引发的重排；
- 吊装与行车冲突回避；
- SAP指令延迟导致准备窗口调整；
- QEC货架交接缺失阻断开工；
- 多项目共享资源下的优先级与公平性策略生效验证。

## 10. 性能与SLO

- 目标规模与求解SLO：
  - 单工包（准备子项≤100）：初排≤5秒，重排≤2秒；
  - 多工包并行（总准备子项≤500）：初排≤20秒，重排≤8秒；
- 可配置：目标权重、滚动窗口大小、冻结策略（冻结进行中与已完结）。
