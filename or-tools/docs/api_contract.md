# 准备阶段 API 契约（Preparation Domain API Contract)

本契约覆盖准备阶段智能排程、事件重排、交接确认、策略切换等接口。所有时间字段使用 ISO8601（UTC+0），数值单位在字段名或说明中明确。

## 1. 认证与通用约定
- 认证：Bearer Token（Header: `Authorization: Bearer <token>`）
- 内容类型：`application/json`
- 幂等性：标注 `idempotency_key` 的接口建议实现幂等。
- 统一错误响应：
```json
{
  "error": {
    "code": "string",   // e.g., INVALID_ARGUMENT, NOT_FOUND, CONFLICT, RATE_LIMITED
    "message": "string",
    "details": [{"field": "string", "reason": "string"}]
  },
  "request_id": "string"
}
```

## 2. 生成准备排程
### POST /prep/tasks/plan
- 功能：基于工包与资源/物料快照生成准备排程与门禁清单。
- 幂等：支持（`idempotency_key`）。
- 请求：
```json
{
  "work_packages": [
    {
      "work_package_id": "WP-001",
      "engine_id": "ENG-001",
      "jobs": ["J-1", "J-2"],
      "materials": [
        {"material_id": "M-001", "must_kit": true, "allow_partial": false, "eta": "2025-08-14T12:00:00Z"}
      ]
    }
  ],
  "assets": [
    {"asset_id": "CRANE-1", "category": "hoist", "is_critical": true, "calendar": {}},
    {"asset_id": "BAY-A", "category": "other", "exclusive_group": "BAY-A"}
  ],
  "humans": [
    {"employee_id": "E-01", "qualifications": ["inspector"], "availability_schedule": {}}
  ],
  "config": {
    "prep_window_days": 2,
    "objective_template": "balanced",   // balanced | protect_sla | cost_min
    "freeze_inprogress": true
  },
  "idempotency_key": "abcd-1234"
}
```
- 成功响应：
```json
{
  "plan_id": "PLAN-20250814-0001",
  "gates": [
    {"gate": "critical_tools_ready", "passed": false, "expected_time": "2025-08-14T10:00:00Z"},
    {"gate": "materials_ready", "passed": true}
  ],
  "preparation_tasks": [
    {
      "prep_id": "P-1001",
      "type": "tool_allocation",
      "is_gate": true,
      "engine_id": "ENG-001",
      "work_package_id": "WP-001",
      "interval": {"start": "2025-08-14T07:00:00Z", "end": "2025-08-14T08:30:00Z"},
      "required_assets": ["CRANE-1"],
      "required_roles": ["supervisor"],
      "area": "BAY-A"
    }
  ],
  "makespan": "PT6H",
  "request_id": "req-xxx"
}
```

## 3. 事件驱动重排
### POST /prep/events/apply
- 功能：应用 ETA 变更/第三方确认/SAP 状态变化等事件并触发局部重排。
- 请求：
```json
{
  "plan_id": "PLAN-20250814-0001",
  "events": [
    {
      "event_id": "EV-01",
      "type": "eta_change",            // eta_change | sap_update | weather | third_party_ack
      "effective_time": "2025-08-14T08:00:00Z",
      "payload": {"material_id": "M-001", "new_eta": "2025-08-14T16:00:00Z"},
      "policy": "replan_unstarted"     // replan_unstarted | rolling_window
    }
  ]
}
```
- 成功响应（含差异）：
```json
{
  "plan_id": "PLAN-20250814-0001",
  "diff": {
    "affected_tasks": ["P-1001", "P-1002"],
    "delays": [{"prep_id": "P-1001", "delay_minutes": 90}],
    "resource_reallocation": [{"asset_id": "CRANE-1", "from": "P-1001", "to": "P-2001"}]
  },
  "new_makespan": "PT7H",
  "request_id": "req-yyy"
}
```

## 4. 准备态汇总
### GET /prep/summary?plan_id=PLAN-...
- 功能：返回门禁通过率、预计准备完成时间、SLA风险、关键路径。
- 响应：
```json
{
  "plan_id": "PLAN-20250814-0001",
  "gate_pass_rate": 0.67,
  "expected_ready_time": "2025-08-14T18:00:00Z",
  "sla_risks": [{"work_package_id": "WP-001", "risk": "high", "reason": "critical_tool_missing"}],
  "critical_path": ["P-1001", "P-1033", "P-1040"],
  "kpis": {"utilization": {"crane": 0.82, "bay": 0.74}}
}
```

## 5. 交接/台账证据上报
### POST /prep/handovers/confirm
- 功能：提交 QEC 货架交接/临时工装设备台账等证据，推动门禁通过。
- 请求：
```json
{
  "plan_id": "PLAN-20250814-0001",
  "prep_id": "P-1040",
  "evidence": {
    "handover_form": "url-or-hash",
    "photo": ["url1", "url2"],
    "signature": {"by": "E-01", "time": "2025-08-14T09:00:00Z"}
  }
}
```
- 响应：
```json
{"status": "ok", "updated_gate": "qec_shelf_handover", "passed": true}
```

## 6. 策略模板切换
### POST /config/priority-template:apply
- 功能：切换到某预设策略模板，可灰度发布。
- 请求：
```json
{
  "template": "balanced",               // balanced | protect_sla | cost_min
  "override_weights": {                  // 可选：细粒度权重调整
    "sla_violation": 10,
    "wait_time": 4,
    "switch_cost": 3,
    "preference": 1
  },
  "scope": {"work_packages": ["WP-001", "WP-002"]},  // 若为空则全局
  "grayscale": {"enabled": true, "ratio": 0.2, "duration_minutes": 120}
}
```
- 响应：
```json
{"status": "ok", "applied_to": ["WP-001", "WP-002"], "request_id": "req-zzz"}
```

## 7. 插单护栏设置
### POST /config/preemption:settings
- 功能：配置插单护栏参数与审批策略。
- 请求：
```json
{
  "max_preemptions_per_project_per_day": 2,
  "max_preemption_hours_per_time": 4,
  "approval": {"required": true, "role": "operation_manager"}
}
```
- 响应：
```json
{"status": "ok"}
```

## 8. 审计与变更日志
### GET /audit/changes?plan_id=PLAN-...
- 功能：查询插单、重排、策略切换的审计记录。
- 响应：
```json
{
  "items": [
    {
      "type": "preemption",
      "preemption_reason": "protect_sla",
      "impacted_tasks": ["P-1001"],
      "delay_minutes": 90,
      "recovery_plan": "Re-schedule after 13:00Z",
      "expected_recovery_time": "2025-08-14T13:00:00Z",
      "approver": "E-OPS-01",
      "timestamp": "2025-08-14T08:05:00Z"
    }
  ]
}
```
