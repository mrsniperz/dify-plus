"""
模块名称: website_a_backend.py
功能描述: 网站A后端SSO集成示例 - 方案一：API Token传递
创建日期: 2025-11-19
作者: Cascade AI
版本: v1.0.0

使用说明:
1. 安装依赖: pip install fastapi requests pydantic cryptography
2. 配置环境变量: DIFY_BASE_URL, DIFY_SSO_SECRET
3. 运行服务: uvicorn website_a_backend:app --reload
"""

import os
import hmac
import hashlib
import time
import secrets
from typing import Optional
from datetime import datetime, timedelta
from urllib.parse import urlencode, quote

import requests
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from cryptography.fernet import Fernet

# ============================================================================
# 配置部分
# ============================================================================

DIFY_BASE_URL = os.getenv("DIFY_BASE_URL", "http://localhost:5001")
DIFY_SSO_SECRET = os.getenv("DIFY_SSO_SECRET", "your-shared-secret-key")
ENCRYPTION_KEY = Fernet.generate_key()  # 生产环境应从环境变量读取
cipher_suite = Fernet(ENCRYPTION_KEY)

app = FastAPI(title="Website A - SSO Integration", version="1.0.0")

# ============================================================================
# 数据模型
# ============================================================================

class SSORequest(BaseModel):
    """SSO请求模型"""
    email: EmailStr
    password: str
    redirect_url: Optional[str] = None


class SSOResponse(BaseModel):
    """SSO响应模型"""
    success: bool
    redirect_url: Optional[str] = None
    message: str


# ============================================================================
# 核心SSO服务类
# ============================================================================

class DifySSO:
    """Dify单点登录服务类"""
    
    def __init__(self, base_url: str, secret_key: str):
        self.base_url = base_url.rstrip('/')
        self.secret_key = secret_key
    
    def get_dify_token(self, email: str, password: str) -> Optional[dict]:
        """
        调用Dify登录API获取token
        
        Args:
            email: 用户邮箱
            password: 用户密码
            
        Returns:
            dict: {access_token, refresh_token} 或 None
            
        Raises:
            HTTPException: 当API调用失败时
        """
        login_url = f"{self.base_url}/console/api/login"
        
        payload = {
            "email": email,
            "password": password
        }
        
        try:
            response = requests.post(
                login_url, 
                json=payload, 
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            
            data = response.json()
            
            if data.get("result") == "success":
                return data.get("data")
            else:
                error_msg = data.get("data", "Unknown error")
                raise HTTPException(status_code=401, detail=f"Dify登录失败: {error_msg}")
                
        except requests.RequestException as e:
            raise HTTPException(status_code=500, detail=f"无法连接到Dify服务: {str(e)}")
    
    def generate_sso_url(self, access_token: str, refresh_token: str, 
                         redirect_path: str = "/") -> str:
        """
        生成SSO跳转URL
        
        Args:
            access_token: Dify访问令牌
            refresh_token: Dify刷新令牌
            redirect_path: 跳转后的路径
            
        Returns:
            str: 完整的SSO跳转URL
        """
        # 加密token以提高安全性
        encrypted_access = cipher_suite.encrypt(access_token.encode()).decode()
        encrypted_refresh = cipher_suite.encrypt(refresh_token.encode()).decode()
        
        # 生成时间戳和签名
        timestamp = int(time.time())
        signature = self._generate_signature(encrypted_access, timestamp)
        
        # 构造URL参数
        params = {
            "sso_token": encrypted_access,
            "refresh_token": encrypted_refresh,
            "timestamp": timestamp,
            "signature": signature,
            "redirect": redirect_path
        }
        
        # 返回完整URL
        sso_url = f"{self.base_url}/sso/auto-login?{urlencode(params)}"
        return sso_url
    
    def _generate_signature(self, token: str, timestamp: int) -> str:
        """
        生成请求签名
        
        Args:
            token: 加密后的token
            timestamp: 时间戳
            
        Returns:
            str: HMAC签名
        """
        message = f"{token}:{timestamp}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature


# ============================================================================
# API路由
# ============================================================================

# 初始化SSO服务
sso_service = DifySSO(DIFY_BASE_URL, DIFY_SSO_SECRET)

@app.post("/api/sso/login", response_model=SSOResponse)
async def sso_login(request: SSORequest):
    """
    SSO登录端点
    
    功能描述: 接收用户凭证，调用Dify API获取token，生成SSO跳转URL
    
    Args:
        request: SSO请求对象
        
    Returns:
        SSOResponse: 包含跳转URL的响应
    """
    # 获取Dify token
    token_data = sso_service.get_dify_token(request.email, request.password)
    
    if not token_data:
        raise HTTPException(status_code=401, detail="认证失败")
    
    # 生成SSO跳转URL
    redirect_path = request.redirect_url or "/"
    sso_url = sso_service.generate_sso_url(
        access_token=token_data["access_token"],
        refresh_token=token_data["refresh_token"],
        redirect_path=redirect_path
    )
    
    return SSOResponse(
        success=True,
        redirect_url=sso_url,
        message="SSO URL生成成功"
    )

