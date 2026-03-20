# MemoryCoreClaw：面向 AI Agent 的类人脑分层记忆系统

> **摘要**
>
> 本文介绍 MemoryCoreClaw，一个模拟人类大脑记忆机制的分层记忆系统，旨在解决 AI Agent 在多轮对话中"每次像新认识一样从零开始"的问题。通过工作记忆（MEMORY.md）与长期记忆（memory.db）的分层协作，结合向量语义搜索、重要性评分、经验教训学习等机制，实现 AI Agent 的记忆延续与快速上下文恢复。

---

## 1. 背景与问题

### 1.1 传统 AI 记忆的局限

主流 AI Agent 框架（如 LangChain、AutoGPT 等）通常采用以下记忆方案：

| 方案 | 特点 | 局限性 |
|------|------|--------|
| **对话历史截断** | 保留最近 N 轮对话 | 超出窗口的历史信息丢失 |
| **摘要压缩** | 定期总结历史对话 | 细节丢失，无法精确检索 |
| **向量数据库** | 语义相似搜索 | 缺乏重要性区分、无结构化关系 |

### 1.2 核心痛点

**"每次会话都像新认识一样"**

- AI Agent 不记得用户的偏好、习惯、背景
- 不记得之前讨论过的项目、决策、教训
- 无法建立实体间的关联关系
- 无优先级区分，重要信息与闲聊同等对待

---

## 2. 设计理念：模拟人脑记忆机制

### 2.1 人类大脑的记忆分层

认知科学研究表明，人类大脑的记忆系统是分层的：

```
┌─────────────────────────────────────────────────────────────────────┐
│                     人类大脑记忆系统                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   工作记忆（Working Memory）                                        │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │ • 位置：前额叶皮层                                          │   │
│   │ • 容量：7±2 个信息块                                        │   │
│   │ • 作用：当前任务上下文、正在处理的信息                       │   │
│   │ • 特点：快速访问、容量有限、易丢失                           │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│                        信息巩固（Consolidation）                     │
│                              ↓                                      │
│   长期记忆（Long-term Memory）                                       │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │ • 位置：海马体 → 大脑皮层                                    │   │
│   │ • 容量：近乎无限                                             │   │
│   │ • 分类：                                                     │   │
│   │   - 情景记忆（Episodic）：事件、经历                         │   │
│   │   - 语义记忆（Semantic）：事实、知识                         │   │
│   │   - 程序记忆（Procedural）：技能、经验                       │   │
│   │ • 特点：持久存储、容量大、需检索才能访问                     │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 核心设计原则

| 人脑机制 | MemoryCoreClaw 实现 |
|----------|---------------------|
| **工作记忆** | MEMORY.md（工作记忆文件） |
| **长期记忆** | memory.db（结构化数据库） |
| **重要性加权** | importance 字段（0-1 评分） |
| **情感关联** | emotion 字段（影响回忆优先级） |
| **遗忘机制** | 记忆衰减算法（访问频率 × 时间衰减） |
| **关联网络** | 实体关系图谱（知识图谱） |
| **经验学习** | experiences 表（行动-情境-结果-洞察） |

---

## 3. 系统架构

### 3.1 分层架构设计

```
┌─────────────────────────────────────────────────────────────────────┐
│                     MemoryCoreClaw 架构                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   第一层：工作记忆层（MEMORY.md）                                    │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │ 内容：                                                      │   │
│   │ • 核心身份（Agent 身份、用户背景）                          │   │
│   │ • 核心偏好（沟通风格、工作习惯）                            │   │
│   │ • 关键配置（路径、密钥位置、输出目录）                      │   │
│   │ • 最近工作上下文（本周重点、进行中任务）                    │   │
│   │ • 常用信息（频繁查询的人、系统、配置）                      │   │
│   │ • 核心教训（必须遵守的规则）                                │   │
│   │ • 记忆搜索方法（如何访问长期记忆）                          │   │
│   │                                                             │   │
│   │ 特点：                                                      │   │
│   │ ✓ AI Agent 每次会话自动加载                                │   │
│   │ ✓ 快速热启动，恢复上下文                                   │   │
│   │ ✓ 人类可读，可手动编辑                                     │   │
│   │ ✓ 轻量（通常 <10KB）                                       │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│                        工作记忆未命中                               │
│                              ↓                                      │
│   第二层：长期记忆层（memory.db）                                    │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │ 数据结构：                                                  │   │
│   │ • facts（事实记忆）：内容、类别、重要性、情感、访问统计     │   │
│   │ • experiences（经验教训）：行动、情境、结果、洞察           │   │
│   │ • relations（实体关系）：实体1-关系-实体2，强度             │   │
│   │ • entities（实体定义）：名称、类型、重要性                  │   │
│   │ • memory_strength（记忆强度）：基础强度、当前强度、衰减     │   │
│   │                                                             │   │
│   │ 能力：                                                      │   │
│   │ ✓ 向量语义搜索（Embedding + 相似度计算）                   │   │
│   │ ✓ 重要性排序（核心记忆 vs 次要信息）                       │   │
│   │ ✓ 情境查询（按人物、地点、时间筛选）                       │   │
│   │ ✓ 关联推理（实体关系网络）                                 │   │
│   │ ✓ 记忆衰减（模拟遗忘，避免膨胀）                           │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                              ↑                                      │
│                        定期沉淀与同步                               │
│                              │                                      │
│   第三层：每日记录层（memory/*.md）                                  │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │ • 今日工作日志                                              │   │
│   │ • 会议纪要                                                  │   │
│   │ • 学习笔记                                                  │   │
│   │ • 临时备忘                                                  │   │
│   │                                                             │   │
│   │ 流转：每日笔记 → 提取精华 → 存入长期记忆                    │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 类比计算机存储层次

| 计算机存储 | MemoryCoreClaw | 特点 |
|------------|----------------|------|
| **L1/L2 缓存** | 会话上下文 | 最快，当前对话 |
| **内存** | MEMORY.md | 快速，每次会话加载 |
| **硬盘** | memory.db | 容量大，需要时检索 |

---

## 4. 核心功能

### 4.1 向量语义搜索

```python
from memorycoreclaw import Memory

mem = Memory(db_path="memory.db")

# 语义搜索，而非关键词匹配
results = mem.recall("谁负责权限系统", limit=5)
# → 返回语义相关的记忆，即使没有"权限系统"字面匹配

# 支持模糊查询
results = mem.recall("上次那个项目的问题", limit=5)
# → 根据语义相似度返回相关记忆
```

**技术实现：**
- 本地 Embedding 模型（如 BGE-M3）
- 向量维度：1024
- 相似度计算：余弦相似度

### 4.2 重要性评分与分层

| 重要性范围 | 级别 | 处理方式 |
|------------|------|----------|
| ≥0.9 | 核心记忆 | 永久保留，注入工作记忆 |
| 0.7-0.9 | 重要记忆 | 长期保留，优先检索 |
| 0.5-0.7 | 普通记忆 | 正常保留 |
| <0.5 | 次要记忆 | 可能衰减，定期清理 |

```python
# 写入时指定重要性
mem.remember("核心配置信息", importance=0.9, category="config")

# 查询核心记忆
results = mem.recall_by_importance(min_importance=0.9)
```

### 4.3 经验教训学习

模拟人类"吃一堑长一智"的学习机制：

```python
mem.learn(
    action="执行的操作",
    context="发生的情境",
    outcome="negative",  # positive/negative/neutral
    insight="学到的教训",
    importance=0.9
)
```

**数据结构：**
| 字段 | 说明 |
|------|------|
| action | 执行的动作 |
| context | 发生的背景情境 |
| outcome | 结果（positive/negative/neutral） |
| insight | 总结的教训或经验 |

### 4.4 实体关系网络

构建知识图谱，支持关联推理：

```python
# 建立关系
mem.relate("张三", "负责", "财务系统")
mem.relate("财务系统", "部署在", "云端服务器")

# 获取关联网络
network = mem.associate("张三", depth=1)
# → 返回：张三 → 负责 → 财务系统 → 部署在 → 云端服务器
```

### 4.5 记忆衰减机制

模拟人类遗忘，避免数据库无限膨胀：

```
当前强度 = 基础强度 × 时间衰减因子 × 访问加成

时间衰减因子 = e^(-λ × 天数)
访问加成 = 1 + log(访问次数 + 1) × α
```

---

## 5. 与 AI Agent 框架的集成

### 5.1 设计原则

1. **不破坏原生机制** — 兼容现有 AI Agent 框架的记忆加载方式
2. **分层协作** — 工作记忆自动加载，长期记忆按需检索
3. **最小侵入** — 作为独立模块，通过 API 调用

### 5.2 集成示例

```
AI Agent 会话流程：

1. 会话启动
   ├── 读取 MEMORY.md（工作记忆）
   │   → 快速恢复上下文
   │   → 知道"我是谁、用户是谁、最近在做什么"
   │
2. 对话过程
   ├── 遇到需要回忆的信息
   │   ├── 先检查 MEMORY.md
   │   └── 未命中 → mem.recall("关键词") 搜索 memory.db
   │
   ├── 学习新知识
   │   ├── mem.remember("内容", importance, category)
   │   └── 定期同步到 MEMORY.md
   │
   └── 犯错总结
       └── mem.learn(action, context, outcome, insight)

3. 会话结束
   └── 更新每日笔记 memory/YYYY-MM-DD.md
```

### 5.3 兼容性矩阵

| AI Agent 框架 | 集成方式 | 状态 |
|---------------|----------|------|
| CoPaw | 原生读取 MEMORY.md | ✅ 已验证 |
| LangChain | 作为 Memory 模块 | 可扩展 |
| AutoGPT | 作为长期存储后端 | 可扩展 |
| 自定义 Agent | Python API 调用 | ✅ 支持 |

---

## 6. 实际应用效果

### 6.1 解决的问题

| 问题 | 传统方案 | MemoryCoreClaw |
|------|----------|----------------|
| 每次会话像新认识 | 需要用户重复介绍 | 自动加载工作记忆 |
| 信息检索不精准 | 关键词匹配，漏相关内容 | 向量语义搜索 |
| 重要信息被淹没 | 扁平存储，无优先级 | 重要性评分，分层存储 |
| 重复犯错 | 无经验记录 | 经验教训学习 |
| 信息碎片化 | 无关联关系 | 实体关系网络 |

### 6.2 性能指标

| 指标 | 数值 |
|------|------|
| 工作记忆加载时间 | <100ms |
| 向量搜索延迟（本地） | <200ms |
| 数据库大小（100条记忆） | ~50KB |
| 支持的最大记忆条数 | 无硬性限制 |

---

## 7. 技术实现

### 7.1 技术栈

| 组件 | 技术选型 |
|------|----------|
| 数据库 | SQLite（轻量、嵌入、加密可选） |
| 向量索引 | SQLite + 余弦相似度计算 |
| Embedding | BGE-M3（本地）或 OpenAI API |
| 文件格式 | Markdown（人类可读）+ JSON（结构化） |

### 7.2 数据库 Schema

```sql
-- 事实记忆
CREATE TABLE facts (
    id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    category TEXT,
    importance REAL DEFAULT 0.5,
    emotion TEXT,
    tags TEXT,
    access_count INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 经验教训
CREATE TABLE experiences (
    id INTEGER PRIMARY KEY,
    action TEXT,
    context TEXT,
    outcome TEXT,
    insight TEXT,
    importance REAL DEFAULT 0.5,
    created_at TIMESTAMP
);

-- 实体关系
CREATE TABLE relations (
    id INTEGER PRIMARY KEY,
    from_entity TEXT,
    relation_type TEXT,
    to_entity TEXT,
    weight REAL DEFAULT 0.5,
    created_at TIMESTAMP
);

-- 记忆强度
CREATE TABLE memory_strength (
    id INTEGER PRIMARY KEY,
    memory_type TEXT,
    memory_id INTEGER,
    base_strength REAL,
    current_strength REAL,
    last_accessed TIMESTAMP
);
```

### 7.3 核心 API

```python
class Memory:
    """MemoryCoreClaw 核心类"""
    
    def remember(self, content: str, importance: float = 0.5, 
                 category: str = None, emotion: str = None) -> int:
        """记住事实"""
        pass
    
    def recall(self, query: str, limit: int = 5) -> List[dict]:
        """语义搜索记忆"""
        pass
    
    def recall_by_category(self, category: str) -> List[dict]:
        """按类别查询"""
        pass
    
    def recall_by_importance(self, min_importance: float = 0.0) -> List[dict]:
        """按重要性查询"""
        pass
    
    def learn(self, action: str, context: str, outcome: str, 
              insight: str, importance: float = 0.5) -> int:
        """学习经验教训"""
        pass
    
    def relate(self, entity1: str, relation: str, entity2: str, 
               weight: float = 0.5) -> int:
        """建立实体关系"""
        pass
    
    def associate(self, entity: str, depth: int = 1) -> dict:
        """获取关联网络"""
        pass
```

---

## 8. 未来展望

### 8.1 短期规划

- [ ] 自动双向同步（MEMORY.md ↔ memory.db）
- [ ] 更多 Embedding 模型支持
- [ ] Web UI 管理界面

### 8.2 长期愿景

- **多 Agent 共享记忆** — 不同 Agent 共享同一记忆库
- **记忆迁移** — 支持导入导出，跨平台使用
- **情感计算** — 更精细的情感关联与回忆触发
- **主动回忆** — 根据上下文主动推送相关记忆

---

## 9. 总结

MemoryCoreClaw 通过模拟人类大脑的记忆机制，实现了 AI Agent 的记忆延续。核心创新点：

1. **分层架构** — 工作记忆 + 长期记忆，快速热启动 + 深度检索
2. **重要性评分** — 区分核心记忆与次要信息
3. **经验学习** — "吃一堑长一智"，避免重复犯错
4. **实体关系** — 知识图谱，支持关联推理
5. **非侵入式** — 兼容现有 AI Agent 框架

**目标：让 AI Agent 不再每次像新认识一样从零开始。**

---

## 附录

### A. 项目信息

- **名称：** MemoryCoreClaw
- **类型：** AI Agent 记忆系统
- **许可：** 开源（MIT License）
- **语言：** Python 3.8+

### B. 参考文献

1. Baddeley, A. (2000). The episodic buffer: a new component of working memory?
2. Miller, G. A. (1956). The magical number seven, plus or minus two
3. Ebbinghaus, H. (1885). Memory: A contribution to experimental psychology

---

*本文档由 MemoryCoreClaw 团队撰写。*