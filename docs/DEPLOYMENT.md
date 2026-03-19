# MemoryCoreClaw 部署文档

本文档详细介绍 MemoryCoreClaw 的安装、配置和部署方式。

---

## 目录

1. [环境要求](#环境要求)
2. [安装方式](#安装方式)
3. [配置说明](#配置说明)
4. [部署场景](#部署场景)
5. [数据管理](#数据管理)
6. [性能优化](#性能优化)
7. [故障排查](#故障排查)

---

## 环境要求

### 系统要求

| 系统 | 版本 | 状态 |
|------|------|------|
| Windows | 10/11 | ✅ 支持 |
| Linux | Ubuntu 18.04+, CentOS 7+ | ✅ 支持 |
| macOS | 10.15+ | ✅ 支持 |

### Python 版本

| Python 版本 | 状态 |
|-------------|------|
| 3.8 | ⚠️ 最低要求 |
| 3.9 | ✅ 推荐 |
| 3.10 | ✅ 支持 |
| 3.11 | ✅ 支持 |
| 3.12+ | 🧪 测试中 |

### 依赖项

```
# 核心依赖（必需）
sqlite3      # Python 内置

# 可选依赖
sentence-transformers  # 语义搜索
cryptography          # 数据库加密
```

---

## 安装方式

### 方式一：PyPI 安装（推荐）

```bash
pip install memorycoreclaw
```

### 方式二：从源码安装

```bash
# 克隆仓库
git clone https://github.com/lcq225/MemoryCoreClaw.git
cd MemoryCoreClaw

# 安装
pip install -e .
```

### 方式三：下载 Release

```bash
# 从 GitHub Releases 下载
wget https://github.com/lcq225/MemoryCoreClaw/archive/refs/tags/v1.0.0.tar.gz
tar -xzf v1.0.0.tar.gz
cd MemoryCoreClaw-1.0.0
pip install .
```

### 验证安装

```python
from memorycoreclaw import Memory
mem = Memory()
print("✅ 安装成功！")
```

---

## 配置说明

### 配置文件位置

```
~/.memorycoreclaw/
├── memory.db        # 默认数据库
├── config.yaml      # 用户配置（可选）
└── backups/         # 备份目录
```

### 配置文件格式

创建 `~/.memorycoreclaw/config.yaml`：

```yaml
# 数据库配置
database:
  path: "~/.memorycoreclaw/memory.db"
  encrypt: false                    # 是否加密
  encryption_key: null              # 加密密钥（如启用）

# 记忆分层配置
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

# 遗忘曲线配置
forgetting:
  enabled: true
  min_strength: 0.1                 # 最低强度阈值
  access_bonus: 1.1                 # 访问加成
  decay_rate: 0.1                   # 衰减率

# 工作记忆配置
working_memory:
  capacity: 9                       # 容量（7±2 模型）
  eviction_policy: lowest_priority  # 驱逐策略
  default_ttl: null                 # 默认过期时间（秒）

# 语义搜索配置
semantic_search:
  enabled: true
  embedding_model: null             # 嵌入模型（如 sentence-transformers）
  keyword_fallback: true            # 关键词回退

# 关系学习配置
ontology:
  allow_custom_relations: true      # 允许自定义关系
  inference_threshold: 0.5          # 推断阈值

# 导出配置
export:
  default_format: json
  include_metadata: true

# 日志配置
logging:
  level: INFO                       # DEBUG, INFO, WARNING, ERROR
  file: null                        # 日志文件路径
```

### 代码中指定配置

```python
from memorycoreclaw import Memory

# 方式一：指定数据库路径
mem = Memory(db_path="/path/to/custom.db")

# 方式二：使用配置文件
# 配置文件会自动从 ~/.memorycoreclaw/config.yaml 加载
mem = Memory()
```

---

## 部署场景

### 场景一：单机应用

最简单的部署方式，适用于个人项目或单用户场景。

```python
from memorycoreclaw import Memory

# 默认配置，数据存储在 ~/.memorycoreclaw/memory.db
mem = Memory()
```

### 场景二：多用户应用

为每个用户创建独立的数据库或使用 session_id 隔离。

```python
from memorycoreclaw import Memory

# 方式一：每个用户独立数据库
user_mem = Memory(db_path=f"/data/memories/{user_id}.db")

# 方式二：共享数据库，session 隔离（工作记忆）
user_mem = Memory(db_path="/data/shared.db", session_id=user_id)
```

### 场景三：服务器部署

```python
import os
from memorycoreclaw import Memory

# 使用环境变量配置
db_path = os.environ.get("MEMORY_DB_PATH", "/data/memory.db")
mem = Memory(db_path=db_path)
```

### 场景四：Docker 部署

**Dockerfile**

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装依赖
RUN pip install memorycoreclaw

# 创建数据目录
RUN mkdir -p /data

# 设置环境变量
ENV MEMORY_DB_PATH=/data/memory.db

# 复制应用代码
COPY app.py .

CMD ["python", "app.py"]
```

**docker-compose.yml**

```yaml
version: '3.8'

services:
  app:
    build: .
    volumes:
      - memory_data:/data
    environment:
      - MEMORY_DB_PATH=/data/memory.db

volumes:
  memory_data:
```

**运行**

```bash
docker-compose up -d
```

### 场景五：Kubernetes 部署

**deployment.yaml**

```yaml
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
      - name: app
        image: memorycoreclaw:latest
        volumeMounts:
        - name: memory-storage
          mountPath: /data
        env:
        - name: MEMORY_DB_PATH
          value: /data/memory.db
      volumes:
      - name: memory-storage
        persistentVolumeClaim:
          claimName: memory-pvc
```

**pvc.yaml**

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: memory-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

---

## 数据管理

### 备份数据

```python
from memorycoreclaw import Memory
import json
from datetime import datetime

mem = Memory()

# 导出所有数据
data = mem.export()

# 保存到文件
backup_file = f"memory_backup_{datetime.now().strftime('%Y%m%d')}.json"
with open(backup_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"备份完成: {backup_file}")
```

### 恢复数据

```python
from memorycoreclaw import Memory
import json

mem = Memory()

# 从备份恢复
with open('memory_backup_20240319.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 导入数据
from memorycoreclaw.utils.export import MemoryExporter
exporter = MemoryExporter(mem.core)
exporter.import_data(data)

print("恢复完成！")
```

### 数据迁移

```python
import sqlite3
from memorycoreclaw import Memory

# 源数据库
source_db = "/old/path/memory.db"
# 目标数据库
target_db = "/new/path/memory.db"

# 直接复制数据库文件
import shutil
shutil.copy(source_db, target_db)

# 验证
mem = Memory(db_path=target_db)
stats = mem.get_stats()
print(f"迁移完成: {stats['facts']} 条记忆")
```

---

## 性能优化

### 数据库优化

```python
from memorycoreclaw import Memory
import sqlite3

mem = Memory()

# 手动执行 VACUUM（压缩数据库）
conn = sqlite3.connect(mem.core.db_path)
conn.execute("VACUUM")
conn.close()

print("数据库优化完成！")
```

### 批量操作

```python
from memorycoreclaw import Memory

mem = Memory()

# 批量添加记忆
facts = [
    ("Alice 擅长 Python", 0.8),
    ("Bob 擅长 Java", 0.7),
    ("Carol 擅长 Go", 0.7),
]

for content, importance in facts:
    mem.remember(content, importance=importance)

print(f"批量添加 {len(facts)} 条记忆")
```

### 索引优化

数据库已自动创建以下索引：
- `idx_facts_content` - 内容索引
- `idx_relations_from` - 关系起点索引
- `idx_relations_to` - 关系终点索引

---

## 故障排查

### 问题 1：数据库锁定

**症状：** `sqlite3.OperationalError: database is locked`

**原因：** SQLite 不支持多进程写入

**解决方案：**
```python
# 方案一：每个进程使用独立数据库
mem = Memory(db_path=f"/data/memory_{process_id}.db")

# 方案二：使用连接池（需要额外配置）
# 方案三：切换到 PostgreSQL/MySQL
```

### 问题 2：内存占用过高

**症状：** 内存使用持续增长

**解决方案：**
```python
from memorycoreclaw import Memory

mem = Memory()

# 清理低强度记忆
mem.apply_forgetting()

# 清理工作记忆
mem.clear_working_memory()

# 执行 VACUUM
import sqlite3
conn = sqlite3.connect(mem.core.db_path)
conn.execute("VACUUM")
conn.close()
```

### 问题 3：查询速度慢

**症状：** recall() 返回缓慢

**解决方案：**
```python
# 方案一：限制返回数量
results = mem.recall("query", limit=5)

# 方案二：使用更精确的关键词
results = mem.recall("Alice TechCorp")  # 比 "Alice" 更精确

# 方案三：定期执行 VACUUM 和 ANALYZE
import sqlite3
conn = sqlite3.connect(mem.core.db_path)
conn.execute("VACUUM")
conn.execute("ANALYZE")
conn.close()
```

### 问题 4：导入错误

**症状：** `ModuleNotFoundError: No module named 'memorycoreclaw'`

**解决方案：**
```bash
# 确认安装
pip list | grep memorycoreclaw

# 重新安装
pip install --force-reinstall memorycoreclaw

# 或从源码安装
git clone https://github.com/lcq225/MemoryCoreClaw.git
cd MemoryCoreClaw
pip install -e .
```

---

## 监控指标

```python
from memorycoreclaw import Memory

mem = Memory()

# 获取统计信息
stats = mem.get_stats()

print(f"""
MemoryCoreClaw 状态报告
========================
事实记忆: {stats['facts']} 条
经验教训: {stats['experiences']} 条
实体关系: {stats['relations']} 条
实体数量: {stats['entities']} 个
""")

# 检查数据库大小
import os
db_size = os.path.getsize(mem.core.db_path) / (1024 * 1024)
print(f"数据库大小: {db_size:.2f} MB")
```

---

## 安全建议

1. **数据加密**
   ```yaml
   database:
     encrypt: true
     encryption_key: "your-secret-key"
   ```

2. **访问控制**
   - 数据库文件权限设置为 600
   - 不要在代码中硬编码敏感信息

3. **定期备份**
   - 设置自动备份脚本
   - 异地备份重要数据

4. **日志审计**
   ```yaml
   logging:
     level: INFO
     file: "/var/log/memorycoreclaw.log"
   ```

---

## 常见问题 (FAQ)

**Q: 支持多语言吗？**
A: 是的，内容支持任意语言，但关系类型目前为英文。

**Q: 可以用于生产环境吗？**
A: 可以，SQLite 稳定可靠，支持百万级记录。

**Q: 如何实现分布式部署？**
A: 目前为单机版，分布式版本规划中。可通过每个节点独立数据库实现。

**Q: 数据会丢失吗？**
A: SQLite 是持久化存储，程序重启后数据不会丢失。建议定期备份。

---

## 更新日志

查看 [CHANGELOG.md](../CHANGELOG.md) 了解版本更新历史。

---

## 获取帮助

- 📖 文档：[docs/](./)
- 🐛 问题反馈：[GitHub Issues](https://github.com/lcq225/MemoryCoreClaw/issues)
- 💬 讨论：[GitHub Discussions](https://github.com/lcq225/MemoryCoreClaw/discussions)