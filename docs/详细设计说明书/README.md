# 飞机发动机QEC拆装智能化系统详细设计说明书

## 0. 文档元信息
- 文档版本：v1.0
- 作者/评审人：系统架构师团队
- 创建/更新日期：2025-09-01
- 关联需求/任务：飞机发动机QEC拆装智能化系统二期建设
- 适用范围：整个系统四大功能模块

## 1. 引言

### 1.1 背景与目标

本文档旨在详细描述飞机发动机QEC拆装智能化系统二期建设的完整详细设计方案，为开发人员、测试人员和运维人员提供技术实现指导。

系统通过引入人工智能技术，提高维修效率、优化资源配置，实现维修工作智能化管理的升级。系统主要包括维修知识库管理、维修规划及资源智能化、生产看板以及发动机检测辅助四大功能模块，旨在构建完善的维修知识体系，实现维修计划的智能生成与调整，优化资源配置，并提供多维度的生产状态可视化展示。

### 1.2 范围与不在范围

**在范围内：**
- 维修知识库管理：知识构建、检索、问答等全功能
- 维修规划及资源智能化：计划生成、资源配置、冲突解决
- 生产看板：多维度可视化展示、实时监控
- 发动机检测辅助：智能检测、报告生成、预警管理
- 系统集成：与SAP、文档管理等外部系统的接口
- 基础设施：数据存储、安全、监控等支撑服务

**不在范围内：**
- SAP系统内部功能实现
- 物流运输环节的业务流程
- 硬件设备的具体选型和采购
- 第三方系统的内部实现

### 1.3 术语与缩写

| 术语/缩略语 | 定义 |
| ---------- | --- |
| QEC | Quick Engine Change，快速发动机更换装置 |
| KB | Knowledge Base，知识库 |
| RAG | Retrieval-Augmented Generation，检索增强生成 |
| NLP | Natural Language Processing，自然语言处理 |
| API | Application Programming Interface，应用程序接口 |
| ETL | Extract Transform Load，数据提取转换加载 |
| VDB | Vector Database，向量数据库 |
| LLM | Large Language Model，大语言模型 |
| MMR | Maximal Marginal Relevance，最大边际相关性 |

### 1.4 参考资料（SRS/PRD/ADR/接口标准/规约）

1. 《飞机发动机QEC拆装智能化系统需求规格说明书》
2. 《飞机发动机QEC拆装智能化系统概要设计说明书》
3. 《飞机发动机QEC拆装业务流程文档》
4. 《机务维修AI辅助系统功能结构规划》
5. 《航空维修行业相关标准和规范》
6. RESTful API设计规范
7. 企业信息安全规范

## 2. 总体设计

### 2.1 架构视图（C4）

```mermaid
C4Context
title 维修知识库管理模块上下文图
Person(maintainer, "维修人员", "执行维修任务，查询维修知识")
Person(controller, "维修控制人员", "配置知识库，管理维修文档")
Person(tech_mgr, "技术管理人员", "管理技术资料，审核知识内容")

System_Boundary(kb_system, "维修知识库管理模块") {
    System(kb_mgmt, "知识库管理服务", "管理维修手册、历史记录、经验库")
    System(qa_service, "智能问答服务", "提供自然语言问答能力")
    System(retrieval, "检索服务", "精准检索与定位维修手册")
}

System_Ext(sap, "SAP系统", "提供维修指令和基础数据")
System_Ext(doc_sys, "文档管理系统", "存储维修手册和技术文档")
System_Ext(ext_kb, "外部知识库", "第三方技术知识源")

Rel(maintainer, qa_service, "提问维修问题")
Rel(maintainer, retrieval, "查找手册章节")
Rel(controller, kb_mgmt, "管理知识库")
Rel(tech_mgr, kb_mgmt, "审核知识内容")

Rel(kb_mgmt, doc_sys, "同步文档", "API")
Rel(kb_mgmt, sap, "获取维修数据", "API")
Rel(retrieval, ext_kb, "检索外部知识", "API")
```

### 2.2 运行环境与技术栈

- **语言/框架**：Python/Flask，前端Next.js
- **运行环境**：Docker容器/Linux/16GB内存/8核CPU/高速网络
- **外部依赖**：关系型数据库/向量数据库/消息队列/对象存储/搜索引擎/AI推理服务

### 2.3 设计约束与关键决策（ADR）

- **决策ADR-001**：采用检索增强生成(RAG)架构/原因：结合向量检索与生成模型优势/备选：纯检索或纯生成/影响：提升答案质量与可追溯性/日期：2025-09-01
- **决策ADR-002**：使用向量数据库存储知识嵌入/原因：支持语义检索与快速相似度计算/备选：传统全文检索/影响：检索精度显著提升/日期：2025-09-01
- **决策ADR-003**：采用分段化知识管理/原因：便于精确引用与上下文控制/备选：整篇文档检索/影响：提升引用精确性/日期：2025-09-01

## 3. 详细设计

### 3.1 模块清单

| 模块 | 职责 | 主要接口 | 数据实体 | 关键流程 |
|---|---|---|---|---|
| 维修知识库管理 | 知识构建、检索、问答服务 | 知识库CRUD、问答API、检索服务 | Dataset、Document、Segment、Message | 知识接入→解析分段→向量索引→智能问答 |
| 维修规划及资源智能化 | 计划生成、资源配置、冲突解决 | 计划API、资源管理API、调度API | Plan、Resource、Task、Schedule | 需求分析→计划生成→资源分配→冲突解决 |
| 生产看板 | 多维度可视化展示、实时监控 | 看板API、数据聚合API、通知API | Dashboard、Metric、Alert、Report | 数据采集→实时计算→可视化展示→告警通知 |
| 发动机检测辅助 | 智能检测、数据分析、预警管理 | 检测API、分析API、预警API | Detection、Analysis、Warning、Report | 检测规划→数据采集→智能分析→预警报告 |

### 3.2 知识库构建与维护模块

#### 3.2.1 职责与边界

**核心职责**：
- 实现维修手册、历史维修记录、维修经验与结构化工程文件等多来源知识的接入、分段、标注、检索参数配置与全生命周期维护
- 提供知识库的创建、更新、删除和版本管理功能
- 支持多种文档格式的解析和标准化处理
- 建立知识分段的向量索引和元数据索引

**边界定义**：
- 处理范围：TXT/MD/PDF/HTML/XLSX/DOCX/CSV等格式文档
- 不处理：音频/视频文件的直接解析（可接受转录文本）
- 支持文档大小：单文件≤100MB，批量上传≤1GB
- 支持知识库规模：单库≤10万文档，≤1000万分段

#### 3.2.2 接口定义（REST API）

| 接口 | 方法 | 路径 | 鉴权 | 入参 | 出参 | 错误码 |
|---|---|---|---|---|---|---|
| 创建知识库 | POST | /v1/datasets | Bearer Token | name, permission, description | dataset_id, status | 400, 401, 409 |
| 知识库列表 | GET | /v1/datasets | Bearer Token | page, limit, name_filter | datasets[], total, page_info | 400, 401 |
| 删除知识库 | DELETE | /v1/datasets/{dataset_id} | Bearer Token | dataset_id | success | 400, 401, 404 |
| 上传文档 | POST | /v1/datasets/{dataset_id}/document/create_by_file | Bearer Token | multipart file, metadata | document_id, status | 400, 401, 413, 415 |
| 文档列表 | GET | /v1/datasets/{dataset_id}/documents | Bearer Token | page, limit, status_filter | documents[], total | 400, 401, 404 |
| 更新文档 | POST | /v1/datasets/{dataset_id}/documents/{document_id}/update_by_file | Bearer Token | multipart file | document_id, status | 400, 401, 404 |
| 删除文档 | DELETE | /v1/datasets/{dataset_id}/documents/{document_id} | Bearer Token | document_id | success | 400, 401, 404 |
| 索引状态 | GET | /v1/datasets/{dataset_id}/documents/{batch}/indexing-status | Bearer Token | batch_id | indexing_status, progress, error | 400, 401, 404 |

**示例请求**：
```http
POST /v1/datasets HTTP/1.1
Content-Type: application/json
Authorization: Bearer eyJ0eXAiOiJKV1Q...

{
  "name": "维修手册知识库",
  "permission": "only_me",
  "description": "X100发动机维修手册集合"
}
```

**示例响应**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "kb_abc123",
    "name": "维修手册知识库",
    "permission": "only_me",
    "document_count": 0,
    "created_at": "2024-12-19T10:30:00Z"
  }
}
```

#### 3.2.3 数据结构与存储

**逻辑模型与实体**：

```sql
-- 知识库主表
CREATE TABLE datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    permission VARCHAR(50) NOT NULL CHECK (permission IN ('only_me', 'all', 'partial')),
    description TEXT,
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, created_by)
);

-- 文档表
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    name VARCHAR(500) NOT NULL,
    file_id VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'uploaded' 
        CHECK (status IN ('uploaded', 'parsing', 'indexing', 'enabled', 'disabled', 'archived')),
    word_count INTEGER DEFAULT 0,
    parsing_completed_at TIMESTAMP WITH TIME ZONE,
    indexing_completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 文档分段表
CREATE TABLE segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    content TEXT NOT NULL,
    word_count INTEGER NOT NULL,
    tokens INTEGER NOT NULL,
    keywords TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引设计
CREATE INDEX idx_documents_dataset_id ON documents(dataset_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_segments_document_id ON segments(document_id);
CREATE INDEX idx_segments_keywords ON segments USING GIN(keywords);
```

**缓存键设计与过期策略**：
- 知识库配置：`kb:config:{dataset_id}` (TTL: 1小时)
- 文档状态：`doc:status:{document_id}` (TTL: 30分钟)
- 检索结果：`search:{query_hash}:{dataset_id}` (TTL: 15分钟)

#### 3.2.4 核心流程

```mermaid
sequenceDiagram
    participant Client as 客户端
    participant API as API网关
    participant Service as 知识库服务
    participant Parser as 文档解析器
    participant VDB as 向量数据库
    participant Queue as 任务队列

    Client->>API: 上传文档
    API->>Service: 创建文档记录
    Service->>Queue: 投递解析任务
    Service-->>Client: 返回文档ID
    
    Queue->>Parser: 处理解析任务
    Parser->>Parser: 提取文本内容
    Parser->>Parser: 分段处理
    Parser->>Service: 更新解析状态
    
    Service->>Queue: 投递索引任务
    Queue->>VDB: 生成向量嵌入
    VDB->>VDB: 存储向量索引
    VDB->>Service: 更新索引状态
    Service-->>Client: 通知索引完成
```

#### 3.2.5 状态机

```mermaid
stateDiagram-v2
    [*] --> UPLOADED: 文档上传
    UPLOADED --> PARSING: 开始解析
    PARSING --> INDEXING: 解析完成
    PARSING --> FAILED: 解析失败
    INDEXING --> ENABLED: 索引完成
    INDEXING --> FAILED: 索引失败
    ENABLED --> DISABLED: 手动禁用
    ENABLED --> ARCHIVED: 归档
    DISABLED --> ENABLED: 重新启用
    FAILED --> PARSING: 重试解析
    ARCHIVED --> [*]: 删除
```

#### 3.2.6 错误处理与重试

**错误分类、错误码、幂等策略**：

| 错误类型 | 错误码 | 描述 | 重试策略 | 幂等处理 |
|---|---|---|---|---|
| 文件格式错误 | 415001 | 不支持的文件格式 | 不重试 | 返回相同错误 |
| 文件过大 | 413001 | 文件大小超限 | 不重试 | 返回相同错误 |
| 解析失败 | 500001 | 文档内容解析失败 | 指数退避，最多3次 | 基于文档ID幂等 |
| 索引失败 | 500002 | 向量索引构建失败 | 指数退避，最多5次 | 基于分段ID幂等 |
| 知识库名称冲突 | 409001 | 知识库名称已存在 | 不重试 | 返回现有知识库ID |

**补偿事务**：
- 文档上传失败：清理已上传的文件和数据库记录
- 索引构建失败：保留文档记录，标记为失败状态，支持重新索引

#### 3.2.7 配置项

| 键 | 默认值 | 范围/限制 | 作用 | 生效方式 |
|---|---|---|---|---|
| MAX_FILE_SIZE | 100MB | 1MB~500MB | 单文件最大大小 | 重启生效 |
| MAX_BATCH_SIZE | 1GB | 100MB~5GB | 批量上传最大大小 | 重启生效 |
| PARSING_TIMEOUT | 300s | 60s~1800s | 文档解析超时时间 | 实时生效 |
| INDEXING_BATCH_SIZE | 100 | 10~1000 | 批量索引分段数量 | 实时生效 |
| RETRY_MAX_ATTEMPTS | 3 | 1~10 | 最大重试次数 | 实时生效 |
| CACHE_TTL | 3600s | 300s~86400s | 缓存过期时间 | 实时生效 |

#### 3.2.8 性能与容量规划

**QPS/吞吐/延迟目标**：
- 文档上传：50 QPS，响应时间 ≤ 2秒
- 文档列表查询：200 QPS，响应时间 ≤ 500ms
- 文档解析：单文档10MB ≤ 30秒
- 向量索引：1000分段/分钟

**并发处理**：
- 支持100个并发上传任务
- 解析队列：10个worker并行处理
- 索引队列：5个worker并行处理

**扩展策略**：
- 水平扩展：API服务无状态，支持负载均衡
- 存储扩展：数据库分片，向量库集群
- 计算扩展：解析和索引服务独立扩容

#### 3.2.9 安全与合规

**鉴权鉴权**：
- JWT Token身份验证
- 基于角色的权限控制（RBAC）
- 知识库级别的访问控制

**加密与审计**：
- 文档存储AES-256加密
- 敏感元数据脱敏显示
- 操作日志审计记录：创建、更新、删除、访问

**权限最小化**：
- 用户仅能访问授权的知识库
- API接口按功能最小权限设计
- 数据库连接使用专用账户

#### 3.2.10 可观测性

**日志等级与结构**：
```json
{
  "timestamp": "2024-12-19T10:30:00Z",
  "level": "INFO",
  "service": "knowledge-service",
  "module": "document-upload",
  "trace_id": "abc123",
  "user_id": "user456",
  "dataset_id": "kb_789",
  "message": "Document uploaded successfully",
  "duration_ms": 1200,
  "file_size": 2048576
}
```

**指标（Prometheus格式）**：
- `knowledge_document_upload_total{status="success|failed"}` - 文档上传计数
- `knowledge_document_parsing_duration_seconds` - 解析耗时分布
- `knowledge_indexing_queue_size` - 索引队列长度
- `knowledge_storage_usage_bytes{dataset_id}` - 存储空间使用

**告警阈值**：
- 文档上传失败率 > 5%
- 解析队列积压 > 100个任务
- 索引构建失败率 > 2%
- 存储使用率 > 80%

### 3.3 智能问答服务模块

#### 3.3.1 职责与边界

**核心职责**：
- 实现面向维修场景的自然语言问题解析与答案生成
- 结合内部维修知识库进行检索增强生成(RAG)
- 提供可解释的答案与引用追溯功能
- 支持多轮对话和上下文理解

**边界定义**：
- 处理自然语言问题，长度≤2000字符
- 支持文本、图片、文档等多模态输入
- 答案生成时间：简单问题≤3秒，复杂问题≤10秒
- 支持的语言：中文、英文

#### 3.3.2 接口定义（REST API）

| 接口 | 方法 | 路径 | 鉴权 | 入参 | 出参 | 错误码 |
|---|---|---|---|---|---|---|
| 发送问题 | POST | /v1/chat-messages | Bearer Token | query, inputs, files, response_mode | answer, conversation_id, message_id | 400, 401, 429 |
| 停止响应 | POST | /v1/chat-messages/{task_id}/stop | Bearer Token | task_id | success | 400, 401, 404 |
| 上传文件 | POST | /v1/files/upload | Bearer Token | multipart file | file_id, name, size | 400, 401, 413, 415 |
| 历史消息 | GET | /v1/messages | Bearer Token | conversation_id, limit, before_id | messages[], has_more | 400, 401, 404 |
| 会话列表 | GET | /v1/conversations | Bearer Token | limit, before_id | conversations[], has_more | 400, 401 |
| 消息反馈 | POST | /v1/messages/{message_id}/feedbacks | Bearer Token | rating, content | success | 400, 401, 404 |

**示例请求**：
```http
POST /v1/chat-messages HTTP/1.1
Content-Type: application/json
Authorization: Bearer eyJ0eXAiOiJKV1Q...

{
  "query": "X100发动机启动失败怎么处理？",
  "inputs": {
    "device_model": "X100",
    "manual_version": "v2.0"
  },
  "response_mode": "streaming",
  "conversation_id": "conv_abc123"
}
```

**示例响应**：
```json
{
  "event": "message",
  "conversation_id": "conv_abc123",
  "message_id": "msg_def456",
  "answer": "根据X100发动机维修手册，启动失败的排查步骤如下：\n\n1. 检查燃油供应系统...",
  "retriever_resources": [
    {
      "segment_id": "seg_789",
      "document_name": "X100维修手册v2.0",
      "content": "启动系统故障排除...",
      "score": 0.95,
      "position": {"page": 156, "section": "3.2.4"}
    }
  ],
  "metadata": {
    "usage": {"tokens": 1250, "cost": 0.025}
  }
}
```

#### 3.3.3 数据结构与存储

**逻辑模型与实体**：

```sql
-- 会话表
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name VARCHAR(255),
    inputs JSONB,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'archived')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 消息表
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    parent_message_id UUID REFERENCES messages(id),
    query TEXT,
    answer TEXT,
    error_message TEXT,
    usage JSONB,
    retriever_resources JSONB,
    agent_thoughts JSONB,
    message_tokens INTEGER DEFAULT 0,
    answer_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 消息反馈表
CREATE TABLE message_feedbacks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    rating VARCHAR(20) CHECK (rating IN ('like', 'dislike')),
    content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引设计
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_message_feedbacks_message_id ON message_feedbacks(message_id);
```

**缓存键设计与过期策略**：
- 会话上下文：`conv:context:{conversation_id}` (TTL: 2小时)
- 用户偏好：`user:pref:{user_id}` (TTL: 24小时)
- 问答缓存：`qa:cache:{query_hash}:{inputs_hash}` (TTL: 1小时)

#### 3.3.4 核心流程

```mermaid
sequenceDiagram
    participant Client as 客户端
    participant API as 问答API
    participant QA as 问答服务
    participant RAG as 检索服务
    participant LLM as 语言模型
    participant KB as 知识库

    Client->>API: 发送问题
    API->>QA: 创建消息记录
    QA->>QA: 解析问题意图
    QA->>RAG: 检索相关知识
    RAG->>KB: 向量检索
    KB-->>RAG: 返回候选分段
    RAG->>RAG: 重排序与筛选
    RAG-->>QA: 返回知识片段
    QA->>LLM: 生成答案
    LLM-->>QA: 返回答案文本
    QA->>QA: 构建引用信息
    QA-->>Client: 流式返回答案
```

#### 3.3.5 状态机

```mermaid
stateDiagram-v2
    [*] --> RECEIVED: 接收问题
    RECEIVED --> PARSING: 解析意图
    PARSING --> RETRIEVING: 检索知识
    RETRIEVING --> GENERATING: 生成答案
    GENERATING --> COMPLETED: 完成回答
    GENERATING --> FAILED: 生成失败
    PARSING --> FAILED: 解析失败
    RETRIEVING --> FAILED: 检索失败
    FAILED --> [*]: 返回错误
    COMPLETED --> [*]: 返回答案
```

#### 3.3.6 错误处理与重试

**错误分类、错误码、幂等策略**：

| 错误类型 | 错误码 | 描述 | 重试策略 | 幂等处理 |
|---|---|---|---|---|
| 问题格式错误 | 400001 | 问题内容为空或格式错误 | 不重试 | 返回相同错误 |
| 模型服务超时 | 504001 | 语言模型响应超时 | 指数退避，最多2次 | 基于消息ID幂等 |
| 检索服务异常 | 500003 | 知识库检索服务异常 | 线性退避，最多3次 | 基于查询哈希幂等 |
| 配额不足 | 429001 | 用户请求配额不足 | 不重试 | 返回配额重置时间 |
| 会话不存在 | 404001 | 指定会话ID不存在 | 不重试 | 创建新会话 |

**补偿事务**：
- 生成失败：保留用户问题，标记答案状态为失败
- 检索异常：降级为基础回答模式，不提供引用

#### 3.3.7 配置项

| 键 | 默认值 | 范围/限制 | 作用 | 生效方式 |
|---|---|---|---|---|
| MAX_QUERY_LENGTH | 2000 | 100~5000 | 问题最大长度 | 实时生效 |
| RETRIEVAL_TOP_K | 8 | 1~50 | 检索返回片段数 | 实时生效 |
| MIN_RELEVANCE_SCORE | 0.3 | 0.1~0.9 | 最低相关度阈值 | 实时生效 |
| GENERATION_TIMEOUT | 30s | 10s~120s | 答案生成超时时间 | 实时生效 |
| MAX_TOKENS | 2048 | 512~4096 | 最大生成token数 | 实时生效 |
| CONVERSATION_TTL | 7200s | 3600s~86400s | 会话上下文保持时间 | 实时生效 |

#### 3.3.8 性能与容量规划

**QPS/吞吐/延迟目标**：
- 问答请求：100 QPS，响应时间 ≤ 3秒(简单问题)
- 流式响应：首字节延迟 ≤ 1秒
- 历史消息查询：500 QPS，响应时间 ≤ 200ms
- 并发会话：支持1000个活跃会话

**并发处理**：
- 问答服务：20个worker并行处理
- 检索服务：异步调用，无阻塞
- 生成服务：支持流式处理

**扩展策略**：
- 水平扩展：问答服务无状态设计
- 缓存优化：多级缓存减少重复计算
- 模型优化：支持模型负载均衡

#### 3.3.9 安全与合规

**鉴权鉴权**：
- JWT Token身份验证
- 用户级别的问答配额控制
- 敏感问题内容过滤

**加密与审计**：
- 会话内容传输加密
- 问答历史审计日志
- 用户隐私数据脱敏

**权限最小化**：
- 用户仅能访问自己的会话
- 知识库访问权限继承
- API调用频率限制

#### 3.3.10 可观测性

**日志等级与结构**：
```json
{
  "timestamp": "2024-12-19T10:30:00Z",
  "level": "INFO",
  "service": "qa-service",
  "module": "chat-completion",
  "trace_id": "xyz789",
  "user_id": "user456",
  "conversation_id": "conv_123",
  "message_id": "msg_456",
  "message": "Answer generated successfully",
  "duration_ms": 2800,
  "tokens_used": 1250,
  "relevance_score": 0.87
}
```

**指标（Prometheus格式）**：
- `qa_messages_total{status="success|failed|timeout"}` - 问答消息计数
- `qa_response_duration_seconds` - 响应时间分布
- `qa_tokens_usage_total` - Token使用量
- `qa_relevance_score_histogram` - 相关度分数分布

**告警阈值**：
- 问答失败率 > 3%
- 平均响应时间 > 5秒
- Token使用率 > 90%
- 相关度分数 < 0.5的比例 > 20%

### 3.4 检索与定位服务模块

#### 3.4.1 职责与边界

**核心职责**：
- 实现"按手册定位"的精准检索与跳转功能
- 提供关键词/语义/混合检索与父子分段上下文合并
- 支持多路召回、重排序与去重优化
- 提供检索质量监控与策略调优能力

**边界定义**：
- 支持向量检索、全文检索、混合检索三种模式
- 单次检索返回分段数：1~50个可配置
- 检索响应时间：≤1秒
- 支持外部知识库联合检索

#### 3.4.2 接口定义（REST API）

| 接口 | 方法 | 路径 | 鉴权 | 入参 | 出参 | 错误码 |
|---|---|---|---|---|---|---|
| 知识检索 | POST | /v1/retrieval/search | Bearer Token | query, dataset_ids, mode, top_k, score_threshold | segments[], total_found, search_id | 400, 401, 404 |
| 手册定位 | POST | /v1/retrieval/locate | Bearer Token | query, device_model, manual_version, section_hint | location_info, context_preview, reference_link | 400, 401, 404 |
| 检索测试 | POST | /v1/retrieval/hit-testing | Bearer Token | query, dataset_id, retrieval_model | segments[], scores[], debug_info | 400, 401, 404 |
| 策略配置 | POST | /v1/retrieval/strategy | Bearer Token | dataset_id, mode, parameters | strategy_id, status | 400, 401, 404 |
| 外部检索 | POST | /v1/retrieval/external | Bearer Token | query, external_kb_id, max_segments, min_relevance | segments[], source_info | 400, 401, 408 |

**示例请求**：
```http
POST /v1/retrieval/locate HTTP/1.1
Content-Type: application/json
Authorization: Bearer eyJ0eXAiOiJKV1Q...

{
  "query": "如何复位燃油控制单元？",
  "device_model": "X100",
  "manual_version": "v2.0",
  "section_hint": "故障排除"
}
```

**示例响应**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "location_info": {
      "manual_name": "X100维修手册v2.0",
      "chapter": "第3章 故障排除",
      "section": "3.2.4",
      "page": 156,
      "relevance_score": 0.95
    },
    "context_preview": "燃油控制单元复位程序：\n1. 关闭主电源开关\n2. 等待30秒...",
    "reference_link": "/datasets/kb_123/documents/doc_456/segments/seg_789"
  }
}
```

#### 3.4.3 数据结构与存储

**逻辑模型与实体**：

```sql
-- 检索记录表
CREATE TABLE retrieval_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID NOT NULL,
    query TEXT NOT NULL,
    mode VARCHAR(50) NOT NULL CHECK (mode IN ('vector', 'keyword', 'hybrid')),
    parameters JSONB,
    results_count INTEGER DEFAULT 0,
    duration_ms INTEGER,
    user_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 检索策略表
CREATE TABLE retrieval_strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    mode VARCHAR(50) NOT NULL,
    parameters JSONB NOT NULL,
    is_active BOOLEAN DEFAULT false,
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dataset_id, name)
);

-- 测试用例表
CREATE TABLE test_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID NOT NULL,
    query TEXT NOT NULL,
    expected_segments UUID[],
    expected_score_threshold FLOAT DEFAULT 0.5,
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引设计
CREATE INDEX idx_retrieval_records_dataset_id ON retrieval_records(dataset_id);
CREATE INDEX idx_retrieval_records_created_at ON retrieval_records(created_at);
CREATE INDEX idx_retrieval_strategies_dataset_id ON retrieval_strategies(dataset_id);
CREATE INDEX idx_test_cases_dataset_id ON test_cases(dataset_id);
```

**缓存键设计与过期策略**：
- 检索结果：`retrieval:cache:{query_hash}:{params_hash}` (TTL: 15分钟)
- 策略配置：`retrieval:strategy:{dataset_id}` (TTL: 1小时)
- 向量嵌入：`embedding:cache:{text_hash}` (TTL: 24小时)

#### 3.4.4 核心流程

```mermaid
sequenceDiagram
    participant Client as 客户端
    participant API as 检索API
    participant Search as 检索服务
    participant VDB as 向量数据库
    participant FTS as 全文搜索
    participant Rerank as 重排服务

    Client->>API: 发起检索请求
    API->>Search: 解析检索参数
    
    par 向量检索
        Search->>VDB: 语义检索
        VDB-->>Search: 候选分段A
    and 关键词检索
        Search->>FTS: 全文检索
        FTS-->>Search: 候选分段B
    end
    
    Search->>Search: 合并候选结果
    Search->>Rerank: 重排序与去重
    Rerank-->>Search: 最终排序结果
    Search->>Search: 上下文合并
    Search-->>Client: 返回检索结果
```

#### 3.4.5 状态机

```mermaid
stateDiagram-v2
    [*] --> RECEIVED: 接收检索请求
    RECEIVED --> PARSING: 解析查询参数
    PARSING --> RETRIEVING: 执行多路检索
    RETRIEVING --> RERANKING: 重排序处理
    RERANKING --> MERGING: 上下文合并
    MERGING --> COMPLETED: 返回结果
    PARSING --> FAILED: 参数错误
    RETRIEVING --> FAILED: 检索失败
    RERANKING --> FAILED: 重排失败
    FAILED --> [*]: 返回错误
    COMPLETED --> [*]: 完成
```

#### 3.4.6 错误处理与重试

**错误分类、错误码、幂等策略**：

| 错误类型 | 错误码 | 描述 | 重试策略 | 幂等处理 |
|---|---|---|---|---|
| 查询参数错误 | 400002 | 检索参数格式错误 | 不重试 | 返回相同错误 |
| 向量库连接失败 | 500004 | 向量数据库不可用 | 指数退避，最多3次 | 基于查询哈希幂等 |
| 检索超时 | 504002 | 检索操作超时 | 线性退避，最多2次 | 降级策略 |
| 知识库不存在 | 404002 | 指定知识库不存在 | 不重试 | 返回空结果 |
| 外部KB超时 | 408001 | 外部知识库响应超时 | 降级为内部检索 | 记录降级日志 |

**补偿事务**：
- 检索失败：降级为基础关键词检索
- 重排失败：返回原始检索结果
- 外部KB失败：仅使用内部知识库

#### 3.4.7 配置项

| 键 | 默认值 | 范围/限制 | 作用 | 生效方式 |
|---|---|---|---|---|
| DEFAULT_TOP_K | 10 | 1~50 | 默认返回分段数 | 实时生效 |
| MIN_SCORE_THRESHOLD | 0.3 | 0.0~1.0 | 最低相关度阈值 | 实时生效 |
| SEARCH_TIMEOUT | 5s | 1s~30s | 检索超时时间 | 实时生效 |
| MAX_CONTEXT_MERGE | 3 | 1~10 | 最大上下文合并数 | 实时生效 |
| CACHE_ENABLED | true | true/false | 是否启用结果缓存 | 实时生效 |
| EXTERNAL_KB_TIMEOUT | 3s | 1s~10s | 外部KB超时时间 | 实时生效 |

#### 3.4.8 性能与容量规划

**QPS/吞吐/延迟目标**：
- 检索请求：300 QPS，响应时间 ≤ 1秒
- 手册定位：200 QPS，响应时间 ≤ 800ms
- 检索测试：50 QPS，响应时间 ≤ 2秒
- 批量检索：支持100个并发请求

**并发处理**：
- 检索服务：30个worker并行处理
- 向量检索：异步并发调用
- 重排服务：CPU密集型，独立扩容

**扩展策略**：
- 水平扩展：检索服务无状态，支持负载均衡
- 缓存优化：多级缓存(内存+Redis)减少延迟
- 向量库优化：分片与副本提高可用性

#### 3.4.9 安全与合规

**鉴权鉴权**：
- JWT Token身份验证
- 知识库级别的检索权限控制
- API访问频率限制

**加密与审计**：
- 检索历史审计记录
- 敏感查询内容脱敏
- 结果访问权限验证

**权限最小化**：
- 用户仅能检索授权知识库
- 检索结果按权限过滤
- 外部KB访问权限控制

#### 3.4.10 可观测性

**日志等级与结构**：
```json
{
  "timestamp": "2024-12-19T10:30:00Z",
  "level": "INFO",
  "service": "retrieval-service",
  "module": "vector-search",
  "trace_id": "ret123",
  "user_id": "user456",
  "dataset_id": "kb_789",
  "query_hash": "abc123",
  "message": "Retrieval completed successfully",
  "duration_ms": 800,
  "results_count": 8,
  "top_score": 0.89
}
```

**指标（Prometheus格式）**：
- `retrieval_requests_total{mode="vector|keyword|hybrid", status="success|failed"}` - 检索请求计数
- `retrieval_duration_seconds{mode}` - 检索延迟分布
- `retrieval_results_count{dataset_id}` - 返回结果数分布
- `retrieval_cache_hit_ratio` - 缓存命中率

**告警阈值**：
- 检索失败率 > 2%
- 平均检索延迟 > 1.5秒
- 缓存命中率 < 60%
- 向量库连接失败率 > 1%

### 3.4.1 元数据管理子模块

#### 3.4.1.1 职责与边界

**核心职责**：
- 管理知识库全局与文档级元数据字段定义
- 支持按来源/型号/版本/时间/标签等维度筛选
- 提供可追溯引用的元数据标注功能
- 实现元数据的批量编辑和版本管理

**边界定义**：
- 支持string/number/time三种字段类型
- 元数据字段数量：单知识库≤50个
- 批量标注：单次≤1000个文档
- 字段名命名规范：小写字母/数字/下划线

#### 3.4.1.2 接口定义（REST API）

| 接口 | 方法 | 路径 | 鉴权 | 入参 | 出参 | 错误码 |
|---|---|---|---|---|---|---|
| 新增元数据字段 | POST | /v1/datasets/{dataset_id}/metadata | Bearer Token | name, type, is_required | field_id, status | 400, 401, 409 |
| 更新元数据字段 | PATCH | /v1/datasets/{dataset_id}/metadata/{field_id} | Bearer Token | name, type, is_required | field_id, status | 400, 401, 404 |
| 删除元数据字段 | DELETE | /v1/datasets/{dataset_id}/metadata/{field_id} | Bearer Token | field_id | success | 400, 401, 404, 409 |
| 元数据字段列表 | GET | /v1/datasets/{dataset_id}/metadata | Bearer Token | - | fields[], total | 400, 401, 404 |
| 批量标注文档 | POST | /v1/datasets/{dataset_id}/documents/metadata | Bearer Token | document_ids[], field_values | updated_count | 400, 401, 413 |

**示例请求**：
```http
POST /v1/datasets/{dataset_id}/metadata HTTP/1.1
Content-Type: application/json
Authorization: Bearer eyJ0eXAiOiJKV1Q...

{
  "name": "device_model",
  "type": "string",
  "is_required": true,
  "description": "设备型号信息"
}
```

#### 3.4.1.3 数据结构与存储

```sql
-- 元数据字段定义表
CREATE TABLE metadata_fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('string', 'number', 'time')),
    is_required BOOLEAN DEFAULT false,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dataset_id, name)
);

-- 文档元数据值表
CREATE TABLE document_metadata_values (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    field_id UUID NOT NULL REFERENCES metadata_fields(id) ON DELETE CASCADE,
    value TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, field_id)
);

-- 索引设计
CREATE INDEX idx_metadata_fields_dataset ON metadata_fields(dataset_id, name);
CREATE INDEX idx_doc_metadata_field_value ON document_metadata_values(field_id, value);
CREATE INDEX idx_doc_metadata_document ON document_metadata_values(document_id);
```

#### 3.4.1.4 核心流程

```mermaid
sequenceDiagram
    participant Admin as 管理员
    participant API as 元数据API
    participant MetaService as 元数据服务
    participant DB as 数据库
    participant Cache as 缓存

    Admin->>API: 定义元数据字段
    API->>MetaService: 校验字段规范
    MetaService->>DB: 创建字段定义
    MetaService->>Cache: 更新字段缓存
    MetaService-->>Admin: 返回字段ID
    
    Admin->>API: 批量标注文档
    API->>MetaService: 验证字段值
    MetaService->>DB: 批量更新元数据
    MetaService->>Cache: 更新文档索引
    MetaService-->>Admin: 返回更新结果
```

### 3.4.2 外部知识库接入子模块

#### 3.4.2.1 职责与边界

**核心职责**：
- 通过标准化API接入外部知识库
- 实现统一的检索结果格式转换
- 提供外部知识与内部知识的合并重排
- 监控外部知识库的可用性和性能

**边界定义**：
- 支持HTTP/HTTPS协议的外部API
- 单次检索返回：≤50个分段
- 超时控制：连接超时≤3秒，读取超时≤10秒
- 支持基本认证和Token认证

#### 3.4.2.2 接口定义（REST API）

| 接口 | 方法 | 路径 | 鉴权 | 入参 | 出参 | 错误码 |
|---|---|---|---|---|---|---|
| 配置外部知识库 | POST | /v1/external-kb/config | Bearer Token | endpoint, credential, kb_id | config_id, status | 400, 401, 422 |
| 外部检索 | POST | /v1/external-kb/search | Bearer Token | query, kb_id, max_segments | segments[], source_info | 400, 401, 408, 422 |
| 测试连接 | POST | /v1/external-kb/test | Bearer Token | config_id | connectivity, response_time | 400, 401, 408 |
| 外部库列表 | GET | /v1/external-kb/configs | Bearer Token | - | configs[], total | 400, 401 |

#### 3.4.2.3 数据结构与存储

```sql
-- 外部知识库配置表
CREATE TABLE external_kb_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    endpoint VARCHAR(500) NOT NULL,
    credential_type VARCHAR(50) NOT NULL CHECK (credential_type IN ('basic', 'token', 'none')),
    credential_data JSONB,
    external_kb_id VARCHAR(255),
    timeout_seconds INTEGER DEFAULT 10,
    max_segments INTEGER DEFAULT 20,
    is_active BOOLEAN DEFAULT true,
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 外部检索记录表
CREATE TABLE external_retrieval_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID NOT NULL REFERENCES external_kb_configs(id),
    query TEXT NOT NULL,
    response_time_ms INTEGER,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    segments_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 3.4.3 关键词与数据索引子模块

#### 3.4.3.1 职责与边界

**核心职责**：
- 建立和维护关键词体系（核心词/同义词/禁用词）
- 构建多维数据索引支持精确筛选
- 提供检索策略的参数配置和调优
- 监控索引质量和检索效果

**边界定义**：
- 词表规模：核心词≤10000个，同义词≤50000个
- 索引维度：≤10个元数据维度
- 策略版本：支持≤5个历史版本回滚
- 重建频率：增量更新≤1小时，全量重建≤24小时

#### 3.4.3.2 接口定义（REST API）

| 接口 | 方法 | 路径 | 鉴权 | 入参 | 出参 | 错误码 |
|---|---|---|---|---|---|---|
| 管理词表 | POST | /v1/datasets/{dataset_id}/keywords | Bearer Token | core_terms[], synonyms[], stopwords[] | version_id, status | 400, 401, 413 |
| 配置索引策略 | POST | /v1/datasets/{dataset_id}/index-strategy | Bearer Token | dimensions[], weights, params | strategy_id, status | 400, 401, 422 |
| 重建索引 | POST | /v1/datasets/{dataset_id}/rebuild-index | Bearer Token | strategy_id, mode | task_id, estimated_time | 400, 401, 409 |
| 索引状态查询 | GET | /v1/datasets/{dataset_id}/index-status | Bearer Token | - | status, progress, metrics | 400, 401, 404 |

### 3.4.4 权限与审计子模块

#### 3.4.4.1 职责与边界

**核心职责**：
- 基于角色的知识库访问权限控制
- 关键操作的审计日志记录
- 操作权限的实时验证
- 审计数据的查询和导出

**边界定义**：
- 角色类型：所有者/管理员/编辑/只读
- 权限粒度：知识库级+文档级+分段级
- 审计保留：≥12个月，支持导出
- 访问日志：记录所有API调用和数据访问

#### 3.4.4.2 权限矩阵

| 角色 | 知识库管理 | 文档管理 | 元数据管理 | 索引重建 | 检索测试 | 审计查看 |
|---|---|---|---|---|---|---|
| 所有者 | 全部权限 | 全部权限 | 全部权限 | 允许 | 允许 | 允许 |
| 管理员 | 查看/编辑 | 全部权限 | 全部权限 | 允许 | 允许 | 允许 |
| 编辑 | 查看 | 增删改查 | 标注编辑 | 受限 | 允许 | 受限 |
| 只读 | 查看 | 查看 | 查看 | 否 | 查看 | 否 |

#### 3.4.4.3 审计日志设计

```sql
-- 操作审计日志表
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 访问日志表  
CREATE TABLE access_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    endpoint VARCHAR(200) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER,
    dataset_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 3.4.5 文档与分段维护子模块

#### 3.4.5.1 职责与边界

**核心职责**：
- 文档状态的生命周期管理
- 分段的增删改查和批量操作
- 文档更新时的索引重建
- 分段质量的监控和优化

**边界定义**：
- 文档状态：uploaded → parsing → indexing → enabled/disabled/archived
- 分段操作：支持单个和批量操作
- 更新频率：文档更新触发增量索引
- 质量监控：分段相关度、长度分布等指标

#### 3.4.5.2 状态机设计

```mermaid
stateDiagram-v2
    [*] --> UPLOADED: 文档上传
    UPLOADED --> PARSING: 开始解析
    PARSING --> INDEXING: 解析完成
    PARSING --> PARSE_FAILED: 解析失败
    INDEXING --> ENABLED: 索引完成
    INDEXING --> INDEX_FAILED: 索引失败
    ENABLED --> DISABLED: 手动禁用
    ENABLED --> ARCHIVED: 归档文档
    ENABLED --> UPDATING: 更新文档
    DISABLED --> ENABLED: 重新启用
    UPDATING --> ENABLED: 更新完成
    UPDATING --> UPDATE_FAILED: 更新失败
    PARSE_FAILED --> PARSING: 重试解析
    INDEX_FAILED --> INDEXING: 重试索引
    UPDATE_FAILED --> ENABLED: 回滚状态
    ARCHIVED --> [*]: 删除文档
```

### 3.5 维修规划及资源智能化模块

#### 3.5.1 职责与边界

**核心职责**：
- 智能化生成和调整维修计划
- 优化航材、人员和工具等资源配置  
- 处理工作协同冲突和资源调度
- 提供维修需求分析和计划执行跟踪

**边界定义**：
- 处理维修指令接收和计划生成
- 支持多维度资源配置优化
- 计划执行时间：简单计划≤10秒，复杂计划≤60秒
- 支持1000+并发资源调度请求

**详细设计**：
> 待补充 - 包含计划生成算法、资源优化策略、冲突解决机制等详细设计

### 3.6 生产看板模块

#### 3.6.1 职责与边界

**核心职责**：
- 提供多维度的生产状态可视化展示
- 实时监控维修计划执行情况
- 展示资源使用状态和工位情况
- 提供预警和告警功能

**边界定义**：
- 支持计划看板、进度看板、资源看板、工位看板
- 数据刷新频率：≤5秒
- 支持大屏显示和移动端适配
- 并发查看用户：≤500人

**详细设计**：
> 待补充 - 包含看板组件设计、数据聚合策略、实时通信机制等详细设计

### 3.7 发动机检测辅助模块

#### 3.7.1 职责与边界

**核心职责**：
- 智能化检测任务管理和路径规划
- 实时检测结果处理和分析
- 自动化报告生成和历史数据分析
- 异常预警和风险评估

**边界定义**：
- 支持多种检测设备接入
- 检测数据处理：实时流式处理
- 报告生成时间：≤30秒
- 支持历史数据回溯分析

**详细设计**：
> 待补充 - 包含检测设备集成、数据分析算法、预警规则引擎等详细设计

## 4. 数据设计

### 4.1 逻辑数据模型

整个系统的核心数据实体及其关系如下（当前重点展示维修知识库管理模块，其他模块的数据模型待补充）：

```mermaid
erDiagram
    USER ||--o{ DATASET : creates
    DATASET ||--o{ DOCUMENT : contains
    DOCUMENT ||--o{ SEGMENT : splits_into
    DATASET ||--o{ METADATA_FIELD : defines
    DOCUMENT ||--o{ DOC_METADATA_VALUE : has
    USER ||--o{ CONVERSATION : initiates
    CONVERSATION ||--o{ MESSAGE : contains
    MESSAGE ||--o{ MESSAGE_FEEDBACK : receives
    DATASET ||--o{ RETRIEVAL_RECORD : logs
    DATASET ||--o{ RETRIEVAL_STRATEGY : configures
    DATASET ||--o{ TEST_CASE : validates

    USER {
        uuid id PK
        string username
        string email
        jsonb roles
        timestamp created_at
    }
    
    DATASET {
        uuid id PK
        string name
        string permission
        text description
        uuid created_by FK
        integer document_count
        timestamp created_at
    }
    
    DOCUMENT {
        uuid id PK
        uuid dataset_id FK
        string name
        string file_id
        string status
        integer word_count
        timestamp parsing_completed_at
        timestamp indexing_completed_at
    }
    
    SEGMENT {
        uuid id PK
        uuid document_id FK
        integer position
        text content
        integer word_count
        integer tokens
        text keywords_array
        float vector_array
    }
    
    METADATA_FIELD {
        uuid id PK
        uuid dataset_id FK
        string name
        string type
        boolean is_required
    }
    
    DOC_METADATA_VALUE {
        uuid id PK
        uuid document_id FK
        uuid field_id FK
        string value
    }
    
    CONVERSATION {
        uuid id PK
        uuid user_id FK
        string name
        jsonb inputs
        string status
    }
    
    MESSAGE {
        uuid id PK
        uuid conversation_id FK
        uuid parent_message_id FK
        text query
        text answer
        jsonb usage
        jsonb retriever_resources
    }
```

### 4.2 物理数据模型与迁移策略

**数据库选择**：PostgreSQL 15+ with pgvector extension
- 支持关系型数据存储和向量数据索引
- 提供JSONB字段类型支持元数据灵活存储
- 具备完善的事务ACID保证

**分区策略**：
- `messages`表按创建时间月份分区，提高查询性能
- `retrieval_records`表按数据集ID分区，便于数据管理
- `segments`表考虑按文档数量进行垂直分片

**索引设计**：
```sql
-- 组合索引优化查询
CREATE INDEX idx_segments_document_vector ON segments USING ivfflat(vector);
CREATE INDEX idx_messages_conversation_time ON messages(conversation_id, created_at DESC);
CREATE INDEX idx_documents_dataset_status ON documents(dataset_id, status);

-- 元数据查询优化
CREATE INDEX idx_doc_metadata_value_field ON doc_metadata_value(field_id, value);
CREATE INDEX idx_metadata_field_dataset ON metadata_field(dataset_id, name);
```

**迁移策略**：
- 使用Alembic进行数据库版本管理
- 采用蓝绿部署，零停机迁移
- 大表迁移采用分批处理，避免长时间锁表

### 4.3 数据流设计

**主要数据流向**：

1. **知识库构建数据流**：
   ```
   文档上传 → 文件存储 → 解析队列 → 文本提取 → 分段处理 → 向量嵌入 → 索引存储
   ```

2. **问答交互数据流**：
   ```
   用户问题 → 意图解析 → 知识检索 → 重排序 → 答案生成 → 引用追踪 → 结果返回
   ```

3. **质量监控数据流**：
   ```
   检索日志 → 指标计算 → 质量评估 → 策略调优 → 效果验证 → 配置更新
   ```

## 5. 接口设计汇总

### 5.1 REST API统一规范

**版本控制**：
- URL路径版本：`/v1/`, `/v2/`
- 向后兼容性：保持旧版本至少6个月
- 废弃通知：通过响应头`X-API-Deprecated`提前通知

**鉴权机制**：
- Bearer Token认证：`Authorization: Bearer <JWT_TOKEN>`
- Token有效期：24小时，支持刷新
- 权限粒度：接口级+资源级双重控制

**请求/响应格式**：
```json
// 统一请求格式
{
  "data": { /* 业务数据 */ },
  "meta": { /* 元数据，如分页信息 */ }
}

// 统一响应格式
{
  "code": 0,                    // 业务状态码，0表示成功
  "message": "success",         // 状态描述
  "data": { /* 响应数据 */ },
  "meta": {
    "request_id": "req_123456", // 请求追踪ID
    "timestamp": "2024-12-19T10:30:00Z",
    "version": "v1.0"
  }
}
```

**分页规范**：
- 使用`limit`和`offset`参数
- 响应包含`total`, `page_size`, `page_number`
- 最大每页限制：100条记录

**错误处理**：
- HTTP状态码与业务错误码分离
- 错误响应包含`error_code`, `error_detail`, `suggestions`
- 支持国际化错误信息

### 5.2 API接口清单

| 模块 | 接口分组 | 接口数量 | 主要功能 |
|---|---|---|---|
| 维修知识库管理 | 知识库CRUD | 8 | 创建、查询、更新、删除知识库 |
| | 文档管理 | 12 | 上传、解析、索引、状态管理 |
| | 分段操作 | 6 | 分段增删改查、批量操作 |
| | 元数据管理 | 8 | 字段定义、批量标注、查询 |
| | 智能问答 | 6 | 问答、会话、历史、反馈 |
| | 检索服务 | 5 | 向量检索、手册定位、测试 |
| | 外部知识库 | 4 | 配置、检索、测试、管理 |
| | 质量监控 | 4 | 测试评估、指标监控、策略配置 |
| | 权限审计 | 6 | 权限控制、审计日志、访问记录 |
| 维修规划及资源智能化 | 计划管理 | 待补充 | 计划生成、调整、执行跟踪 |
| | 资源管理 | 待补充 | 航材、人员、工具配置 |
| | 冲突解决 | 待补充 | 资源冲突检测与解决 |
| 生产看板 | 看板展示 | 待补充 | 计划、进度、资源、工位看板 |
| | 数据聚合 | 待补充 | 实时数据收集与计算 |
| | 告警通知 | 待补充 | 异常告警与通知推送 |
| 发动机检测辅助 | 检测管理 | 待补充 | 任务创建、路径规划 |
| | 数据分析 | 待补充 | 实时分析、历史分析 |
| | 预警管理 | 待补充 | 异常检测、预警推送 |

### 5.3 限流策略

**API限流规则**：
- 用户级限流：1000 req/hour
- IP级限流：5000 req/hour  
- 接口级限流：根据业务重要性分级
- 突发流量：允许短时间超限，后续限制

**限流实现**：
- 使用Redis + Lua脚本实现分布式限流
- 支持滑动窗口和令牌桶算法
- 提供限流状态查询接口

## 6. 非功能需求

### 6.1 可用性/SLA指标

- 系统可用性：99.9%（年计划外停机时间≤8.76小时）
- 服务恢复时间：平均故障恢复时间(MTTR) ≤ 30分钟
- 故障检测时间：平均故障检测时间(MTTD) ≤ 5分钟
- API可用性：核心接口99.95%，非核心接口99.9%

### 6.2 性能指标

**响应时间要求**：
- 知识库列表查询：≤200ms (P95)
- 文档上传接口：≤2s (P95)
- 智能问答接口：≤3s (P95)
- 检索服务接口：≤1s (P95)

**吞吐量要求**：
- 知识库管理：200 QPS
- 智能问答服务：100 QPS  
- 检索服务：300 QPS
- 并发用户：支持1000个活跃用户

### 6.3 扩展性要求

**水平扩展能力**：
- API服务：无状态设计，支持负载均衡
- 数据库：读写分离，支持分片扩展
- 向量库：支持集群模式
- 缓存：Redis集群部署

**数据扩展能力**：
- 支持TB级知识库数据存储
- 支持百万级分段向量索引
- 支持万级并发检索请求

### 6.4 可靠性要求

**数据备份策略**：
- 数据库：每日增量备份，每周全量备份
- 文件存储：异地冗余存储，3副本保证
- 向量数据：定期快照备份
- 配置数据：版本化管理，支持快速回滚

**容灾恢复**：
- RTO（恢复时间目标）：≤4小时
- RPO（恢复点目标）：≤1小时
- 支持跨机房容灾部署
- 关键服务双活架构

### 6.5 安全与隐私要求

**数据安全**：
- 传输加密：TLS 1.3
- 存储加密：AES-256
- 密钥管理：独立密钥管理服务
- 敏感数据脱敏：自动化脱敏规则

**访问安全**：
- 身份认证：JWT + 多因素认证
- 权限控制：RBAC细粒度权限
- 操作审计：完整审计日志
- 防护措施：防SQL注入、XSS、CSRF

### 6.6 可维护性要求

**监控与告警**：
- 系统监控：CPU、内存、磁盘、网络
- 应用监控：响应时间、错误率、吞吐量
- 业务监控：知识库使用量、问答质量
- 告警通知：多渠道告警，升级机制

**日志管理**：
- 结构化日志：JSON格式统一输出
- 日志等级：ERROR、WARN、INFO、DEBUG
- 日志聚合：ELK Stack集中管理
- 日志保留：业务日志30天，审计日志1年

## 7. 部署与运维

### 7.1 部署架构

**容器化部署架构**：

```mermaid
graph TB
    subgraph "负载均衡层"
        LB[负载均衡器]
    end
    
    subgraph "应用层"
        API1[API服务实例1]
        API2[API服务实例2]
        API3[API服务实例3]
    end
    
    subgraph "服务层"
        KB[知识库服务]
        QA[问答服务]
        RET[检索服务]
        TASK[任务队列服务]
    end
    
    subgraph "数据层"
        PG[(PostgreSQL)]
        VDB[(向量数据库)]
        REDIS[(Redis缓存)]
        STORAGE[(对象存储)]
    end
    
    LB --> API1
    LB --> API2
    LB --> API3
    
    API1 --> KB
    API2 --> QA
    API3 --> RET
    
    KB --> PG
    QA --> VDB
    RET --> REDIS
    TASK --> STORAGE
```

**部署环境规划**：

| 环境 | 用途 | 配置 | 数据保留 |
|---|---|---|---|
| 开发环境 | 功能开发测试 | 2核4GB×3, 单副本 | 7天 |
| 测试环境 | 集成测试验证 | 4核8GB×3, 高可用 | 30天 |
| 预生产环境 | 性能测试验证 | 生产配置×0.5, 高可用 | 90天 |
| 生产环境 | 正式服务 | 8核16GB×5, 三副本 | 永久 |

### 7.2 部署配置

**Docker容器配置**：
```yaml
# docker-compose.yml
version: '3.8'
services:
  knowledge-api:
    image: knowledge-base:v1.0
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/knowledge_db
      - REDIS_URL=redis://redis:6379/0
      - VECTOR_DB_URL=http://vectordb:8080
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
          cpus: "1.0"
        reservations:
          memory: 1G
          cpus: "0.5"
```

**Kubernetes部署配置**：
```yaml
# k8s-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: knowledge-api
  labels:
    app: knowledge-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: knowledge-api
  template:
    metadata:
      labels:
        app: knowledge-api
    spec:
      containers:
      - name: api
        image: knowledge-base:v1.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: database-url
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 7.3 运维监控

**健康检查**：
- 应用健康检查：`/health` 端点检查服务状态
- 就绪检查：`/ready` 端点检查依赖服务连通性
- 深度检查：`/health/deep` 端点检查业务功能可用性

**监控指标**：
```yaml
# prometheus配置
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'knowledge-api'
    static_configs:
      - targets: ['knowledge-api:8000']
    metrics_path: /metrics
    scrape_interval: 10s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

**日志收集**：
```yaml
# filebeat配置
filebeat.inputs:
- type: container
  paths:
    - /var/lib/docker/containers/*/*.log
  processors:
  - add_docker_metadata:
      host: "unix:///var/run/docker.sock"
  - decode_json_fields:
      fields: ["message"]
      target: ""
      overwrite_keys: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "knowledge-base-logs-%{+yyyy.MM.dd}"
```

### 7.4 备份与恢复

**数据备份策略**：
```bash
#!/bin/bash
# 数据库备份脚本
pg_dump -h postgres -U knowledge_user -d knowledge_db \
  --no-password --clean --if-exists \
  --format=custom \
  --file=/backup/knowledge_db_$(date +%Y%m%d_%H%M%S).dump

# 向量数据备份
curl -X POST "http://vectordb:8080/collections/knowledge/snapshots" \
  -H "Content-Type: application/json" \
  -d '{"snapshot_name": "daily_'$(date +%Y%m%d)'"}'

# 文件备份到对象存储
aws s3 sync /data/files s3://knowledge-backup/files/$(date +%Y%m%d)/
```

**恢复流程**：
1. 确认备份文件完整性
2. 停止应用服务
3. 恢复数据库：`pg_restore -d knowledge_db backup.dump`
4. 恢复向量数据：从快照恢复向量索引
5. 恢复文件数据：从对象存储下载文件
6. 启动应用服务并验证

## 8. 测试设计

### 8.1 测试覆盖范围

**功能测试**：
- 知识库CRUD操作完整性测试
- 文档上传、解析、索引流程测试
- 智能问答准确性与响应时间测试
- 检索功能精确度与召回率测试

**性能测试**：
- 并发用户访问压力测试
- 大文件上传性能测试
- 海量数据检索性能测试
- 系统资源使用率测试

**安全测试**：
- 身份认证与授权测试
- API安全漏洞扫描
- 数据传输加密验证
- 敏感信息泄露检测

### 8.2 关键测试用例

| 用例类别 | 用例名称 | 前置条件 | 测试步骤 | 期望结果 | 自动化 |
|---|---|---|---|---|---|
| 知识库管理 | 创建知识库 | 用户已登录 | 1.填写名称描述 2.选择权限 3.提交创建 | 知识库创建成功，返回ID | 是 |
| 文档处理 | 大文件上传 | 准备100MB PDF文件 | 1.选择文件 2.上传 3.等待解析 | 30秒内解析完成 | 是 |
| 智能问答 | 维修问题问答 | 知识库已建立 | 1.输入"发动机故障" 2.等待回答 | 3秒内返回相关答案 | 是 |
| 检索服务 | 手册定位 | 手册已上传索引 | 1.输入定位查询 2.获取结果 | 1秒内返回章节位置 | 是 |
| 性能测试 | 并发问答 | 100个虚拟用户 | 1.同时发起问答 2.记录响应时间 | 95%请求<5秒 | 是 |

### 8.3 自动化测试

**单元测试**：
```python
# 示例单元测试
import pytest
from knowledge_service import DatasetService

class TestDatasetService:
    def test_create_dataset(self):
        service = DatasetService()
        dataset = service.create_dataset(
            name="测试知识库",
            permission="only_me",
            description="单元测试用知识库"
        )
        assert dataset.id is not None
        assert dataset.name == "测试知识库"
        
    def test_upload_document(self):
        service = DatasetService()
        dataset = service.create_dataset("测试库", "only_me")
        
        with open("test.pdf", "rb") as f:
            document = service.upload_document(
                dataset_id=dataset.id,
                file=f,
                metadata={"type": "manual"}
            )
        assert document.status == "uploaded"
```

**集成测试**：
```python
# API集成测试
import requests

def test_qa_flow():
    # 创建知识库
    response = requests.post("/v1/datasets", json={
        "name": "集成测试库",
        "permission": "only_me"
    })
    dataset_id = response.json()["data"]["id"]
    
    # 上传文档
    with open("manual.pdf", "rb") as f:
        files = {"file": f}
        response = requests.post(
            f"/v1/datasets/{dataset_id}/document/create_by_file",
            files=files
        )
    assert response.status_code == 200
    
    # 等待索引完成
    time.sleep(30)
    
    # 测试问答
    response = requests.post("/v1/chat-messages", json={
        "query": "如何启动发动机？",
        "inputs": {"device_model": "X100"}
    })
    assert response.status_code == 200
    assert "启动" in response.json()["data"]["answer"]
```

## 9. 风险与问题

### 9.1 技术风险

| 风险项 | 风险等级 | 影响范围 | 缓解策略 | 应急预案 |
|---|---|---|---|---|
| 向量数据库性能瓶颈 | 高 | 检索服务 | 分片部署，读写分离 | 降级为关键词检索 |
| 大语言模型服务中断 | 中 | 问答功能 | 多供应商备用 | 切换备用模型 |
| 文档解析失败率高 | 中 | 知识库构建 | 多解析器并行 | 人工处理失败文档 |
| 数据库连接池耗尽 | 中 | 整体服务 | 连接池监控 | 重启服务释放连接 |

### 9.2 业务风险

| 风险项 | 风险等级 | 影响范围 | 缓解策略 | 应急预案 |
|---|---|---|---|---|
| 问答准确率不达标 | 高 | 用户体验 | 持续优化模型 | 人工客服兜底 |
| 知识库数据泄露 | 高 | 安全合规 | 加密存储传输 | 立即隔离受影响系统 |
| 用户采纳率低 | 中 | 项目价值 | 用户培训推广 | 调整产品策略 |
| 维修手册版本混乱 | 中 | 数据质量 | 版本管理流程 | 临时锁定问题版本 |

### 9.3 开放问题与待确认项

**待确认问题**：
1. 大语言模型的具体选型和配置参数
2. 向量数据库的分片策略和副本数量
3. 文档解析服务的具体实现方案
4. 与SAP系统的集成接口规范

**待补充项**：
1. 详细的错误码定义和国际化方案
2. 生产环境的灾备切换流程
3. 数据迁移工具的开发计划
4. 用户权限模型的细化设计

## 10. 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|---|---|---|---|
| v1.0 | 2025-09-01 | 初版发布，完成整体系统架构和维修知识库管理模块详细设计 | 系统架构师团队 |
| | | 包含四大功能模块总体设计，维修知识库管理模块详细实现 | |
| | | 定义了数据模型、接口规范、部署方案等技术基础架构 | |
| | | 为其他三个模块预留了详细设计占位符，待后续补充完善 | |

## 附录

### 附录A. 术语表

| 术语 | 英文 | 定义 |
|---|---|---|
| 检索增强生成 | RAG (Retrieval-Augmented Generation) | 结合检索和生成的AI技术，通过检索相关知识来增强答案生成质量 |
| 向量嵌入 | Vector Embedding | 将文本转换为高维向量表示，用于语义相似度计算 |
| 分段 | Segment | 将长文档切分为的较小文本块，便于检索和引用 |
| 重排序 | Reranking | 对初步检索结果进行二次排序，提升相关性 |

### 附录B. 参考链接

1. [PostgreSQL官方文档](https://www.postgresql.org/docs/)
2. [FastAPI框架文档](https://fastapi.tiangolo.com/)
3. [Docker容器化指南](https://docs.docker.com/)
4. [Kubernetes部署文档](https://kubernetes.io/docs/)
5. [Prometheus监控指南](https://prometheus.io/docs/)

### 附录C. 关联代码/配置路径

基于项目代码结构，主要模块对应的实现路径：

**维修知识库管理模块**：
- 知识库管理服务：`api/services/dataset_service.py`
- 文档处理服务：`api/services/file_service.py`
- 检索服务：`api/core/rag/retrieval/`, `api/core/rag/datasource/retrieval_service.py`
- 问答服务：`api/services/app_generate_service.py`
- 向量存储服务：`api/services/vector_service.py`
- 元数据服务：`api/services/metadata_service.py`
- 外部知识服务：`api/services/external_knowledge_service.py`
- 知识实体：`api/services/entities/knowledge_entities/`
- 检索测试服务：`api/services/hit_testing_service.py`
- 数据模型：`api/models/dataset.py`
- API控制器：`api/controllers/console/datasets/`, `api/controllers/service_api/dataset/`
- 任务队列：`api/tasks/add_document_to_index_task.py`, `api/tasks/document_indexing_task.py`
- RAG核心：`api/core/rag/embedding/`, `api/core/rag/extractor/`, `api/core/rag/index_processor/`

**维修规划及资源智能化模块**：
- 待补充：计划生成服务、资源管理服务、调度算法等实现路径

**生产看板模块**：
- 待补充：看板服务、数据聚合服务、实时通信等实现路径

**发动机检测辅助模块**：
- 待补充：检测服务、分析引擎、预警服务等实现路径 