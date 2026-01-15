# 安装claude-mem

```bash
# Clone the repository
git clone https://github.com/thedotmack/claude-mem.git
cd claude-mem

# Install dependencies
npm install

# Build hooks and worker service
npm run build

# Worker service will auto-start on first Claude Code session
# Or manually start with:
npm run worker:start

# Verify worker is running
npm run worker:status
```

# windows wsl下启动和管理方法

进入目录：/home/x1/.claude/plugins/marketplaces/thedotmack

# mac 

进入目录：/Users/sniperz/.claude/plugins/marketplaces/thedotmack

```bash
npm run worker:start

# 2. 确认进程在 PM2 列表里
pm2 list
# 输出里应该有 claude-mem-worker 是 online 状态

# 3. 再保存 + 设置开机自启
pm2 save
pm2 startup

# 4. 设置不开机启动
pm2 delete claude-mem-worker
pm2 unstartup
```

## 🛠️ 解决重复进程问题

### **1. 停止重复的进程**

根据您的输出，您现在有两个 claude-mem-worker 进程（ID 0 和 ID 1），其中 ID 0 正在停止中。让我帮您清理：

```bash
# 首先，停止所有 claude-mem-worker 进程
pm2 stop claude-mem-worker

# 或者按 ID 停止特定进程
pm2 stop 0
pm2 stop 1

# 删除重复的进程（彻底移除）
pm2 delete 0
pm2 delete 1

# 验证是否都停止了
pm2 list
```

### **管理命令速查**

```bash
# 查看进程状态
pm2 list

# 停止进程
pm2 stop claude-mem-worker
# 或
pm2 stop <id>

# 重启进程
pm2 restart claude-mem-worker

# 删除进程
pm2 delete claude-mem-worker

# 查看日志
pm2 logs claude-mem-worker

# 监控资源使用
pm2 monit

# 保存当前进程列表
pm2 save

# 重新加载保存的进程
pm2 resurrect
```
