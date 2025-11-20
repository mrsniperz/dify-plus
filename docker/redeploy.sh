#!/bin/bash

# Dify Plus 重新部署脚本
# 用于修复 workflow 应用访问问题

echo "=== 开始重新部署 Dify Plus ==="

# 停止所有容器
echo "1. 停止现有容器..."
docker compose -f docker-compose.dify-plus.yaml down

# 清理旧的镜像和缓存
echo "2. 清理旧的镜像和缓存..."
docker system prune -f
docker image prune -f

# 清理旧的网络（如果存在）
echo "3. 清理网络..."
docker network prune -f

# 重新拉取最新镜像
echo "4. 拉取最新镜像..."
docker compose -f docker-compose.dify-plus.yaml pull

# 重新构建并启动服务
echo "5. 重新启动服务..."
docker compose -f docker-compose.dify-plus.yaml up -d --force-recreate

# 等待服务启动
echo "6. 等待服务启动..."
sleep 45

# 检查服务状态
echo "7. 检查服务状态..."
docker compose -f docker-compose.dify-plus.yaml ps

# 运行诊断脚本
echo "8. 运行诊断脚本..."
./debug-workflow.sh

echo ""
echo "=== 重新部署完成！ ==="
echo "请在浏览器中访问: https://app.anyremote.cn:8333"
echo ""
echo "如果仍有问题，请检查日志:"
echo "docker compose -f docker-compose.dify-plus.yaml logs -f nginx"
echo "docker compose -f docker-compose.dify-plus.yaml logs -f api"
echo "docker compose -f docker-compose.dify-plus.yaml logs -f web"
echo ""
echo "或运行诊断脚本:"
echo "./debug-workflow.sh"