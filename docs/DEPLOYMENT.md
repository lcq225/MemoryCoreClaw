# MemoryCoreClaw 部署指南

> 从安装到生产的完整部署流程

---

## 📋 目录

- [环境要求](#环境要求)
- [安装方式](#安装方式)
- [基础配置](#基础配置)
- [高级配置](#高级配置)
- [与 AI Agent 集成](#与-ai-agent-集成)
- [生产环境部署](#生产环境部署)
- [监控与维护](#监控与维护)
- [故障排查](#故障排查)

---

## 环境要求

### 基础要求

| 项目 | 版本要求 |
|------|---------|
| Python | ≥ 3.8 |
| SQLite | ≥ 3.35.0 |
| 内存 | ≥ 100MB |
| 磁盘 | ≥ 50MB |

### 可选依赖

| 功能 | 依赖包 |
|------|--------|
| 语义搜索 | `sentence-transformers` |
| 可视化 | `matplotlib`, `networkx` |
| 加密存储 | `cryptography` |

---

## 安装方式

### 方式一：PyPI 安装（推荐）

```bash
pip install memorycoreclaw
```

### 方式二：从源码安装

```bash
git clone https://github.com/lcq225/MemoryCoreClaw.git
cd MemoryCoreClaw
pip install -e .
```

### 方式三：指定可选依赖

```bash
# 安装语义搜索支持
pip install memorycoreclaw[embeddings]

# 安装可视化支持
pip install memorycoreclaw[visualization]

# 安装开发依赖
pip install memorycoreclaw[dev]
```

---

## 基础配置

### 快速开始

```python
from memorycoreclaw import Memory

# 使用默认配置
mem = Memory()

# 指定数据库路径
mem = Memory(db_path="/path/to/your/memory.db")
```

### 配置文件

创建 `config/memory.yaml`：

```yaml
# 数据库配置
database:
  path: "~/.memorycoreclaw/memory.db"
  encrypt: false
  pool_size: 5

# 记忆分层
layers:
  core:
    min_importance: 0.9
    retention: permanent
  important:
    min_importance: 0.7
    retention: long_term
  normal:
    min_importance: 0.5
    retention: standard
  minor:
    min_importance: 0.0
    retention: may_decay

# 遗忘曲线
forgetting:
  enabled: true
  decay_rate: 0.1
  min_strength: 0.1
  access_bonus: 1.1

# 工作记忆
working_memory:
  capacity: 9
  eviction_policy: lowest_priority
  default_ttl: 3600

# 语义搜索
semantic:
  enabled: false
  model: "sentence-transformers/all-MiniLM-L6-v2"
  dimensions: 384
```

---

## 高级配置

### 语义搜索配置

```python
from memorycoreclaw import Memory

# 启用语义搜索
mem = Memory(
    db_path="memory.db",
    embedding_config={
        "backend": "openai",
        "api_key": "your-api-key",
        "base_url": "https://api.openai.com/v1",
        "model_name": "text-embedding-3-small",
        "dimensions": 1536
    }
)

# 或使用本地模型
mem = Memory(
    db_path="memory.db",
    embedding_config={
        "backend": "openai",
        "api_key": "ollama",
        "base_url": "http://localhost:11434/v1",
        "model_name": "bge-m3",
        "dimensions": 1024
    }
)
```

### 环境变量配置

```bash
# 数据库路径
export MEMORY_DB_PATH="/data/memory.db"

# 输出目录
export MEMORY_OUTPUT_DIR="/data/output"

# Embedding 配置
export MEMORY_EMBEDDING_BACKEND="openai"
export MEMORY_EMBEDDING_API_KEY="your-key"
export MEMORY_EMBEDDING_BASE_URL="https://api.openai.com/v1"
export MEMORY_EMBEDDING_MODEL="text-embedding-3-small"
```

---

## 与 AI Agent 集成

### 与 CoPaw 集成

MemoryCoreClaw 可作为 CoPaw 的技能使用：

```
# 目录结构
.copaw/
└── workspaces/
    └── default/
        └── active_skills/
            └── memorycoreclaw/
                ├── __init__.py
                ├── core/
                ├── cognitive/
                ├── retrieval/
                ├── storage/
                ├── utils/
                └── scripts/
```

```python
# 在 CoPaw 中使用
import sys
sys.path.insert(0, 'active_skills')
from memorycoreclaw import Memory

mem = Memory(db_path=r"memory.db")

# 记住用户偏好
mem.remember("用户喜欢简洁的回复", importance=0.85, category="preference")

# 召回记忆辅助回复
preferences = mem.recall_by_category("preference")
```

### 与 LangChain 集成

```python
from langchain.memory import BaseMemory
from memorycoreclaw import Memory

class MemoryCoreClawMemory(BaseMemory):
    """LangChain 记忆适配器"""
    
    def __init__(self, db_path=None):
        self.mem = Memory(db_path=db_path)
    
    @property
    def memory_variables(self):
        return ["memory_context"]
    
    def load_memory_variables(self, inputs):
        query = inputs.get("input", "")
        memories = self.mem.recall(query, limit=5)
        context = "\n".join([m["content"] for m in memories])
        return {"memory_context": context}
    
    def save_context(self, inputs, outputs):
        user_input = inputs.get("input", "")
        ai_output = outputs.get("output", "")
        self.mem.remember(
            f"User: {user_input}",
            importance=0.5,
            source="user"
        )
        self.mem.remember(
            f"AI: {ai_output}",
            importance=0.5,
            source="llm"
        )
    
    def clear(self):
        pass

# 使用
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain

memory = MemoryCoreClawMemory()
llm = ChatOpenAI()
chain = ConversationChain(llm=llm, memory=memory)
```

### 与 AutoGen 集成

```python
from memorycoreclaw import Memory
import autogen

# 创建记忆增强的 Agent
class MemoryEnabledAgent(autogen.ConversableAgent):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self.memory = Memory()
    
    def generate_reply(self, messages, sender=None, **kwargs):
        # 召回相关记忆
        last_message = messages[-1]["content"] if messages else ""
        relevant_memories = self.memory.recall(last_message, limit=3)
        
        # 增强上下文
        memory_context = "\n".join([m["content"] for m in relevant_memories])
        if memory_context:
            messages = [{
                "role": "system",
                "content": f"相关记忆：\n{memory_context}"
            }] + messages
        
        # 生成回复
        reply = super().generate_reply(messages, sender, **kwargs)
        
        # 记住对话
        self.memory.remember(
            f"与 {sender} 对话：{last_message[:100]}",
            importance=0.5,
            source="user"
        )
        
        return reply
```

---

## 生产环境部署

### Docker 部署

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 创建数据目录
RUN mkdir -p /data

# 设置环境变量
ENV MEMORY_DB_PATH=/data/memory.db
ENV MEMORY_OUTPUT_DIR=/data/output

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from memorycoreclaw import Memory; m = Memory(); print('OK')" || exit 1

CMD ["python", "-m", "memorycoreclaw.utils.visualization"]
```

```bash
# 构建镜像
docker build -t memorycoreclaw:2.1.0 .

# 运行容器
docker run -d \
    --name memorycoreclaw \
    -v /data/memory:/data \
    -e MEMORY_DB_PATH=/data/memory.db \
    memorycoreclaw:2.1.0
```

### Kubernetes 部署

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: memorycoreclaw
spec:
  replicas: 1
  selector:
    matchLabels:
      app: memorycoreclaw
  template:
    metadata:
      labels:
        app: memorycoreclaw
    spec:
      containers:
      - name: memorycoreclaw
        image: memorycoreclaw:2.1.0
        ports:
        - containerPort: 8080
        env:
        - name: MEMORY_DB_PATH
          value: "/data/memory.db"
        volumeMounts:
        - name: data
          mountPath: /data
        livenessProbe:
          exec:
            command:
            - python
            - -c
            - "from memorycoreclaw import Memory; Memory()"
          initialDelaySeconds: 10
          periodSeconds: 30
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: memorycoreclaw-pvc
```

---

## 监控与维护

### 健康检查脚本

```bash
# 检查数据库状态
python scripts/check_memory.py

# 输出示例：
# 📊 MemoryCoreClaw 数据库状态
# ================================
# 📝 事实记忆：124 条
# 📚 经验教训：51 条
# 🔗 实体关系：45 条
# 🎯 实体定义：42 条
# 
# ✅ 数据库健康
```

### 定期优化

```bash
# 优化数据库
python scripts/optimize_database.py

# 输出示例：
# 🔧 数据库优化完成
# - 清理孤立记录：3 条
# - 修复记忆强度：5 条
# - 补充实体定义：2 条
```

### 自动化维护（Cron）

```bash
# 添加到 crontab
# 每天凌晨 2 点优化数据库
0 2 * * * cd /app && python scripts/optimize_database.py >> /var/log/memory_optimize.log 2>&1

# 每周日凌晨 3 点检查重复
0 3 * * 0 cd /app && python scripts/check_duplicates.py >> /var/log/memory_check.log 2>&1
```

---

## 故障排查

### 常见问题

#### 1. 数据库锁定

```
错误：database is locked
```

**解决方案：**
- 确保没有其他进程占用数据库
- 使用连接池
- 考虑使用 WAL 模式

```python
# 启用 WAL 模式
mem = Memory(db_path="memory.db", wal_mode=True)
```

#### 2. 向量搜索失败

```
错误：embedding failed
```

**解决方案：**
- 检查 Embedding 配置
- 确认模型可用
- 自动降级到关键词搜索

```python
# 检查配置
from memorycoreclaw import Memory
mem = Memory(
    db_path="memory.db",
    embedding_config={
        "backend": "openai",
        "base_url": "http://localhost:11434/v1",  # 本地 Ollama
        "model_name": "bge-m3"
    }
)

# 测试连接
result = mem.recall("测试", limit=1)
print(f"搜索状态：{'成功' if result else '失败'}")
```

#### 3. 内存占用过高

**解决方案：**
- 定期清理低重要性记忆
- 使用记忆压缩
- 限制工作记忆容量

```bash
# 清理低重要性记忆
python scripts/optimize_database.py --cleanup-minor
```

### 日志配置

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='memorycoreclaw.log'
)

# 使用
from memorycoreclaw import Memory
mem = Memory(db_path="memory.db")
# 操作日志会自动记录
```

---

## 升级指南

### 从 v2.0.0 升级到 v2.1.0

```bash
# 1. 备份数据库
cp memory.db memory.db.backup

# 2. 升级包
pip install memorycoreclaw==2.1.0

# 3. 运行优化脚本（添加新字段）
python scripts/optimize_database.py --upgrade

# 4. 验证
python scripts/check_memory.py
```

### 数据迁移

```python
# 从旧版本迁移数据
from memorycoreclaw import Memory

# 连接旧数据库
old_mem = Memory(db_path="old_memory.db")
# 导出数据
data = old_mem.export_json()

# 连接新数据库
new_mem = Memory(db_path="new_memory.db")
# 导入数据
new_mem.import_json(data)
```

---

**MemoryCoreClaw v2.1.0** - 安全、可靠的 AI 记忆引擎