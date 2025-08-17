# 测试数据深度分析与改进指南

## 1. 测试数据字段详细解析

### 1.1 数据结构概览

测试数据采用分层结构设计，模拟真实的航空发动机维修排程场景：

```
测试数据
├── work_packages (工作包)     - 维修项目级别
├── jobs (任务)              - 具体维修步骤
├── resources (资源)         - 所有可用资源
└── schedule_request (排程请求) - 排程配置和约束
```

### 1.2 工作包 (Work Packages) 字段解析

| 字段名 | 类型 | 含义 | 业务价值 |
|--------|------|------|----------|
| `work_package_id` | String | 工作包唯一标识 | 用于追踪和管理维修项目 |
| `name` | String | 工作包名称 | 便于识别和沟通 |
| `priority` | Enum | 优先级(high/medium/low) | 影响排程顺序和资源分配 |
| `estimated_duration_hours` | Number | 预估总工时 | 用于容量规划和进度控制 |
| `deadline` | DateTime | 截止时间 | 硬约束，影响排程可行性 |
| `engine_id` | String | 发动机编号 | 关联具体维修对象 |
| `aircraft_tail` | String | 飞机尾号 | 追溯到具体飞机 |

### 1.3 任务 (Jobs) 字段解析

#### 基础信息
- `job_id`: 任务唯一标识，格式为"工作包ID-JOB-序号"
- `base_duration_hours`: 基础工时，不考虑资源效率因子
- `required_qualifications`: 所需技能资质列表

#### 增强版资源需求 (Enhanced Resource Requirements)
```json
"required_resources": [
  {
    "resource_id": "MAT-001",
    "resource_type": "material", 
    "quantity": 2,
    "must_kit": true,           // 是否必须齐套
    "criticality": "high"       // 重要性级别
  },
  {
    "resource_id": "EQP-001",
    "resource_type": "equipment",
    "quantity": 1,
    "exclusive": true,          // 是否独占使用
    "setup_time_hours": 1.5     // 设置时间
  }
]
```

#### 约束条件 (Constraints)
- `max_parallel_resources`: 最大并行资源数
- `must_complete_by`: 必须完成时间
- `allow_overtime`: 是否允许加班

### 1.4 资源类型详细分析

#### 人力资源 (Human Resources)
```json
{
  "resource_type": "human",
  "qualifications": ["电气", "机械", "液压"],
  "skill_levels": {"电气": 4, "机械": 3},
  "experience_years": 5.5,
  "performance_rating": 4.2,
  "hourly_rate": 120.0
}
```

#### 航材资源 (Materials) - 新增
```json
{
  "resource_type": "material",
  "part_number": "PN-12345",
  "total_quantity": 50,
  "available_quantity": 10,
  "must_kit": true,              // 齐套策略
  "allow_partial": false,        // 是否允许分段
  "eta": "2025-08-20T10:00:00",  // 预计到货时间
  "storage_location": "货架-A-10",
  "qec_shelf_slot": "B-08-17",   // QEC货架位置
  "unit_cost": 1500.0,
  "criticality": "high",         // 重要性
  "is_ready": true,              // 是否就绪
  "is_kitted": false             // 是否已齐套
}
```

#### 设备资源 (Equipment) - 新增
```json
{
  "resource_type": "equipment",
  "model": "QD-50T",
  "serial_number": "EQ001",
  "is_exclusive": true,          // 独占性
  "exclusive_group": "CRANE_A",  // 独占组
  "capacity_limits": {"max_load": "50T"},
  "maintenance_interval_hours": 500,
  "hourly_cost": 500.0,
  "setup_cost": 200.0
}
```

#### 工具资源 (Tools) - 新增
```json
{
  "resource_type": "tool", 
  "calibration_due": "2025-12-31",
  "requires_certification": true,
  "max_concurrent_users": 2,
  "storage_location": "工具柜-A-15"
}
```

#### 工位资源 (Workspaces) - 新增
```json
{
  "resource_type": "workspace",
  "max_concurrent_jobs": 3,
  "equipped_tools": ["TOOL-001", "TOOL-002"],
  "required_certifications": ["电气", "机械"]
}
```

## 2. 航材信息配置问题解答

### 2.1 为什么原测试数据中没有航材信息？

**根本原因**：原始测试数据生成逻辑不完整

在 `or-tools/tests/test_api.py` 的 `generate_test_data()` 方法中：

```python
# 原始代码只生成人力资源
resources = []
technician_names = ["张师傅", "李技师", "王工程师", "刘专家", "陈主管"]
for i, name in enumerate(technician_names):
    resource = {
        "resource_id": f"TECH-{i+1:03d}",
        "employee_id": f"EMP-{i+1:03d}",
        # ... 只有人力资源配置
    }
```

**系统能力**：虽然系统完全支持航材资源，但测试数据生成器没有实现。

### 2.2 航材资源在源代码中的定义位置

#### 核心定义文件：

1. **资源类型枚举**：`src/core/constants.py`
   ```python
   class ResourceType(str, Enum):
       MATERIAL = "material"  # 航材类型已定义
   ```

2. **航材数据模型**：`src/models/preparation.py`
   ```python
   class MaterialItem(BaseModel):
       material_id: str
       part_number: Optional[str]
       must_kit: bool = True
       required_quantity: int
       available_quantity: int
       eta: Optional[datetime]
       # ... 完整的航材属性
   ```

3. **物理资源模型**：`src/models/resource.py`
   ```python
   class PhysicalResource(Resource):
       # 可用于航材、设备等物理资源建模
   ```

### 2.3 如何添加和修改航材配置

#### 方法1：使用增强版测试数据生成器

```bash
# 生成包含完整资源类型的测试数据
python or-tools/tests/enhanced_test_data_generator.py --scenario standard

# 生成复杂场景测试数据
python or-tools/tests/enhanced_test_data_generator.py --scenario complex
```

#### 方法2：手动配置航材资源

在测试数据中添加航材资源：

```json
{
  "resource_id": "MAT-001",
  "resource_type": "material",
  "name": "发动机密封圈",
  "part_number": "PN-12345",
  "total_quantity": 20,
  "available_quantity": 5,
  "must_kit": true,
  "criticality": "high",
  "eta": "2025-08-20T10:00:00",
  "storage_location": "货架-A-10",
  "unit_cost": 1500.0
}
```

#### 方法3：在任务中引用航材

```json
{
  "job_id": "WP-001-JOB-01",
  "required_resources": [
    {
      "resource_id": "MAT-001",
      "resource_type": "material",
      "quantity": 2,
      "must_kit": true,
      "criticality": "high"
    }
  ]
}
```

### 2.4 航材约束条件的定义和修改

#### 齐套约束 (Kitting Constraints)
```json
{
  "must_kit": true,        // 必须齐套才能开始
  "allow_partial": false,  // 不允许分段执行
  "required_quantity": 5,  // 需求数量
  "available_quantity": 3  // 可用数量
}
```

#### 时间约束 (Temporal Constraints)
```json
{
  "eta": "2025-08-20T10:00:00",  // 预计到货时间
  "lead_time_days": 15,          // 采购周期
  "shelf_life_days": 365         // 保质期
}
```

#### 成本约束 (Cost Constraints)
```json
{
  "unit_cost": 1500.0,           // 单价
  "total_budget": 50000.0,       // 总预算
  "cost_center": "MAINT_DEPT"    // 成本中心
}
```

## 3. 测试数据完整性评估

### 3.1 当前测试数据的不足

#### 原始测试数据问题：
- ❌ **资源类型单一**：只有人力资源，缺少航材、设备、工具、工位
- ❌ **约束简化**：required_resources只是字符串，没有数量、约束信息
- ❌ **缺少物料准备**：没有MaterialItem相关测试数据
- ❌ **缺少设备独占性**：没有行车、工位等独占资源测试
- ❌ **时间约束简单**：只有基本工作时间，没有维护窗口等
- ❌ **成本优化缺失**：虽然有hourly_rate，但没有设备、航材成本

#### 增强版测试数据改进：
- ✅ **完整资源类型**：人力、航材、设备、工具、工位全覆盖
- ✅ **复杂资源约束**：数量、齐套、独占性、认证要求等
- ✅ **真实业务场景**：航材ETA、设备维护、工位容量等
- ✅ **成本优化**：多维度成本考虑
- ✅ **质量要求**：检查、认证、文档要求

### 3.2 测试场景覆盖度分析

| 测试场景类型 | 原始数据 | 增强数据 | 说明 |
|-------------|----------|----------|------|
| 基础排程 | ✅ | ✅ | 简单任务依赖和资源分配 |
| 航材齐套约束 | ❌ | ✅ | must_kit=true的航材约束 |
| 设备独占性 | ❌ | ✅ | 行车、工位等独占资源 |
| 工位容量限制 | ❌ | ✅ | 多任务并行的工位约束 |
| 技能认证要求 | 部分 | ✅ | 工具使用和工位准入认证 |
| 成本优化 | 部分 | ✅ | 多维度成本最小化 |
| 时间窗口约束 | 基础 | ✅ | 设备维护、航材ETA等 |
| 质量控制 | ❌ | ✅ | 检查要求、文档要求等 |

### 3.3 边界情况和异常场景

#### 资源不足场景
```json
{
  "resource_id": "MAT-007",
  "available_quantity": 1,    // 可用数量不足
  "required_quantity": 5,     // 需求数量
  "must_kit": true           // 必须齐套
}
```

#### 设备冲突场景
```json
{
  "resource_id": "EQP-001",
  "is_exclusive": true,       // 独占设备
  "current_status": "maintenance"  // 维护中不可用
}
```

#### 技能不匹配场景
```json
{
  "required_certifications": ["高压电气"],
  "available_technicians": [
    {"qualifications": ["机械", "液压"]}  // 缺少所需技能
  ]
}
```

## 4. 实际使用指南

### 4.1 快速开始

#### 生成标准测试数据
```bash
# 生成标准复杂度的增强测试数据
python or-tools/tests/enhanced_test_data_generator.py --scenario standard

# 输出文件：enhanced_test_data.json
# 包含：3个工作包，9个任务，33个资源（5类型）
```

#### 生成复杂测试数据
```bash
# 生成高复杂度测试数据，用于压力测试
python or-tools/tests/enhanced_test_data_generator.py --scenario complex --output complex_test_data.json

# 输出：5个工作包，更多任务，更复杂的资源约束
```

#### 使用增强测试数据求解
```bash
# 使用增强测试数据进行排程求解
python or-tools/tests/solve_test_data.py --direct --output enhanced_solution.json

# 注意：需要修改solve_test_data.py中的数据文件路径
```

### 4.2 自定义测试场景

#### 场景1：航材短缺测试
```python
# 修改enhanced_test_data_generator.py
def generate_material_shortage_scenario():
    """生成航材短缺场景"""
    materials = []
    for i in range(5):
        material = {
            "resource_id": f"MAT-{i+1:03d}",
            "available_quantity": 1,      # 故意设置不足
            "required_quantity": 5,       # 需求量大
            "must_kit": True,            # 必须齐套
            "criticality": "high",       # 高重要性
            "eta": (datetime.now() + timedelta(days=30)).isoformat()  # 延迟到货
        }
        materials.append(material)
    return materials
```

#### 场景2：设备维护冲突测试
```python
def generate_equipment_maintenance_scenario():
    """生成设备维护冲突场景"""
    equipment = {
        "resource_id": "EQP-001",
        "is_exclusive": True,
        "current_status": "maintenance",
        "next_maintenance": (datetime.now() + timedelta(hours=8)).isoformat(),
        "maintenance_duration_hours": 4
    }
    return equipment
```

### 4.3 测试数据验证

#### 数据完整性检查
```python
def validate_test_data(test_data):
    """验证测试数据完整性"""
    checks = {
        "work_packages_exist": len(test_data.get("work_packages", [])) > 0,
        "jobs_exist": len(test_data.get("jobs", [])) > 0,
        "resources_complete": all([
            len(test_data.get("materials", [])) > 0,
            len(test_data.get("equipment", [])) > 0,
            len(test_data.get("tools", [])) > 0,
            len(test_data.get("workspaces", [])) > 0,
            len(test_data.get("humans", [])) > 0
        ]),
        "resource_references_valid": validate_resource_references(test_data)
    }
    return checks
```

#### 约束条件检查
```python
def validate_constraints(test_data):
    """验证约束条件设置"""
    issues = []

    # 检查航材齐套约束
    for job in test_data.get("jobs", []):
        for req_res in job.get("required_resources", []):
            if req_res.get("resource_type") == "material":
                material = find_material(test_data, req_res["resource_id"])
                if material and req_res.get("must_kit") and material["available_quantity"] < req_res["quantity"]:
                    issues.append(f"航材 {req_res['resource_id']} 数量不足，无法满足齐套要求")

    return issues
```

### 4.4 性能测试建议

#### 小规模测试（开发调试）
- 工作包：2-3个
- 任务：5-10个
- 资源：20-30个
- 预期求解时间：< 5秒

#### 中等规模测试（功能验证）
- 工作包：5-8个
- 任务：15-30个
- 资源：50-80个
- 预期求解时间：10-30秒

#### 大规模测试（压力测试）
- 工作包：10-20个
- 任务：50-100个
- 资源：100-200个
- 预期求解时间：1-5分钟

## 5. 常见问题解答

### 5.1 数据格式问题

**Q: 为什么任务的required_resources从字符串改为对象？**

A: 原始格式过于简化：
```json
// 原始格式 - 信息不足
"required_resources": ["工具1", "工具2"]

// 增强格式 - 包含完整约束信息
"required_resources": [
  {
    "resource_id": "TOOL-001",
    "resource_type": "tool",
    "quantity": 1,
    "requires_certification": true
  }
]
```

**Q: 如何处理资源ID引用一致性？**

A: 确保任务中引用的resource_id在resources列表中存在：
```python
def validate_resource_references(test_data):
    all_resource_ids = {r["resource_id"] for r in test_data["resources"]}
    for job in test_data["jobs"]:
        for req_res in job["required_resources"]:
            if req_res["resource_id"] not in all_resource_ids:
                return False
    return True
```

### 5.2 约束配置问题

**Q: 如何设置航材的齐套约束？**

A: 通过must_kit和allow_partial字段控制：
```json
{
  "must_kit": true,        // 必须齐套才能开始任务
  "allow_partial": false,  // 不允许分段执行
  "required_quantity": 5,  // 需要5个
  "available_quantity": 3  // 只有3个可用 -> 约束冲突
}
```

**Q: 如何设置设备的独占性约束？**

A: 通过is_exclusive和exclusive_group控制：
```json
{
  "is_exclusive": true,           // 独占使用
  "exclusive_group": "CRANE_A",   // 同组设备互斥
  "max_concurrent_jobs": 1        // 最多1个任务
}
```

### 5.3 求解器适配问题

**Q: 增强测试数据是否兼容现有求解器？**

A: 需要确保求解器支持新的资源类型和约束。检查以下文件：
- `src/solvers/constraint_builder.py` - 约束构建逻辑
- `src/services/scheduling_service.py` - 排程服务接口
- `src/models/` - 数据模型定义

**Q: 如何调试求解失败问题？**

A: 使用详细日志和约束验证：
```python
# 在solve_test_data.py中添加调试信息
def debug_solve_failure(test_data, solution):
    if not solution or solution.get("error"):
        print("🔍 求解失败分析:")
        print(f"   工作包数量: {len(test_data['work_packages'])}")
        print(f"   任务数量: {len(test_data['jobs'])}")
        print(f"   资源数量: {len(test_data['resources'])}")

        # 检查资源约束冲突
        conflicts = check_resource_conflicts(test_data)
        if conflicts:
            print(f"   资源冲突: {conflicts}")
```

## 6. 下一步改进建议

### 6.1 短期改进（1-2周）

1. **完善求解器适配**
   - 确保所有资源类型都被正确处理
   - 添加新约束类型的支持
   - 优化求解性能

2. **增加测试场景**
   - 航材ETA延迟场景
   - 设备故障场景
   - 人员请假场景
   - 紧急插单场景

3. **改进数据验证**
   - 添加数据完整性检查
   - 约束条件合理性验证
   - 性能基准测试

### 6.2 中期改进（1个月）

1. **动态事件支持**
   - 实时航材状态更新
   - 设备故障事件处理
   - 计划变更事件

2. **高级约束建模**
   - 多技能组合要求
   - 时间窗口约束
   - 成本预算约束

3. **可视化支持**
   - 甘特图展示
   - 资源利用率图表
   - 约束冲突可视化

### 6.3 长期改进（3个月）

1. **智能数据生成**
   - 基于历史数据的智能生成
   - 机器学习驱动的场景生成
   - 自适应复杂度调整

2. **实时优化**
   - 在线重排程
   - 增量求解
   - 多目标优化

3. **企业级功能**
   - 多租户支持
   - 权限控制
   - 审计日志

---

## 总结

通过本次分析和改进，我们：

1. **深入解析了测试数据结构**，明确了每个字段的业务含义
2. **识别并解决了航材配置缺失问题**，提供了完整的解决方案
3. **全面评估了测试数据完整性**，创建了增强版测试数据生成器
4. **提供了实用的使用指南**，帮助快速上手和自定义场景

增强版测试数据现在包含了：
- ✅ 5种完整的资源类型（人力、航材、设备、工具、工位）
- ✅ 复杂的约束条件（齐套、独占、认证、容量等）
- ✅ 真实的业务场景（ETA、维护、成本等）
- ✅ 边界和异常情况测试

这为智能排程系统的测试和验证提供了坚实的基础。
