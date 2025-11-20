#!/bin/bash

echo "=== Dify Plus 配置验证脚本 ==="
echo ""

echo "1. 验证 docker-compose.yaml 配置："
if docker compose -f docker-compose.dify-plus.yaml config > /dev/null 2>&1; then
    echo "✅ docker-compose.yaml 配置正确"
else
    echo "❌ docker-compose.yaml 配置有误："
    docker compose -f docker-compose.dify-plus.yaml config
    exit 1
fi

echo ""
echo "2. 检查 web 服务环境变量："
echo "关键的 SSR 相关环境变量："
docker compose -f docker-compose.dify-plus.yaml config | grep -A 20 "web:" | grep -E "(NEXT_|NODE_ENV|BROWSER|INTERNAL_API_URL)"

echo ""
echo "3. 验证 nginx 配置："
if [ -f "nginx/conf.d/default.conf" ]; then
    echo "✅ nginx 配置文件存在"
    echo "workflow 路由配置："
    grep -A 10 "workflow" nginx/conf.d/default.conf | head -15
else
    echo "❌ nginx 配置文件不存在"
fi

echo ""
echo "=== 验证完成 ==="