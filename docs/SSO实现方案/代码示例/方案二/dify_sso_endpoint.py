"""
模块名称: dify_sso_endpoint.py
功能描述: Dify后端自定义SSO端点 - 方案二：自定义SSO端点
创建日期: 2025-11-19
作者: Cascade AI
版本: v1.0.0

部署位置: api/controllers/console/auth/sso_extend.py

使用说明:
1. 将此文件复制到 api/controllers/console/auth/ 目录
2. 在 api/controllers/console/auth/__init__.py 中导入
3. 配置环境变量 SSO_SHARED_SECRET
4. 重启Dify服务
"""

import hmac
import hashlib
import time
from datetime import datetime, timedelta, UTC
from typing import Optional

from flask import request, redirect
from flask_restful import Resource, reqparse
from werkzeug.exceptions import Unauthorized, BadRequest

from configs import dify_config
from extensions.ext_database import db
from libs.helper import extract_remote_ip
from libs.passport import PassportService
from models.account import Account, AccountStatus
from services.account_service import AccountService, TokenPair

from .. import api


# ============================================================================
# 配置部分
# ============================================================================

# SSO共享密钥，应与外部网站A保持一致
SSO_SHARED_SECRET = dify_config.SSO_SHARED_SECRET if hasattr(dify_config, 'SSO_SHARED_SECRET') else "your-shared-secret-key"

# SSO Token有效期（秒）
SSO_TOKEN_VALIDITY = 300  # 5分钟


# ============================================================================
# SSO服务类
# ============================================================================

class SSOService:
    """SSO认证服务类"""
    
    @staticmethod
    def verify_signature(email: str, timestamp: int, signature: str) -> bool:
        """
        验证SSO请求签名
        
        Args:
            email: 用户邮箱
            timestamp: 请求时间戳
            signature: 请求签名
            
        Returns:
            bool: 签名是否有效
        """
        # 检查时间戳有效性（防止重放攻击）
        current_time = int(time.time())
        if abs(current_time - timestamp) > SSO_TOKEN_VALIDITY:
            return False
        
        # 生成期望的签名
        message = f"{email}:{timestamp}"
        expected_signature = hmac.new(
            SSO_SHARED_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # 使用恒定时间比较防止时序攻击
        return hmac.compare_digest(signature, expected_signature)
    
    @staticmethod
    def authenticate_user(email: str) -> Optional[Account]:
        """
        通过邮箱认证用户
        
        Args:
            email: 用户邮箱
            
        Returns:
            Account: 用户账户对象或None
        """
        account = db.session.query(Account).filter_by(email=email).first()
        
        if not account:
            return None
        
        if account.status == AccountStatus.BANNED.value:
            raise Unauthorized("账户已被禁用")
        
        return account
    
    @staticmethod
    def create_sso_token(account: Account) -> TokenPair:
        """
        为SSO用户创建token
        
        Args:
            account: 用户账户对象
            
        Returns:
            TokenPair: 访问令牌对
        """
        # 更新登录信息
        ip_address = extract_remote_ip(request)
        if ip_address:
            AccountService.update_login_info(account=account, ip_address=ip_address)
        
        # 激活待激活账户
        if account.status == AccountStatus.PENDING.value:
            account.status = AccountStatus.ACTIVE.value
            db.session.commit()
        
        # 生成token
        token_pair = AccountService.login(account=account, ip_address=ip_address)
        
        return token_pair


# ============================================================================
# API端点
# ============================================================================

class SSOLoginApi(Resource):
    """
    SSO登录API端点
    
    功能描述: 接收来自外部网站的SSO请求，验证签名后自动登录用户
    
    请求参数:
        - email: 用户邮箱
        - timestamp: 请求时间戳
        - signature: HMAC-SHA256签名
        - redirect: 登录后跳转路径（可选）
    
    响应:
        - 成功: 重定向到Dify前端并设置token
        - 失败: 返回错误信息
    """
    
    def get(self):
        """处理SSO GET请求"""
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, required=True, location='args')
        parser.add_argument('timestamp', type=int, required=True, location='args')
        parser.add_argument('signature', type=str, required=True, location='args')
        parser.add_argument('redirect', type=str, required=False, location='args', default='/')
        args = parser.parse_args()
        
        # 验证签名
        if not SSOService.verify_signature(args['email'], args['timestamp'], args['signature']):
            raise Unauthorized("SSO签名验证失败")
        
        # 认证用户
        account = SSOService.authenticate_user(args['email'])
        if not account:
            raise Unauthorized("用户不存在")
        
        # 生成token
        token_pair = SSOService.create_sso_token(account)
        
        # 构造重定向URL，将token传递给前端
        frontend_url = dify_config.CONSOLE_WEB_URL or "http://localhost:3000"
        redirect_url = f"{frontend_url}/sso-callback?access_token={token_pair.access_token}&refresh_token={token_pair.refresh_token}&redirect={args['redirect']}"
        
        return redirect(redirect_url, code=302)
    
    def post(self):
        """处理SSO POST请求"""
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, required=True, location='json')
        parser.add_argument('timestamp', type=int, required=True, location='json')
        parser.add_argument('signature', type=str, required=True, location='json')
        parser.add_argument('redirect', type=str, required=False, location='json', default='/')
        args = parser.parse_args()
        
        # 验证签名
        if not SSOService.verify_signature(args['email'], args['timestamp'], args['signature']):
            return {"result": "fail", "message": "SSO签名验证失败"}, 401
        
        # 认证用户
        account = SSOService.authenticate_user(args['email'])
        if not account:
            return {"result": "fail", "message": "用户不存在"}, 401
        
        # 生成token
        token_pair = SSOService.create_sso_token(account)
        
        return {
            "result": "success",
            "data": {
                "access_token": token_pair.access_token,
                "refresh_token": token_pair.refresh_token,
                "redirect": args['redirect']
            }
        }


# 注册API路由
api.add_resource(SSOLoginApi, "/sso/login")

