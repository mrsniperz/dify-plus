/**
 * Dify SSO Token Handler
 * 
 * 功能:
 * 1. 从URL参数中获取access_token和refresh_token
 * 2. 将token存储到localStorage，供Dify应用使用
 * 3. 清理URL中的敏感token信息，提高安全性
 * 4. 重新加载页面，让Dify应用识别登录状态
 * 
 * 使用方法:
 * 将此脚本添加到Dify前端的 index.html 文件 <body> 标签底部。
 */

(function() {
  try {
    const urlParams = new URLSearchParams(window.location.search);
    const accessToken = urlParams.get('sso_access_token');
    const refreshToken = urlParams.get('sso_refresh_token');

    // 检查URL中是否存在token
    if (accessToken || refreshToken) {
      console.log('SSO Handler: Detected SSO tokens in URL.');

      if (accessToken) {
        // 存储access_token到localStorage
        localStorage.setItem('console_token', accessToken);
        console.log('SSO Handler: Access token stored successfully.');
      }

      if (refreshToken) {
        // 存储refresh_token到localStorage
        localStorage.setItem('refresh_token', refreshToken);
        console.log('SSO Handler: Refresh token stored successfully.');
      }

      // 从URL中移除敏感参数，避免token泄露
      urlParams.delete('sso_access_token');
      urlParams.delete('sso_refresh_token');
      
      // 构建新的、干净的URL
      // 使用 history.replaceState() 替换当前历史记录，避免用户点击后退按钮回到带token的URL
      const newUrl = window.location.pathname + (urlParams.toString() ? '?' + urlParams.toString() : '');
      window.history.replaceState({ path: newUrl }, document.title, newUrl);
      
      console.log('SSO Handler: URL cleaned. Reloading page...');
      
      // 重新加载页面，让Dify的前端应用能够读取新的token并更新UI为登录状态
      window.location.reload();
    }
  } catch (error) {
    console.error('Dify SSO Handler Error:', error);
  }
})();

