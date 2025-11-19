"""
模块名称: website_a_sso_client.py
功能描述: 网站A的SSO客户端 - 方案二：自定义SSO端点
创建日期: 2025-11-19
作者: Cascade AI
版本: v1.0.0

使用说明:
1. 安装依赖: pip install fastapi requests pydantic
2. 配置环境变量: DIFY_BASE_URL, SSO_SHARED_SECRET
3. 运行服务: uvicorn website_a_sso_client:app --reload
"""

import os
import hmac
import hashlib
import time
from typing import Optional
from urllib.parse import urlencode

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel, EmailStr

# ============================================================================
# 配置部分
# ============================================================================

DIFY_BASE_URL = os.getenv("DIFY_BASE_URL", "http://localhost:5001")
SSO_SHARED_SECRET = os.getenv("SSO_SHARED_SECRET", "your-shared-secret-key")

app = FastAPI(title="Website A - SSO Client (方案二)", version="1.0.0")

# ============================================================================
# 数据模型
# ============================================================================

class SSOLoginRequest(BaseModel):
    """SSO登录请求模型"""
    email: EmailStr
    redirect_path: Optional[str] = "/"


# ============================================================================
# SSO客户端服务类
# ============================================================================

class DifySSOClient:
    """Dify SSO客户端服务类"""
    
    def __init__(self, base_url: str, shared_secret: str):
        self.base_url = base_url.rstrip('/')
        self.shared_secret = shared_secret
    
    def generate_sso_signature(self, email: str, timestamp: int) -> str:
        """
        生成SSO请求签名
        
        Args:
            email: 用户邮箱
            timestamp: 请求时间戳
            
        Returns:
            str: HMAC-SHA256签名
        """
        message = f"{email}:{timestamp}"
        signature = hmac.new(
            self.shared_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def generate_sso_url(self, email: str, redirect_path: str = "/") -> str:
        """
        生成SSO登录URL
        
        Args:
            email: 用户邮箱
            redirect_path: 登录后跳转路径
            
        Returns:
            str: 完整的SSO登录URL
        """
        timestamp = int(time.time())
        signature = self.generate_sso_signature(email, timestamp)
        
        params = {
            "email": email,
            "timestamp": timestamp,
            "signature": signature,
            "redirect": redirect_path
        }
        
        sso_url = f"{self.base_url}/console/api/sso/login?{urlencode(params)}"
        return sso_url
    
    def sso_login_post(self, email: str, redirect_path: str = "/") -> dict:
        """
        通过POST方式进行SSO登录
        
        Args:
            email: 用户邮箱
            redirect_path: 登录后跳转路径
            
        Returns:
            dict: 包含token的响应数据
            
        Raises:
            HTTPException: 当SSO登录失败时
        """
        timestamp = int(time.time())
        signature = self.generate_sso_signature(email, timestamp)
        
        sso_url = f"{self.base_url}/console/api/sso/login"
        
        payload = {
            "email": email,
            "timestamp": timestamp,
            "signature": signature,
            "redirect": redirect_path
        }
        
        try:
            response = requests.post(
                sso_url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            
            data = response.json()
            
            if data.get("result") == "success":
                return data.get("data")
            else:
                raise HTTPException(
                    status_code=401,
                    detail=f"SSO登录失败: {data.get('message', 'Unknown error')}"
                )
                
        except requests.RequestException as e:
            raise HTTPException(
                status_code=500,
                detail=f"无法连接到Dify服务: {str(e)}"
            )


# ============================================================================
# API路由
# ============================================================================

# 初始化SSO客户端
sso_client = DifySSOClient(DIFY_BASE_URL, SSO_SHARED_SECRET)


@app.get("/", response_class=HTMLResponse)
async def index():
    """首页 - SSO登录表单"""
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>网站A - SSO登录 (方案二)</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 400px;
                margin: 100px auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 { color: #333; margin-bottom: 20px; }
            input {
                width: 100%;
                padding: 10px;
                margin: 10px 0;
                border: 1px solid #ddd;
                border-radius: 4px;
                box-sizing: border-box;
            }
            button {
                width: 100%;
                padding: 12px;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            }
            button:hover { background: #5568d3; }
            .method { margin: 20px 0; }
            .method h3 { color: #666; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 SSO登录 (方案二)</h1>
            
            <div class="method">
                <h3>方法1: GET重定向</h3>
                <form action="/sso/redirect" method="get">
                    <input type="email" name="email" placeholder="邮箱地址" required>
                    <button type="submit">直接跳转到Dify</button>
                </form>
            </div>
            
            <div class="method">
                <h3>方法2: POST获取Token</h3>
                <input type="email" id="emailPost" placeholder="邮箱地址">
                <button onclick="ssoLoginPost()">获取Token并跳转</button>
            </div>
        </div>
        
        <script>
            async function ssoLoginPost() {
                const email = document.getElementById('emailPost').value;
                if (!email) {
                    alert('请输入邮箱地址');
                    return;
                }
                
                try {
                    const response = await fetch('/sso/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ email: email })
                    });
                    
                    const data = await response.json();
                    if (data.redirect_url) {
                        window.location.href = data.redirect_url;
                    }
                } catch (error) {
                    alert('登录失败: ' + error.message);
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/sso/redirect")
async def sso_redirect(email: str, redirect: str = "/"):
    """
    SSO重定向端点 (GET方式)
    
    功能描述: 生成SSO URL并重定向到Dify
    
    Args:
        email: 用户邮箱
        redirect: 登录后跳转路径
        
    Returns:
        RedirectResponse: 重定向到Dify SSO端点
    """
    sso_url = sso_client.generate_sso_url(email, redirect)
    return RedirectResponse(url=sso_url, status_code=302)


@app.post("/sso/login")
async def sso_login(request: SSOLoginRequest):
    """
    SSO登录端点 (POST方式)
    
    功能描述: 调用Dify SSO API获取token，返回前端跳转URL
    
    Args:
        request: SSO登录请求
        
    Returns:
        dict: 包含跳转URL的响应
    """
    token_data = sso_client.sso_login_post(
        email=request.email,
        redirect_path=request.redirect_path
    )
    
    # 构造前端回调URL
    frontend_url = DIFY_BASE_URL.replace('/api', '')  # 假设前端与API同域
    callback_url = f"{frontend_url}/sso-callback?access_token={token_data['access_token']}&refresh_token={token_data['refresh_token']}&redirect={token_data['redirect']}"
    
    return {
        "success": True,
        "redirect_url": callback_url,
        "message": "SSO登录成功"
    }

