# PostgreSQL 密码认证失败 - 故障排查与解决方案

## 问题描述

### 错误症状
```log
plugin_daemon-1  | 2026/01/15 06:58:40 [error] failed to initialize database, got error failed to connect to `host=db user=postgres database=dify_plugin`: failed SASL auth (FATAL: password authentication failed for user "postgres" (SQLSTATE 28P01))
db-1             | 2026-01-15 06:57:48.342 UTC [487] FATAL:  password authentication failed for user "postgres"
api-1            | sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) FATAL:  password authentication failed for user "postgres"
web-1             | status: 137 (Killed by OOM Killer)
```

### 核心问题
PostgreSQL 密码认证失败，导致：
- `plugin_daemon` 无法启动（panic）
- `api`、`worker`、`beat` 无法连接数据库
- `nginx` 无法代理到 API 服务（502 错误）
- `web` 容器因内存不足被 kill（status: 137）

---

## 问题原因

### 根本原因
**Docker volume 中已有 PostgreSQL 数据，使用的密码与当前配置的密码不一致。**

当你之前运行过 Dify（或其他使用 PostgreSQL 的项目），Docker volume `docker_db-data` 中已经保存了 PostgreSQL 数据目录。这个数据目录包含了：
- 数据库文件
- 用户认证信息
- 加密后的密码哈希

当你再次启动 Docker Compose 时，即使 `.env` 文件中设置了新密码 `difyai123456`，PostgreSQL 容器仍然使用 volume 中的旧密码进行认证。

### 详细分析

1. **数据库初始化流程**
   ```
   PostgreSQL 容器启动
   ↓
   读取 PGDATA 中的数据（如果 volume 存在）
   ↓
   使用数据目录中保存的密码进行用户认证
   ↓
   环境变量中的密码（DB_PASSWORD）
   ↓
   ❌ 认证失败（密码不匹配）
   ```

2. **为什么无法直接修改密码**
   - PostgreSQL 的密码是存储在数据目录中的
   - 重新设置密码需要：
     1. 访问数据库
     2. 修改 `pg_hba.conf`
     3. 重启 PostgreSQL 服务
   - 或者完全重新初始化数据目录

3. **为什么会尝试 ALTER USER 失败**
   ```
   docker compose exec db bash
   ↓
   psql -U postgres -d dify
   ↓
   ❌ ERROR: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed
   ↓
   原因：PostgreSQL 服务未启动完成，socket 文件不存在
   ```

---

## 解决方案

### 方案 1：删除 volume 重新部署（推荐，最简单）⭐

**适用场景**：首次部署或可以接受数据丢失

**优点**：
- ✅ 最简单直接
- ✅ 彻底解决密码不匹配问题
- ✅ 确保环境干净

**缺点**：
- ⚠️ 会丢失所有现有数据（用户、应用、数据集等）

**操作步骤**：
```bash
# 1. 停止所有服务
cd /root/docker
docker compose -f docker-compose.dify-plus.yaml down

# 2. 删除数据库 volume（会丢失所有数据）
docker volume rm docker_db-data

# 3. 重新启动（会使用新密码创建数据库）
docker compose -f docker-compose.dify-plus.yaml up -d

# 4. 检查启动状态
docker compose -f docker-compose.dify-plus.yaml ps
docker compose -f docker-compose.dify-plus.yaml logs -f db --tail 20
```

---

### 方案 2：临时停止 db 容器，修改 volume 中的密码文件（保留数据）

**适用场景**：需要保留现有数据

**优点**：
- ✅ 保留现有数据
- ✅ 可以修改密码

**缺点**：
- ⚠️ 需要手动操作
- ⚠️ 如果数据已经加密或损坏，可能无法访问
- ⚠️ 操作复杂度中等

**操作步骤**：
```bash
# 1. 停止所有服务
cd /root/docker
docker compose -f docker-compose.dify-plus.yaml down

# 2. 启动 db 容器但阻止进程启动（这样 volume 会被挂载但不会执行初始化）
docker compose -f docker-compose.dify-plus.yaml up db --no-deps --scale db=1

# 3. 在另一个终端，进入容器修改密码
docker compose -f docker-compose.dify-plus.yaml exec db bash

# 4. 在容器内执行 SQL 修改密码
psql -U postgres -d dify
\password
输入当前密码（根据错误日志中的提示）
# 如果不知道当前密码，查看 pg_hba.conf
\q
SELECT * FROM pg_shadow;
# 退出容器
\q
exit

# 5. 退出容器并重启所有服务
docker compose -f docker-compose.dify-plus.yaml down
docker compose -f docker-compose.dify-plus.yaml up -d

# 6. 检查日志确认数据库启动
docker compose -f docker-compose.dify-plus.yaml logs -f db --tail 20
```

**详细说明**：
1. `--no-deps` 参数会启动 db 容器但不启动依赖服务（如 api、worker）
2. 进入容器后，`psql` 可能会提示输入密码
3. 成功修改后，退出容器并重启所有服务
4. 如果不记得当前密码，需要查看 `docker/volumes/db/data` 中的配置文件

---

### 方案 3：检查并修改环境变量（保守方案）

**适用场景**：不确定密码或配置问题

**操作步骤**：
```bash
# 1. 检查当前 .env 中的密码设置
cd /root/docker
cat .env | grep DB_PASSWORD

# 2. 如果密码不是 difyai123456，编辑 .env 文件
nano .env
# 或
vim .env

# 3. 修改这一行（大约在第 85 行）
DB_PASSWORD=difyai123456

# 4. 保存后重启服务
docker compose -f docker-compose.dify-plus.yaml down
docker compose -f docker-compose.dify-plus.yaml up -d

# 5. 检查日志
docker compose -f docker-compose.dify-plus.yaml logs -f db --tail 30
docker compose -f docker-compose.dify-plus.yaml logs -f api --tail 20
docker compose -f docker-compose.dify-plus.yaml logs -f plugin_daemon --tail 20
```

**说明**：
- 这个方案适用于密码配置错误的情况
- 如果 volume 中的密码与配置不同，这个方案不会生效
- 此时应该选择方案 1 或方案 2

---

## 推荐操作流程（最佳实践）

### 如果不介意丢失数据，强烈推荐方案 1

1. **停止所有服务**
   ```bash
   cd /root/docker
   docker compose -f docker-compose.dify-plus.yaml down
   ```

2. **删除数据库 volume**
   ```bash
   docker volume rm docker_db-data
   ```

3. **重新启动**
   ```bash
   docker compose -f docker-compose.dify-plus.yaml up -d
   ```

4. **检查启动状态**
   ```bash
   # 检查所有容器状态
   docker compose -f docker-compose.dify-plus.yaml ps

   # 检查数据库日志
   docker compose -f docker-compose.dify-plus.yaml logs -f db --tail 20

   # 检查 API 日志
   docker compose -f docker-compose.dify-plus.yaml logs -f api --tail 20

   # 检查 plugin_daemon 日志
   docker compose -f docker-compose.dify-plus.yaml logs -f plugin_daemon --tail 20
   ```

5. **访问 Web 界面验证**
   ```
   # 打开浏览器访问
   https://app.anyremote.cn:8333
   ```

---

## 验证成功标准

执行上述方案后，如果问题解决，应该看到：

### 1. 数据库日志
```log
db-1             | 2026-01-15 06:58:40 database system is ready to accept connections
db-1             | LOG:  database system was shut down at 2026-01-15 06:58:39
db-1             | LOG:  starting PostgreSQL 15.6 on x86_64-unknown-linux-musl
db-1             | LOG:  redirecting log output to logging collector process
db-1             | LOG:  background writer process started
db-1             | LOG:  database system is ready to accept connections
```

### 2. API 服务日志
```log
api-1            | Running migrations
api-1            | Starting API server on 0.0.0.0:5001
api-1            | Application startup complete
```

### 3. plugin_daemon 日志
```log
plugin_daemon-1   | 2026/01/15 14:56:48 [INFO]init routine pool, size: 10000
plugin_daemon-1   | 2026/01/15 14:56:48 database connected successfully
```

### 4. Nginx 日志
```log
nginx-1          | 2026/01/15 14:58:00 connect() failed (111: Connection refused)  # API 启动前可能看到
nginx-1          | 2026/01/15 14:58:05 upstream timed out (110: Connection timed out)  # 启动中可能看到
nginx-1          | 2026/01/15 14:58:10 [info] 34256#34256: *1 upstream responded with 200  # 成功
```

---

## 预防措施

### 1. 使用固定的密码
在 `.env` 文件中设置强密码，并在部署文档中记录：
```bash
# 生成强密码
openssl rand -base64 32

# 在 .env 中设置
DB_PASSWORD=your_strong_password_here
```

### 2. 记录密码管理
创建一个密码管理文件（不要提交到 Git）：
```bash
# 创建密码管理文件
touch docker/.env.local
echo "DB_PASSWORD=your_strong_password_here" > docker/.env.local

# 确保 .env.local 在 .gitignore 中
echo ".env.local" >> .gitignore
```

### 3. 定期备份
定期备份 PostgreSQL 数据 volume：
```bash
# 备份数据库
docker run --rm \
  -v docker_db-data:/var/lib/postgresql/data \
  -v $(pwd)/backup:/backup \
  postgres:15-alpine \
  tar czf /backup/postgres_backup_$(date +%Y%m%d).tar.gz /var/lib/postgresql/data
```

---

## 常见错误排查

### 错误 1：FATAL: password authentication failed
**原因**：密码不匹配
**解决方案**：
- 方案 1（删除 volume）
- 方案 2（修改 volume 密码）

### 错误 2：connection to server on socket failed
**原因**：PostgreSQL 服务未完全启动
**解决方案**：
- 等待数据库完全启动（检查日志）
- 确认数据库健康检查通过

### 错误 3：Killed (status: 137)
**原因**：容器内存不足被 OOM Killer 杀掉
**解决方案**：
- 增加 Docker 可用内存
- 减少 web 容器的 PM2_INSTANCES 数量
- 检查服务器总内存使用情况

### 错误 4：nginx upstream connection refused
**原因**：API 服务未启动
**解决方案**：
- 检查 API 和 worker 日志
- 确认数据库连接正常
- 检查依赖关系（depends_on）

---

## 技术细节

### Docker Compose Volume 路径
```yaml
volumes:
  db-data:
    driver: local
    name: docker_db-data  # 实际 volume 名称
```

### PostgreSQL 数据目录结构
```
/var/lib/postgresql/data/
├── base/              # PostgreSQL 基础数据
├── global/            # 全局数据
├── pg_wal/            # WAL 日志
├── pg_hba.conf        # 认证配置（包含密码哈希）
├── pg_ident.conf       # 连接配置
└── postmaster.pid      # PID 文件
```

### 密码存储位置
PostgreSQL 密码存储在数据目录中，而不是容器文件系统中：
- **首次启动**：使用环境变量 `POSTGRES_PASSWORD` 设置密码
- **后续启动**：使用数据目录中已保存的密码（即使环境变量不同）

---

## 相关文档

- Docker Compose 文档：https://docs.docker.com/compose/
- PostgreSQL 密码管理：https://www.postgresql.org/docs/current/runtime-config-client-connections-manuals.html
- Dify 部署文档：https://docs.dify.ai/

---

## 更新日志

- **2026-01-15**：创建初始文档，记录 PostgreSQL 密码认证失败的解决方案
- **版本**：v1.0
- **适用场景**：dify-plus docker 部署环境

---

## 快速参考

```bash
# 快速检查命令
docker compose -f docker-compose.dify-plus.yaml ps          # 查看容器状态
docker compose -f docker-compose.dify-plus.yaml logs db --tail 50    # 查看数据库日志
docker volume ls                                          # 列出所有 volumes
docker volume inspect docker_db-data                          # 查看 volume 详情

# 快速重置命令（删除所有数据）
docker compose -f docker-compose.dify-plus.yaml down
docker volume rm docker_db-data
docker compose -f docker-compose.dify-plus.yaml up -d
```

---

**注意**：选择方案 1 会删除所有数据，请在执行前确认是否可以接受数据丢失！
