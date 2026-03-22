# MemoryCoreClaw 设计理念

> 让 AI Agent 拥有类人脑的长期记忆能力

---

## 🎯 设计目标

MemoryCoreClaw 的核心目标是解决 AI Agent 的"记忆缺失"问题：

| 传统 AI | MemoryCoreClaw |
|---------|----------------|
| 对话上下文有限（通常 4K-128K tokens） | 永久记忆存储 |
| 每次对话从零开始 | 自动召回相关记忆 |
| 无法积累知识 | 知识图谱持续增长 |
| 无法记住用户偏好 | 长期记住并关联用户信息 |

---

## 🧠 认知科学基础

MemoryCoreClaw 的设计灵感来源于认知科学和神经科学的核心概念：

### 1. 分层记忆模型

人类记忆不是单一的存储系统，而是分层的：

```
┌─────────────────────────────────────────────────────────────┐
│                     记忆层次模型                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   核心层 (Core Layer)                                       │
│   ├── 重要性 ≥ 0.9                                          │
│   ├── 永久保留，不衰减                                       │
│   ├── 自动注入到每次对话上下文                               │
│   └── 示例：用户身份、核心偏好、关键配置                     │
│                                                             │
│   重要层 (Important Layer)                                  │
│   ├── 重要性 0.7-0.9                                        │
│   ├── 长期保留，缓慢衰减                                     │
│   └── 示例：重要项目信息、用户习惯                           │
│                                                             │
│   普通层 (Normal Layer)                                     │
│   ├── 重要性 0.5-0.7                                        │
│   ├── 正常保留，定期整合                                     │
│   └── 示例：日常对话、一般信息                               │
│                                                             │
│   次要层 (Minor Layer)                                      │
│   ├── 重要性 < 0.5                                          │
│   ├── 可能衰减，可被清理                                     │
│   └── 示例：临时信息、低价值内容                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**设计理念：** 并非所有信息都同等重要。分层存储让系统更高效，核心信息永远在线，次要信息按需清理。

### 2. Ebbinghaus 遗忘曲线

德国心理学家 Hermann Ebbinghaus 发现，记忆会随时间衰减：

```
记忆强度
    │
1.0 ┤■■■■■■■
    │        ■■■■
    │            ■■■
    │                ■■
    │                  ■
0.5 ┤                    ■■
    │                       ■
    │                         ■
    │                           ■
0.0 ┤                             ■■■■■■
    └──────────────────────────────────────▶ 时间
       1天  2天  3天  4天  5天  6天  7天
```

**MemoryCoreClaw 实现：**

```python
# 记忆强度随时间衰减
strength = base_strength * exp(-decay_rate * days_since_access)

# 访问可增强记忆（重置衰减）
def access_memory(memory_id):
    memory.access_count += 1
    memory.last_accessed = now()
    memory.current_strength = min(1.0, memory.base_strength * (1.1 ** access_count))
```

**设计理念：** 不常用的记忆逐渐淡忘，经常访问的记忆更加牢固——就像人脑一样。

### 3. 情境记忆 (Contextual Memory)

人类记忆往往与特定情境绑定：

- "上次在咖啡馆，我们讨论了项目方案"
- "我和 Alice 在北京出差时解决了那个 bug"

**MemoryCoreClaw 实现：**

```python
# 情境维度
@dataclass
class Context:
    location: Optional[str]     # 地点
    people: List[str]           # 人物
    emotion: Optional[str]      # 情绪
    activity: Optional[str]     # 活动
    channel: Optional[str]      # 渠道（如微信、邮件）
    timestamp: datetime         # 时间

# 情境触发
def recall_by_context(people=None, location=None, emotion=None):
    """按情境召回记忆"""
    ...
```

**设计理念：** 记忆不是孤立的数据点，而是与情境紧密关联的。情境检索让记忆更"人性化"。

### 4. 工作记忆 (Working Memory)

认知科学家 George Miller 提出，人类工作记忆容量约为 7±2 个单位。

**MemoryCoreClaw 实现：**

```python
class WorkingMemory:
    """容量有限的工作记忆"""
    CAPACITY = 9  # 7 ± 2
    
    def hold(self, key: str, value: Any, priority: float = 0.5):
        """暂存信息，超出容量时驱逐低优先级项"""
        if len(self.items) >= self.CAPACITY:
            self._evict_lowest_priority()
        self.items[key] = WorkingMemoryItem(key, value, priority)
    
    def retrieve(self, key: str) -> Optional[Any]:
        """取出信息"""
        ...
```

**设计理念：** 工作记忆是临时存储，用于保存当前任务相关的信息。容量限制迫使系统聚焦于最重要的信息。

---

## 🏗️ 架构设计

### 模块划分

```
┌─────────────────────────────────────────────────────────────┐
│                    MemoryCoreClaw 架构                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│   │   Memory    │  │ SafeMemory  │  │   Memory    │        │
│   │  (基础接口) │  │ (安全接口)  │  │  Engine     │        │
│   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│          │                │                │                │
│          └────────────────┼────────────────┘                │
│                           │                                 │
│   ┌───────────────────────┼───────────────────────┐         │
│   │                       │                       │         │
│   ▼           ▼           ▼           ▼           ▼         │
│ ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐           │
│ │认知 │   │检索 │   │存储 │   │工具 │   │脚本 │           │
│ │模块 │   │模块 │   │模块 │   │模块 │   │目录 │           │
│ └──┬──┘   └──┬──┘   └──┬──┘   └──┬──┘   └──┬──┘           │
│    │         │         │         │         │                │
│    ▼         ▼         ▼         ▼         ▼                │
│ • 遗忘曲线  • 语义搜索 • SQLite  • 导出    • 检查脚本       │
│ • 情境记忆  • 本体论   • 加密    • 可视化  • 优化脚本       │
│ • 工作记忆  • 关系推理 • 多模态  • GitHub  • 同步脚本       │
│ • 启发推理                      API                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 核心流程

```
┌─────────────────────────────────────────────────────────────┐
│                    记忆存储流程                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   用户输入                                                  │
│      │                                                      │
│      ▼                                                      │
│   ┌──────────────┐                                         │
│   │ 内容解析     │ ← 提取关键信息、识别实体                │
│   └──────┬───────┘                                         │
│          │                                                  │
│          ▼                                                  │
│   ┌──────────────┐                                         │
│   │ 重要性评估   │ ← 自动评分 + 用户指定                   │
│   └──────┬───────┘                                         │
│          │                                                  │
│          ▼                                                  │
│   ┌──────────────┐                                         │
│   │ 分层分配     │ ← 核心/重要/普通/次要                   │
│   └──────┬───────┘                                         │
│          │                                                  │
│          ▼                                                  │
│   ┌──────────────┐                                         │
│   │ 情境绑定     │ ← 关联人物、地点、时间                  │
│   └──────┬───────┘                                         │
│          │                                                  │
│          ▼                                                  │
│   ┌──────────────┐                                         │
│   │ 向量编码     │ ← 可选：语义向量生成                    │
│   └──────┬───────┘                                         │
│          │                                                  │
│          ▼                                                  │
│   ┌──────────────┐                                         │
│   │ 持久化存储   │ ← SQLite 数据库                         │
│   └──────────────┘                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    记忆召回流程                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   查询请求                                                  │
│      │                                                      │
│      ▼                                                      │
│   ┌──────────────┐                                         │
│   │ 查询理解     │ ← 解析查询意图                          │
│   └──────┬───────┘                                         │
│          │                                                  │
│          ▼                                                  │
│   ┌──────────────┐                                         │
│   │ 多路召回     │                                         │
│   │              │                                         │
│   │ ├─ 关键词    │ ← 快速匹配                              │
│   │ ├─ 语义      │ ← 向量相似度（可选）                    │
│   │ ├─ 情境      │ ← 人物/地点触发                         │
│   │ └─ 关系      │ ← 关联实体查询                          │
│   └──────┬───────┘                                         │
│          │                                                  │
│          ▼                                                  │
│   ┌──────────────┐                                         │
│   │ 融合排序     │ ← 综合相关性 + 重要性 + 时间衰减        │
│   └──────┬───────┘                                         │
│          │                                                  │
│          ▼                                                  │
│   ┌──────────────┐                                         │
│   │ 访问增强     │ ← 更新记忆强度                          │
│   └──────┬───────┘                                         │
│          │                                                  │
│          ▼                                                  │
│   返回结果                                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔒 安全设计（v2.1.0 新增）

### 为什么需要安全设计？

在生产环境中，记忆系统面临多种风险：

| 风险 | 描述 | 解决方案 |
|------|------|---------|
| 误删核心记忆 | 用户误操作删除重要信息 | 核心记忆保护 |
| 参数边界问题 | 无效参数导致异常 | 自动边界检查 |
| 数据库连接泄漏 | 连接未正确关闭 | 连接管理器 |
| 数据不一致 | 操作中断导致不一致 | 事务保护 |
| 来源不可追溯 | 不知道记忆来源 | 来源标记 |

### SafeMemory 接口

```python
class SafeMemory:
    """安全的记忆接口"""
    
    # 1. 连接管理
    def __init__(self, db_path: str):
        self._engine = MemoryEngine(db_path)
        # 使用连接池，确保连接正确关闭
    
    # 2. 边界检查
    def recall(self, query: str, limit: int = 10) -> List[Dict]:
        """带边界检查的召回"""
        if limit is None or limit < 0:
            limit = 10  # 自动修正
        return self._engine.recall(query, limit)
    
    # 3. 核心记忆保护
    def delete(self, memory_id: int, force: bool = False) -> Dict:
        """带保护的删除"""
        memory = self._get_memory(memory_id)
        if memory.importance >= 0.9 and not force:
            return {
                "success": False,
                "warning": "核心记忆需要 force=True 才能删除",
                "memory": memory
            }
        return self._engine.delete(memory_id)
    
    # 4. 来源标记
    def remember(self, content: str, importance: float = 0.5,
                 source: str = "user", source_confidence: float = 1.0, **kwargs):
        """带来源标记的记忆存储"""
        return self._engine.remember(
            content,
            importance=importance,
            source=source,
            source_confidence=source_confidence,
            **kwargs
        )
```

### 来源追踪

```python
# 记忆来源类型
class SourceType(Enum):
    USER = "user"        # 用户提供
    LLM = "llm"          # AI 生成
    DOCUMENT = "document"  # 文档提取
    SYSTEM = "system"    # 系统生成

# 来源置信度
# 1.0 = 完全确定
# 0.5-0.9 = 部分确定
# < 0.5 = 不确定

# 示例
mem.remember(
    "项目截止日期是3月30日",
    importance=0.8,
    source="user",
    source_confidence=1.0  # 用户明确告知，完全确定
)

mem.remember(
    "用户可能喜欢咖啡",
    importance=0.5,
    source="llm",
    source_confidence=0.6  # AI 推断，部分确定
)
```

---

## 📊 数据模型

### 核心表结构

```sql
-- 事实记忆表
CREATE TABLE facts (
    id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    importance REAL DEFAULT 0.5,
    category TEXT DEFAULT 'general',
    emotion TEXT DEFAULT 'neutral',
    tags TEXT,  -- JSON array
    source TEXT DEFAULT 'user',
    source_confidence REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP,
    access_count INTEGER DEFAULT 0
);

-- 经验教训表
CREATE TABLE experiences (
    id INTEGER PRIMARY KEY,
    action TEXT NOT NULL,
    context TEXT,
    outcome TEXT DEFAULT 'neutral',
    insight TEXT NOT NULL,
    importance REAL DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 实体关系表
CREATE TABLE relations (
    id INTEGER PRIMARY KEY,
    from_entity TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    to_entity TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 实体定义表
CREATE TABLE entities (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    entity_type TEXT,
    importance REAL DEFAULT 0.5,
    access_count INTEGER DEFAULT 0
);

-- 记忆强度表
CREATE TABLE memory_strength (
    id INTEGER PRIMARY KEY,
    memory_type TEXT NOT NULL,  -- 'fact' or 'experience'
    memory_id INTEGER NOT NULL,
    base_strength REAL DEFAULT 0.5,
    current_strength REAL,
    last_calculated TIMESTAMP
);

-- 情境表
CREATE TABLE contexts (
    id INTEGER PRIMARY KEY,
    location TEXT,
    people TEXT,  -- JSON array
    emotion TEXT,
    activity TEXT,
    channel TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 工作记忆表
CREATE TABLE working_memory (
    id INTEGER PRIMARY KEY,
    session_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT,
    priority REAL DEFAULT 0.5,
    ttl_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔄 版本演进

### v1.0.0 - 基础记忆引擎
- 核心记忆存储和检索
- 分层记忆模型
- 遗忘曲线
- 情境记忆
- 工作记忆
- 关系网络

### v2.0.0 - 可视化增强
- D3.js 交互式知识图谱
- 统计报告
- 记忆浏览器
- 环境变量支持

### v2.1.0 - 安全与维护
- **SafeMemory 安全接口**
- **来源标记与追踪**
- **健康检查脚本**
- **数据库优化工具**
- **GitHub API 集成**

---

## 🚀 未来规划

### v2.2.0 计划
- 多模态记忆（图片、音频）
- 记忆压缩（相似记忆合并）
- 联想推理（A→B→C 推理）

### v3.0.0 愿景
- 分布式记忆存储
- 联邦学习支持
- 跨 Agent 记忆共享

---

**MemoryCoreClaw** - 让 AI Agent 拥有记忆 🧠