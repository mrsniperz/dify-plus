#!/bin/bash

echo "=== Dify Plus Workflow 修复脚本 ==="
echo ""

echo "1. 重启 web 服务（应用新的环境变量）："
docker compose -f docker-compose.dify-plus.yaml restart web

echo ""
echo "2. 重启 nginx 服务（应用新的路由配置）："
docker compose -f docker-compose.dify-plus.yaml restart nginx

echo ""
echo "3. 等待服务启动："
sleep 15

echo ""
echo "4. 检查 web 服务日志："
docker compose -f docker-compose.dify-plus.yaml logs --tail 10 web

echo ""
echo "5. 测试 workflow 访问："
echo "尝试访问: https://app.anyremote.cn:8333/workflow/24s0gG9vFpVixt3e"

echo ""
echo "6. 如果仍有问题，查看详细错误："
echo "docker compose -f docker-compose.dify-plus.yaml logs -f web"

echo ""
echo "=== 修复完成 ==="