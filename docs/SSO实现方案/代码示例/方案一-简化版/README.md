# Dify SSO - 方案一简化版 (Docker快速启动)

> 🚀 **目标**: 10分钟内实现从外部网站到Dify的单点登录

---

## 📋 方案概述

本方案是**方案一（调用Dify API）**的简化版，专为Docker部署环境设计。它将网站A的后端和前端集成到一个Python脚本中，让您可以通过一个命令快速启动并测试SSO流程。

### 工作流程

1.  **用户访问**：用户访问 `http://localhost:8000`，看到一个登录页面。
2.  **提交凭证**：用户输入Dify的账号密码。
3.  **获取Token**：脚本后端调用Dify的 `/console/api/login` 接口，获取 `access_token` 和 `refresh_token`。
4.  **构造URL**：脚本将获取到的tokens作为URL参数，构造一个指向Dify前端的URL。
5.  **重定向**：浏览器跳转到Dify前端，URL中包含tokens。
6.  **前端处理**：Dify前端通过一段简单的JavaScript代码，从URL中读取tokens并存储到 `localStorage`。
7.  **自动登录**：Dify前端检测到 `localStorage` 中的token，自动完成登录。

---

## 🚀 快速启动步骤

### 步骤1: 安装依赖

```bash
pip install fastapi uvicorn requests
```

### 步骤2: 配置Dify地址

打开 `docker_sso_quickstart.py` 文件，根据您的实际情况修改顶部的配置：

```python
# Dify API地址（Docker部署通常是 http://宿主机IP:5001）
DIFY_API_URL = os.getenv("DIFY_API_URL", "http://localhost:5001")

# Dify前端地址（Docker部署通常是 http://宿主机IP:3000）
DIFY_WEB_URL = os.getenv("DIFY_WEB_URL", "http://localhost:3000")
```

### 步骤3: 启动服务

在 `方案一-简化版` 目录下运行：

```bash
uvicorn docker_sso_quickstart:app --host 0.0.0.0 --port 8000
```

### 步骤4: 访问登录页面

在浏览器中打开 `http://localhost:8000`。

---

## 🔧 Dify前端配置 (关键步骤)

由于我们不修改Dify源码，需要让Dify前端能够处理URL中的token。最简单的方式是在Dify前端的 `index.html` 中加入一小段JavaScript代码。

### 步骤1: 找到Dify前端的 `index.html`

如果您是通过Docker部署的，这个文件在 **web** 服务的镜像里。您可以通过挂载或修改镜像的方式来更新它。

一个更简单的方法是，如果您使用Nginx作为反向代理，可以通过Nginx注入这段脚本。

### 步骤2: 添加脚本

将以下脚本添加到 `index.html` 的 `<body>` 标签底部：

```html
<!-- Dify SSO Token Handler Start -->
<script>
  (function() {
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const accessToken = urlParams.get('sso_access_token');
      const refreshToken = urlParams.get('sso_refresh_token');

      if (accessToken) {
        // 存储token到localStorage
        localStorage.setItem('console_token', accessToken);
        console.log('SSO: Access token stored.');
      }

      if (refreshToken) {
        localStorage.setItem('refresh_token', refreshToken);
        console.log('SSO: Refresh token stored.');
      }

      // 如果成功存储了token，清理URL并重新加载页面
      if (accessToken || refreshToken) {
        // 移除URL中的敏感参数
        urlParams.delete('sso_access_token');
        urlParams.delete('sso_refresh_token');
        
        const newUrl = window.location.pathname + '?' + urlParams.toString();
        
        // 使用replaceState而不是pushState，避免污染浏览器历史
        window.history.replaceState({}, document.title, newUrl);
        
        // 重新加载页面以让Dify应用识别token
        window.location.reload();
      }
    } catch (error) {
      console.error('Dify SSO Handler Error:', error);
    }
  })();
</script>
<!-- Dify SSO Token Handler End -->
```

### 为什么需要这段代码？

-   **读取Token**：从URL参数 `sso_access_token` 和 `sso_refresh_token` 中获取令牌。
-   **存储Token**：将令牌存入 `localStorage`，这是Dify前端识别登录状态的地方。
-   **清理URL**：移除URL中的敏感token信息，提高安全性。
-   **重新加载**：刷新页面，让Dify的前端应用能够读取到新的token并更新UI为登录状态。

---

## 💡 总结

这个简化版方案为您提供了一个**功能完整**且**易于部署**的SSO原型。您可以基于此快速验证SSO流程，并根据需要将其逻辑集成到您现有的网站A中。

