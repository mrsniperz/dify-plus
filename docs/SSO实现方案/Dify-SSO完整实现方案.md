# Dify平台单点登录(SSO)完整实现方案

> 文档版本: v1.0.0  
> 创建日期: 2025-11-19  
> 作者: Cascade AI  

## 目录
- [1. Dify认证机制分析](#1-dify认证机制分析)
- [2. SSO实现方案概述](#2-sso实现方案概述)
- [3. 方案一：API Token传递方案](#3-方案一api-token传递方案)
- [4. 方案二：自定义SSO端点方案](#4-方案二自定义sso端点方案)
- [5. 安全措施与最佳实践](#5-安全措施与最佳实践)
- [6. 部署指南](#6-部署指南)

---

## 1. Dify认证机制分析

### 1.1 Token类型与结构

Dify使用**JWT (JSON Web Token)**进行身份认证，包含两种token：

#### Access Token
- **用途**: 访问API资源的凭证
- **算法**: HS256 (HMAC-SHA256)
- **有效期**: 由`ACCESS_TOKEN_EXPIRE_MINUTES`配置（默认60分钟）
- **存储位置**: 
  - 前端: `localStorage` (key: `console_token`)
  - Cookie: `x-token`
- **Payload结构**:
```json
{
  "user_id": "用户ID",
  "exp": 1234567890,
  "iss": "SELF_HOSTED",
  "sub": "Console API Passport"
}
```

#### Refresh Token
- **用途**: 刷新access token
- **有效期**: 由`REFRESH_TOKEN_EXPIRE_DAYS`配置（默认30天）
- **存储位置**: Redis
- **格式**: UUID字符串

### 1.2 认证流程

```
用户登录 → 验证凭证 → 生成TokenPair → 存储refresh_token到Redis → 返回tokens
```

### 1.3 核心API端点

| 端点 | 方法 | 功能 | 请求体 | 响应 |
|------|------|------|--------|------|
| `/console/api/login` | POST | 用户登录 | `{email, password}` | `{access_token, refresh_token}` |
| `/console/api/refresh-token` | POST | 刷新token | `{refresh_token}` | `{access_token, refresh_token}` |
| `/console/api/logout` | GET | 用户登出 | - | `{result: "success"}` |

### 1.4 Token验证机制

Dify使用`PassportService`类进行token的签发和验证：

```python
# 位置: api/libs/passport.py
class PassportService:
    def issue(self, payload):
        return jwt.encode(payload, self.sk, algorithm="HS256")
    
    def verify(self, token):
        return jwt.decode(token, self.sk, algorithms=["HS256"])
```

**密钥来源**: `dify_config.SECRET_KEY` (环境变量)

---

## 2. SSO实现方案概述

### 2.1 方案对比

| 方案 | 复杂度 | 安全性 | 是否需要修改Dify源码 | 适用场景 |
|------|--------|--------|---------------------|----------|
| 方案一：API Token传递 | ⭐⭐ | ⭐⭐⭐ | 否 | 快速实现，网站A与Dify在同一域 |
| 方案二：自定义SSO端点 | ⭐⭐⭐ | ⭐⭐⭐⭐ | 是 | 企业级应用，需要统一认证 |
| 方案三：OAuth2.0 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 是 | 标准化集成，多系统互联 |

### 2.2 推荐方案选择

- **快速实现**: 选择方案一
- **企业应用**: 选择方案二
- **标准化集成**: 选择方案三（本文档暂不详述）

---

## 3. 方案一：API Token传递方案

### 3.1 方案架构

```
网站A前端 → 网站A后端 → Dify API (/console/api/login) → 获取Token
                                                              ↓
网站A前端 ← 重定向URL + Token ← 网站A后端 ←─────────────────┘
    ↓
Dify前端 (接收Token并存储到localStorage)
```

### 3.2 实现步骤

#### 步骤1: 网站A后端实现Token获取

**Python示例** (Flask/FastAPI):

```python
import requests
import hmac
import hashlib
import time
from urllib.parse import urlencode

class DifySSO:
    def __init__(self, dify_base_url, secret_key):
        self.dify_base_url = dify_base_url
        self.secret_key = secret_key
    
    def get_dify_token(self, email, password):
        """
        调用Dify登录API获取token
        
        Args:
            email: 用户邮箱
            password: 用户密码
            
        Returns:
            dict: {access_token, refresh_token} 或 None
        """
        login_url = f"{self.dify_base_url}/console/api/login"
        
        payload = {
            "email": email,
            "password": password
        }
        
        try:
            response = requests.post(login_url, json=payload, timeout=10)
            data = response.json()
            
            if data.get("result") == "success":
                return data.get("data")
            else:
                print(f"登录失败: {data.get('data')}")
                return None
                
        except Exception as e:
            print(f"请求失败: {e}")
            return None
```

**完整代码请查看**: `docs/SSO实现方案/代码示例/方案一/`

---

## 4. 方案二：自定义SSO端点方案

### 4.1 方案架构

此方案需要在Dify后端添加自定义SSO认证端点，支持通过共享密钥验证。

**详细实现请查看后续文档部分**

---

## 5. 安全措施与最佳实践

### 5.1 Token传输安全

1. **强制HTTPS**: 所有token传输必须使用HTTPS
2. **Token加密**: URL传递时对token进行加密
3. **时效性验证**: 添加timestamp参数，验证请求时效性

### 5.2 防止Token泄露

1. **不在URL中明文传递**: 使用POST或加密方式
2. **短期有效token**: 专门为SSO生成短期token（5分钟）
3. **一次性token**: Token使用后立即失效

### 5.3 CSRF防护

1. **State参数**: 添加随机state参数并验证
2. **Referer检查**: 验证请求来源
3. **SameSite Cookie**: 设置Cookie的SameSite属性

---

## 6. 部署指南

### 6.1 环境要求

- Dify版本: >= 0.6.0
- Python: >= 3.10
- Redis: 用于存储refresh token

### 6.2 配置说明

**Dify环境变量**:
```bash
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30
```

**网站A配置**:
```python
DIFY_BASE_URL=https://your-dify-domain.com
DIFY_SSO_SECRET=shared-secret-key
```

---

**下一步**: 查看详细代码实现和测试用例

