#!/bin/bash

echo "=== Dify Plus Workflow 问题诊断脚本 ==="
echo ""

echo "1. 检查服务状态："
docker compose -f docker-compose.dify-plus.yaml ps

echo ""
echo "2. 检查网络连通性："
echo "=== 使用 wget 检查 web 容器是否能访问 api 容器 ==="
docker compose -f docker-compose.dify-plus.yaml exec web wget -q -O - http://api:5001/console/api/apps 2>/dev/null | head -c 100 || echo "❌ web -> api 连接失败"

echo ""
echo "=== 使用 wget 检查 nginx 容器是否能访问 web 容器 ==="
docker compose -f docker-compose.dify-plus.yaml exec nginx wget -q -O - http://web:3000/ 2>/dev/null | head -c 100 || echo "❌ nginx -> web 连接失败"

echo ""
echo "3. 测试 workflow 路径："
echo "=== 直接访问 web 容器的 workflow 路径 ==="
docker compose -f docker-compose.dify-plus.yaml exec web wget -q -O - "http://localhost:3000/workflow/24s0gG9vFpVixt3e" 2>/dev/null | head -c 100 || echo "❌ 直接访问 web 容器 workflow 失败"

echo ""
echo "=== 通过正确的 nginx 端口访问 workflow 路径 ==="
docker compose -f docker-compose.dify-plus.yaml exec nginx wget -q -O - "http://localhost:8183/workflow/24s0gG9vFpVixt3e" 2>/dev/null | head -c 100 || echo "❌ 通过 nginx 8183 端口访问 workflow 失败"

echo ""
echo "4. 检查环境变量："
echo "=== web 容器环境变量 ==="
docker compose -f docker-compose.dify-plus.yaml exec web env | grep -E "(API_URL|CONSOLE_|APP_|INTERNAL_)"

echo ""
echo "5. 检查最近的错误日志："
echo "=== web 容器最近的错误日志 ==="
docker compose -f docker-compose.dify-plus.yaml logs --tail 20 web

echo ""
echo "=== nginx 容器最近的错误日志 ==="
docker compose -f docker-compose.dify-plus.yaml logs --tail 20 nginx

echo ""
echo "6. 测试 API 端点："
echo "=== 测试 console API ==="
docker compose -f docker-compose.dify-plus.yaml exec nginx wget -q -O - "http://localhost:8183/console/api/apps" 2>/dev/null | head -c 100 || echo "❌ console API 访问失败"

echo ""
echo "=== 测试 API 健康检查 ==="
docker compose -f docker-compose.dify-plus.yaml exec nginx wget -q -O - "http://api:5001/console/api/apps" 2>/dev/null | head -c 100 || echo "❌ API 健康检查失败"

echo ""
echo "=== 检查 web 容器内 Next.js 进程 ==="
docker compose -f docker-compose.dify-plus.yaml exec web ps aux || echo "❌ 无法检查 web 容器进程"

echo ""
echo "=== 诊断完成 ==="