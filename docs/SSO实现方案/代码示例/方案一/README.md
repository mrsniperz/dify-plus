# Dify SSO 方案一：实施指南 (调用API)

> 🚀 **目标**: 快速、安全地实现Dify单点登录，无需修改Dify源码。

---

## 📋 方案概述

本方案通过在您的网站A后端调用Dify官方的登录API来获取认证令牌（`access_token`和`refresh_token`），然后将这些令牌安全地传递给前端，最终由Dify的前端应用完成自动登录。

### 核心优势

-   ✅ **非侵入式**：完全无需修改Dify的后端源代码或Docker镜像。
-   ✅ **高安全性**：遵循Dify设计的标准认证流程，不暴露数据库或`SECRET_KEY`。
-   ✅ **易于维护**：与Dify核心逻辑解耦，未来Dify升级不影响SSO功能。
-   ✅ **快速实现**：整个流程可在30分钟内完成部署和测试。

### 工作流程

1.  **用户登录网站A**：用户在您的网站A上完成身份认证。
2.  **触发SSO**：用户点击一个“进入Dify”的链接或按钮。
3.  **后端获取Token**：网站A的后端服务调用Dify的`/console/api/login`接口，使用预置的Dify管理员或特定账户的凭证，获取有效的tokens。
4.  **安全跳转**：网站A后端构建一个指向Dify前端的URL，并将获取到的tokens作为参数附在URL上。
5.  **前端处理Token**：Dify前端页面通过一段注入的JavaScript脚本，从URL中捕获tokens，并将它们存入浏览器的`localStorage`。
6.  **无缝登录**：脚本清理URL并刷新页面，Dify应用检测到`localStorage`中的tokens，自动完成登录，对用户全程无感。

---

## 🚀 实施步骤

### 步骤1：部署网站A后端服务

此服务负责与Dify API通信并生成跳转链接。

1.  **代码文件**：`website_a_backend.py`
2.  **安装依赖**：
    ```bash
    pip install fastapi uvicorn requests pydantic cryptography
    ```
3.  **配置环境变量**：
    ```bash
    # Dify API的访问地址
    export DIFY_BASE_URL="http://<您的Dify服务器IP>:5001"

    # 用于URL签名和加密的密钥（请替换为强随机字符串）
    export DIFY_SSO_SECRET="your-strong-random-secret-key"
    ```
4.  **启动服务**：
    ```bash
    uvicorn website_a_backend:app --host 0.0.0.0 --port 8000
    ```

### 步骤2：部署网站A前端页面

这是一个简单的HTML页面，用于模拟用户从您的网站A发起SSO请求。

1.  **代码文件**：`website_a_frontend.html`
2.  **配置API地址**：
    打开`website_a_frontend.html`，修改JavaScript部分中的`API_BASE_URL`，使其指向您刚刚部署的后端服务。
    ```javascript
    const API_BASE_URL = 'http://<您的网站A后端IP>:8000';
    ```
3.  **访问页面**：
    直接在浏览器中打开此HTML文件，或将其部署到Web服务器。

### 步骤3：配置Dify前端（关键）

为了让Dify能够接收并处理我们传递的token，需要在Dify前端页面注入一个处理器脚本。

1.  **脚本文件**：`dify_frontend_handler.js` (本目录中已提供)
2.  **注入方法**：最佳方式是通过反向代理（如Nginx）注入，这样无需修改Dify的Docker镜像。

    **Nginx配置示例**：
    编辑您用于代理Dify前端（通常是3000端口）的Nginx配置文件。

    ```nginx
    server {
        listen 80;
        server_name your-dify-domain.com;

        # ... 其他配置 ...

        location / {
            proxy_pass http://localhost:3000;
            proxy_set_header Host $host;
            # ... 其他proxy配置 ...

            # --- SSO脚本注入 --- 
            # 在</body>标签前注入我们的处理器脚本
            sub_filter '</body>' '<script src="/sso_handler.js"></script></body>';
            sub_filter_once on;
        }

        # 让Nginx能够提供这个JS文件
        location /sso_handler.js {
            # 将dify_frontend_handler.js文件放在这个路径下
            alias /path/to/your/sso/scripts/dify_frontend_handler.js;
            types { application/javascript js; }
        }
    }
    ```

3.  **重启Nginx**：
    ```bash
    sudo systemctl restart nginx
    ```

---

## 🧪 测试流程

1.  确保Dify服务、网站A后端服务和Nginx都已正确配置并启动。
2.  在浏览器中访问您的网站A前端页面（例如`http://<网站A后端IP>:8000`）。
3.  输入一个有效的Dify用户邮箱和密码。
4.  点击“登录并跳转到Dify”按钮。
5.  观察浏览器行为：
    *   应短暂跳转到一个带有`sso_token`参数的Dify URL。
    *   页面会自动刷新，URL中的token参数会消失。
    *   Dify页面加载完成，并显示为已登录状态。

如果以上步骤均符合预期，恭喜您，SSO已成功实现！

