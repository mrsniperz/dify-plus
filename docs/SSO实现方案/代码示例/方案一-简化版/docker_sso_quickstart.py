"""
模块名称: docker_sso_quickstart.py
功能描述: Docker部署环境下的Dify SSO快速实现（方案一简化版）
创建日期: 2025-11-19
作者: Cascade AI
版本: v1.0.0

特点：
- 专为Docker部署优化
- 10分钟内完成部署
- 无需修改Dify源码
- 无需连接数据库和Redis

使用方法：
1. pip install fastapi uvicorn requests
2. 修改下面的配置
3. uvicorn docker_sso_quickstart:app --host 0.0.0.0 --port 8000
"""

import os
from typing import Optional
from datetime import datetime

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, EmailStr

# ============================================================================
# 配置部分 - 请根据您的实际情况修改
# ============================================================================

# Dify API地址（Docker部署通常是 http://宿主机IP:5001）
DIFY_API_URL = os.getenv("DIFY_API_URL", "http://localhost:5001")

# Dify前端地址（Docker部署通常是 http://宿主机IP:3000）
DIFY_WEB_URL = os.getenv("DIFY_WEB_URL", "http://localhost:3000")

# ============================================================================
# FastAPI应用
# ============================================================================

app = FastAPI(
    title="Dify SSO - Docker快速版",
    description="适用于Docker部署的Dify单点登录方案",
    version="1.0.0"
)

# ============================================================================
# 数据模型
# ============================================================================

class LoginRequest(BaseModel):
    """登录请求模型"""
    email: EmailStr
    password: str


# ============================================================================
# 核心SSO逻辑
# ============================================================================

def call_dify_login_api(email: str, password: str) -> Optional[dict]:
    """
    调用Dify登录API获取token
    
    Args:
        email: 用户邮箱
        password: 用户密码
        
    Returns:
        dict: {access_token, refresh_token} 或 None
    """
    login_url = f"{DIFY_API_URL}/console/api/login"
    
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
            error_msg = data.get("data", "登录失败")
            print(f"[{datetime.now()}] 登录失败: {email} - {error_msg}")
            return None
            
    except Exception as e:
        print(f"[{datetime.now()}] API调用失败: {e}")
        return None


# ============================================================================
# API路由
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def index():
    """首页 - 简单的登录表单"""
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dify SSO登录</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                padding: 40px;
                max-width: 400px;
                width: 100%;
            }}
            h1 {{
                color: #333;
                margin-bottom: 10px;
                font-size: 28px;
                text-align: center;
            }}
            .subtitle {{
                color: #666;
                margin-bottom: 30px;
                font-size: 14px;
                text-align: center;
            }}
            .form-group {{
                margin-bottom: 20px;
            }}
            label {{
                display: block;
                margin-bottom: 8px;
                color: #555;
                font-weight: 500;
                font-size: 14px;
            }}
            input {{
                width: 100%;
                padding: 12px 15px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 14px;
                transition: all 0.3s;
            }}
            input:focus {{
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }}
            button {{
                width: 100%;
                padding: 14px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
            }}
            button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }}
            button:active {{
                transform: translateY(0);
            }}
            button:disabled {{
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }}
            .message {{
                margin-top: 20px;
                padding: 12px;
                border-radius: 8px;
                font-size: 14px;
                display: none;
                text-align: center;
            }}
            .message.success {{
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }}
            .message.error {{
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }}
            .loading {{
                display: none;
                text-align: center;
                margin-top: 20px;
            }}
            .spinner {{
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 10px;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            .info {{
                margin-top: 20px;
                padding: 15px;
                background: #e7f3ff;
                border-left: 4px solid #2196F3;
                border-radius: 4px;
                font-size: 12px;
                color: #1976D2;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Dify SSO</h1>
            <p class="subtitle">快速登录到Dify平台</p>
            
            <form id="loginForm">
                <div class="form-group">
                    <label for="email">邮箱地址</label>
                    <input 
                        type="email" 
                        id="email" 
                        name="email" 
                        required 
                        placeholder="your.email@example.com"
                        autocomplete="email"
                    >
                </div>
                
                <div class="form-group">
                    <label for="password">密码</label>
                    <input 
                        type="password" 
                        id="password" 
                        name="password" 
                        required 
                        placeholder="请输入密码"
                        autocomplete="current-password"
                    >
                </div>
                
                <button type="submit" id="submitBtn">
                    登录并跳转到Dify
                </button>
            </form>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p style="color: #666;">正在登录...</p>
            </div>
            
            <div class="message" id="message"></div>
            
            <div class="info">
                <strong>提示：</strong>使用您的Dify账号登录
            </div>
        </div>

        <script>
            const form = document.getElementById('loginForm');
            const submitBtn = document.getElementById('submitBtn');
            const loading = document.getElementById('loading');
            const message = document.getElementById('message');
            
            form.addEventListener('submit', async (e) => {{
                e.preventDefault();
                
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;
                
                // 显示加载状态
                submitBtn.disabled = true;
                loading.style.display = 'block';
                message.style.display = 'none';
                
                try {{
                    const response = await fetch('/api/sso/login', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{ email, password }})
                    }});
                    
                    const data = await response.json();
                    
                    if (response.ok && data.success) {{
                        showMessage('登录成功！正在跳转...', 'success');
                        
                        // 延迟跳转
                        setTimeout(() => {{
                            window.location.href = data.redirect_url;
                        }}, 1000);
                    }} else {{
                        showMessage(data.message || '登录失败，请检查账号密码', 'error');
                        submitBtn.disabled = false;
                    }}
                }} catch (error) {{
                    console.error('登录错误:', error);
                    showMessage('网络错误，请稍后重试', 'error');
                    submitBtn.disabled = false;
                }} finally {{
                    loading.style.display = 'none';
                }}
            }});
            
            function showMessage(text, type) {{
                message.textContent = text;
                message.className = `message ${{type}}`;
                message.style.display = 'block';
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/api/sso/login")
async def sso_login(request: LoginRequest):
    """
    SSO登录API
    
    功能：调用Dify API获取token，生成跳转URL
    """
    # 调用Dify登录API
    token_data = call_dify_login_api(request.email, request.password)
    
    if not token_data:
        raise HTTPException(
            status_code=401,
            detail="登录失败，请检查邮箱和密码是否正确"
        )
    
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    
    # 构造跳转URL（方式1：通过URL参数传递）
    redirect_url = f"{DIFY_WEB_URL}?sso_access_token={access_token}&sso_refresh_token={refresh_token}"
    
    print(f"[{datetime.now()}] SSO登录成功: {request.email}")
    
    return {
        "success": True,
        "redirect_url": redirect_url,
        "message": "登录成功"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "dify_api": DIFY_API_URL,
        "dify_web": DIFY_WEB_URL
    }


# ============================================================================
# 启动说明
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Dify SSO - Docker快速版")
    print("=" * 60)
    print(f"Dify API: {DIFY_API_URL}")
    print(f"Dify Web: {DIFY_WEB_URL}")
    print("=" * 60)
    print("启动命令: uvicorn docker_sso_quickstart:app --host 0.0.0.0 --port 8000")
    print("访问地址: http://localhost:8000")
    print("=" * 60)

