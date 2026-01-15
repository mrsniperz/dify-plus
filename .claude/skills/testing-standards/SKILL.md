---
name: testing-standards
description: Python 项目测试代码编写和组织规范，包括测试结构、命名约定、复用策略和执行规范
---

# Testing Standards

当编写、组织或执行测试代码时，请遵循以下规范。

## 测试代码组织规范

### 目录结构
1. **测试文件存放**: 所有测试代码必须存放在 `tests/` 目录下
2. **测试输出管理**: 所有测试输出结果存放在 `test_output/` 目录下

### 标准测试目录结构
```
tests/
├── unit/                  # 单元测试
├── integration/           # 集成测试
├── fixtures/              # 测试数据和夹具
├── mocks/                 # 模拟对象
└── conftest.py           # pytest 配置和共享 fixtures
```

## 测试代码复用规则

### 避免重复原则
1. **重复检查**: 创建新测试前必须检查现有测试代码
2. **代码复用策略**:
   - 优先复用现有测试工具函数
   - 扩展现有测试类而非重新创建
   - 提取公共测试逻辑到 `tests/fixtures/` 或 `tests/mocks/`
3. **测试工具函数**: 在 `tests/conftest.py` 中定义通用测试工具

### 共享资源管理
- 使用 pytest fixtures 共享测试数据和设置
- 将可复用的 mock 对象放在 `tests/mocks/` 目录
- 将测试数据文件放在 `tests/fixtures/` 目录

## 测试命名约定

遵循清晰、一致的命名规范：

1. **测试文件**: `test_<module_name>.py`
   - 示例: `test_user_service.py`, `test_api_routes.py`

2. **测试类**: `Test<ClassName>`
   - 示例: `TestUserService`, `TestAuthMiddleware`

3. **测试方法**: `test_<function_name>_<scenario>`
   - 示例: `test_create_user_success`, `test_login_invalid_credentials`
   - 格式: 动作 + 场景/条件 + 预期结果

## 测试执行规范

### 测试前检查清单
在执行测试前，确认以下事项：

- [ ] 检查是否存在相似的测试用例
- [ ] 确认测试数据的准备和清理
- [ ] 验证测试环境的隔离性
- [ ] 检查测试依赖的可用性

### 测试文档要求
每个测试方法必须包含清晰的文档字符串：

```python
def test_create_user_with_valid_data(self):
    """
    测试使用有效数据创建用户

    测试目的: 验证用户创建功能的正常流程
    输入条件: 有效的用户名、邮箱和密码
    期望结果: 成功创建用户并返回用户对象
    测试类型: 单元测试
    优先级: P0
    """
    # 测试实现
```

### 文档字符串必须包含
- **测试目的**: 说明这个测试验证什么
- **输入条件**: 测试的前置条件和输入数据
- **期望结果**: 测试应该产生的结果
- **测试类型**: 单元测试/集成测试/端到端测试
- **优先级**: P0(关键)/P1(重要)/P2(一般)

## 测试最佳实践

### 测试隔离性
- 每个测试应该独立运行，不依赖其他测试
- 使用 setup/teardown 或 fixtures 管理测试状态
- 避免测试之间共享可变状态

### 测试可读性
- 使用 AAA 模式: Arrange(准备), Act(执行), Assert(断言)
- 每个测试只验证一个行为
- 使用描述性的变量名和断言消息

### 测试覆盖率
- 优先测试核心业务逻辑
- 覆盖边界条件和异常情况
- 不追求 100% 覆盖率，关注关键路径

## pytest 特定规范

### Fixtures 使用
```python
# conftest.py
import pytest

@pytest.fixture
def sample_user():
    """提供测试用户数据"""
    return {
        "username": "testuser",
        "email": "test@example.com"
    }

@pytest.fixture
def db_session():
    """提供数据库会话"""
    session = create_test_session()
    yield session
    session.close()
```

### 参数化测试
```python
@pytest.mark.parametrize("input,expected", [
    ("valid@email.com", True),
    ("invalid-email", False),
    ("", False),
])
def test_email_validation(input, expected):
    """测试邮箱验证逻辑"""
    assert validate_email(input) == expected
```

### 测试标记
```python
@pytest.mark.slow
def test_large_dataset_processing():
    """标记为慢速测试"""
    pass

@pytest.mark.integration
def test_api_integration():
    """标记为集成测试"""
    pass
```

## 常见测试模式

### Mock 外部依赖
```python
from unittest.mock import Mock, patch

def test_api_call_with_mock():
    """使用 mock 测试外部 API 调用"""
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {"status": "ok"}
        result = fetch_data_from_api()
        assert result["status"] == "ok"
```

### 异常测试
```python
def test_invalid_input_raises_error():
    """测试无效输入抛出异常"""
    with pytest.raises(ValueError, match="Invalid input"):
        process_data(invalid_data)
```

### 异步测试
```python
@pytest.mark.asyncio
async def test_async_function():
    """测试异步函数"""
    result = await async_operation()
    assert result is not None
```

## 执行命令

根据项目环境选择合适的命令：

### UV 环境
```bash
# 运行所有测试
uv run pytest

# 运行特定文件
uv run pytest tests/unit/test_user.py

# 运行特定测试
uv run pytest tests/unit/test_user.py::test_create_user

# 显示详细输出
uv run pytest -v

# 显示覆盖率
uv run pytest --cov=src
```

### 标准环境
```bash
# 运行所有测试
pytest

# 运行特定标记的测试
pytest -m "not slow"

# 并行运行测试
pytest -n auto
```

## 测试维护

### 定期审查
- 删除过时的测试
- 更新测试以反映代码变更
- 重构重复的测试代码

### 失败测试处理
- 立即修复失败的测试
- 不要注释掉失败的测试
- 如果测试不再相关，删除它

### 测试性能
- 保持测试快速运行
- 将慢速测试标记并分离
- 使用 mock 避免真实的网络/数据库调用
