# MemoryCoreClaw：类人脑长期记忆引擎设计思路

> 本文记录 MemoryCoreClaw 项目的设计理念、核心思路与实现方案

**创建时间：** 2026-03-19  
**项目地址：** https://github.com/lcq225/MemoryCoreClaw

---

## 一、为什么需要这个项目？

### 问题背景

在使用 AI Agent（如 ChatGPT、Claude、CoPaw）的过程中，我发现一个核心痛点：

> **AI 没有长期记忆，每次对话都是"新"的。**

具体表现：

| 场景 | 问题 |
|------|------|
| 用户偏好 | 每次都要重新告诉 AI 我的偏好、工作背景 |
| 历史对话 | AI 无法记住上周聊过什么、做过什么决策 |
| 知识积累 | 每次对话的知识无法沉淀，没有"成长" |
| 上下文限制 | 对话一长，早期内容就被"遗忘" |

### 现有方案的局限

| 方案 | 优点 | 局限 |
|------|------|------|
| 对话历史 | 简单 | 上下文窗口有限，成本高 |
| RAG 检索 | 可检索大量文档 | 不是真正的"记忆"，没有强度衰减 |
| 向量数据库 | 语义搜索能力强 | 没有分层、没有遗忘机制 |
| 简单 KV 存储 | 轻量 | 无结构、无关联、无衰减 |

### 我的思路

**为什么不模拟人类大脑的记忆机制？**

人类记忆有几个关键特性：

1. **分层记忆** - 有些事永远不忘（核心记忆），有些事逐渐模糊
2. **遗忘曲线** - Ebbinghaus 发现记忆强度随时间衰减
3. **情境触发** - "上次在咖啡馆聊的那个项目..." 能唤起记忆
4. **工作记忆** - 短期暂存，容量有限（7±2）
5. **关联记忆** - 提到 Alice 就联想到她工作的公司、她的技能

**MemoryCoreClaw 就是实现这些特性的记忆引擎。**

---

## 二、核心设计

### 2.1 分层记忆系统

**设计理念：** 不是所有记忆都同等重要，应该有不同的重要级别和保留策略。

```
┌─────────────────────────────────────────────────────┐
│  核心层 (Core)      importance ≥ 0.9               │
│  - 永久保留，注入每次对话上下文                      │
│  - 例：用户姓名、公司、关键偏好                      │
├─────────────────────────────────────────────────────┤
│  重要层 (Important) 0.7 ≤ importance < 0.9         │
│  - 长期保留，定期巩固                               │
│  - 例：重要项目信息、关键决策                        │
├─────────────────────────────────────────────────────┤
│  普通层 (Normal)     0.5 ≤ importance < 0.7         │
│  - 正常保留，可能整合                                │
│  - 例：日常对话、一般信息                            │
├─────────────────────────────────────────────────────┤
│  次要层 (Minor)      importance < 0.5               │
│  - 可能衰减删除                                      │
│  - 例：临时信息、琐碎细节                            │
└─────────────────────────────────────────────────────┘
```

**代码实现：**

```python
class MemoryLayer(Enum):
    CORE = 0.9       # 永久保留
    IMPORTANT = 0.7  # 长期保留
    NORMAL = 0.5     # 正常保留
    MINOR = 0.3      # 可能衰减
```

### 2.2 遗忘曲线

**设计理念：** 记忆不是永久的，会随时间衰减，但访问可以增强。

**Ebbinghaus 公式：**

```
R = e^(-t/S)

R = 记忆保持率
t = 距上次访问的时间（天）
S = 记忆强度（与重要性相关）
```

**效果：**

```
重要性 0.9 的记忆：30 天后保持率约 74%
重要性 0.5 的记忆：30 天后保持率约 52%
重要性 0.3 的记忆：30 天后保持率约 26%
```

**访问增强机制：**

每次访问记忆时，记忆强度增加：

```python
def access_memory(memory_id):
    memory.access_count += 1
    memory.last_accessed = now()
    memory.strength *= 1.1  # 增强 10%
```

### 2.3 情境记忆

**设计理念：** 记忆与情境绑定，情境可以触发相关记忆。

**情境维度：**

```python
@dataclass
class Context:
    location: str      # 地点：办公室、咖啡馆、家里
    people: List[str]  # 人物：Alice、Bob
    emotion: str       # 情绪：开心、沮丧
    activity: str      # 活动：开会、写代码、吃饭
    channel: str       # 渠道：微信、邮件、面对面
    timestamp: datetime
```

**使用场景：**

```python
# 记住一个带情境的记忆
mem.remember(
    "讨论了 Q2 预算方案",
    importance=0.8,
    context=Context(
        location="会议室A",
        people=["Alice", "Bob"],
        activity="meeting"
    )
)

# 后来通过情境触发
mem.recall_by_context(people=["Alice"])
# 返回：与 Alice 相关的所有记忆
```

### 2.4 工作记忆

**设计理念：** 人类短期记忆容量有限（7±2），AI 也应该有类似的限制。

```python
class WorkingMemory:
    capacity = 9  # 7±2 模型
    
    def hold(self, key, value, priority=0.5, ttl=None):
        """暂存信息"""
        if len(self.items) >= self.capacity:
            self._evict_lowest_priority()
        self.items[key] = WorkingItem(key, value, priority, ttl)
    
    def retrieve(self, key):
        """取出信息"""
        return self.items.get(key)
```

**使用场景：**

```python
# 暂存当前任务
mem.hold("current_task", "写 MemoryCoreClaw 文档", priority=0.9)
mem.hold("pending_review", ["PR#123", "PR#456"], priority=0.7)

# 取出
task = mem.retrieve("current_task")
```

### 2.5 关系学习

**设计理念：** 实体之间的关系是知识的重要组成部分。

**标准关系类型（28种）：**

```python
STANDARD_RELATIONS = {
    # 工作
    'works_at', 'manages', 'collaborates_with', 'reports_to',
    # 知识
    'knows', 'learned', 'teaches',
    # 使用
    'uses', 'depends_on', 'implements',
    # 偏好
    'prefers', 'likes', 'dislikes',
    # 社交
    'friend_of', 'colleague_of',
    # 位置
    'located_in', 'part_of',
    # ...
}
```

**使用方式：**

```python
# 建立关系
mem.relate("Alice", "works_at", "TechCorp")
mem.relate("Alice", "knows", "Bob")
mem.relate("Bob", "manages", "Carol")

# 查询关系网络
network = mem.associate("Alice", depth=2)
# 返回：Alice 的 2 层关系网络
```

---

## 三、技术架构

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    Memory API                           │
│  remember() / recall() / learn() / relate()             │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                   Memory Engine                         │
│  统一接口层，协调各模块                                   │
└─────────────────────────────────────────────────────────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
┌───▼───┐  ┌───────────┐  ┌───▼───┐  ┌───────────┐
│ Core  │  │ Cognitive │  │Retrieval│ │  Storage  │
│Engine │  │  Modules  │  │ Modules │ │  Modules  │
└───────┘  └───────────┘  └─────────┘ └───────────┘
    │            │              │            │
    │      ┌─────┴─────┐        │      ┌─────┴─────┐
    │      │           │        │      │           │
    │  Forgetting  Working    Semantic  Database
    │    Curve      Memory    Search    (SQLite)
    │                               │
    │                          Contextual
    │                           Memory
    │
    └─── Facts / Lessons / Relations / Entities ───┘
```

### 3.2 数据模型

```sql
-- 事实记忆
CREATE TABLE facts (
    id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    importance REAL DEFAULT 0.5,
    category TEXT DEFAULT 'general',
    emotion TEXT DEFAULT 'neutral',
    tags TEXT,
    created_at TIMESTAMP,
    last_accessed TIMESTAMP,
    access_count INTEGER DEFAULT 0
);

-- 经验教训
CREATE TABLE experiences (
    id INTEGER PRIMARY KEY,
    action TEXT NOT NULL,      -- 做了什么
    context TEXT,              -- 什么情境
    outcome TEXT,              -- 结果如何
    insight TEXT NOT NULL,     -- 学到了什么
    importance REAL DEFAULT 0.5
);

-- 实体关系
CREATE TABLE relations (
    id INTEGER PRIMARY KEY,
    from_entity TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    to_entity TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    evidence TEXT
);

-- 工作记忆
CREATE TABLE working_memory (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    key TEXT NOT NULL,
    value TEXT,
    priority REAL DEFAULT 0.5,
    expires_at TIMESTAMP,
    UNIQUE(session_id, key)
);
```

---

## 四、使用示例

### 4.1 基础使用

```python
from memorycoreclaw import Memory

mem = Memory()

# 记住事实
mem.remember("Alice 在 Acme Corp 工作", importance=0.9)
mem.remember("Alice 喜欢简洁的沟通风格", importance=0.8, category="preference")

# 召回记忆
results = mem.recall("Alice")
# 返回所有与 Alice 相关的记忆

# 学习经验
mem.learn(
    action="未备份直接修改配置",
    context="系统升级",
    outcome="negative",
    insight="修改前必须备份",
    importance=0.9
)

# 建立关系
mem.relate("Alice", "works_at", "Acme Corp")
mem.relate("Acme Corp", "located_in", "Beijing")
```

### 4.2 与 AI Agent 集成

```python
class AgentWithMemory:
    def __init__(self):
        self.memory = Memory()
    
    def chat(self, user_input):
        # 1. 召回相关记忆
        context = self.memory.recall(user_input, limit=5)
        
        # 2. 构建增强提示词
        enhanced_prompt = f"""
历史记忆：
{format_memories(context)}

用户问题：{user_input}
"""
        # 3. 调用 LLM
        response = self.llm.generate(enhanced_prompt)
        
        # 4. 记住这次对话
        self.memory.remember(f"用户问：{user_input}", importance=0.5)
        self.memory.remember(f"AI答：{response}", importance=0.5)
        
        return response
```

---

## 五、设计决策记录

### 决策 1：为什么用 SQLite？

| 选项 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| SQLite | 轻量、无依赖、单文件 | 不支持高并发写 | ✅ 选择 |
| PostgreSQL | 功能强大、高并发 | 需要部署服务 | ❌ 过重 |
| MongoDB | 灵活 Schema | 无 SQL 查询 | ❌ 不适合 |

**理由：** AI Agent 通常是单用户或中等并发，SQLite 足够。单文件便于备份和迁移。

### 决策 2：为什么不默认启用语义搜索？

| 考量 | 说明 |
|------|------|
| 依赖 | 语义搜索需要嵌入模型（如 sentence-transformers） |
| 资源 | 模型占用内存和计算资源 |
| 简单场景 | 关键词搜索已足够 |

**决策：** 语义搜索作为可选功能，默认关闭，用户可按需启用。

### 决策 3：为什么用 0-1 的重要性范围？

- 直观：0.9 就是 90% 重要
- 灵活：可随时调整阈值
- 可计算：直接用于遗忘曲线公式

---

## 六、后续规划

### 短期

- [ ] 支持更多数据库后端（PostgreSQL、MySQL）
- [ ] 完善语义搜索功能
- [ ] 添加记忆去重机制

### 中期

- [ ] 记忆自动摘要和整合
- [ ] 多用户隔离支持
- [ ] Web UI 管理界面

### 长期

- [ ] 分布式存储支持
- [ ] 记忆共享和同步
- [ ] 与主流 AI Agent 框架深度集成

---

## 七、总结

MemoryCoreClaw 是我对"AI 需要什么样的记忆系统"的思考和实现：

1. **分层记忆** - 不是所有信息都同等重要
2. **遗忘机制** - 记忆会衰减，访问会增强
3. **情境触发** - 记忆与情境绑定
4. **工作记忆** - 短期暂存，容量有限
5. **关系学习** - 实体之间的知识关联

这不是一个简单的存储系统，而是模拟人类认知的记忆引擎。

---

**项目地址：** https://github.com/lcq225/MemoryCoreClaw

**文档：**
- [入门指南](https://github.com/lcq225/MemoryCoreClaw/blob/main/docs/GETTING_STARTED.md)
- [API 参考](https://github.com/lcq225/MemoryCoreClaw/blob/main/docs/API.md)
- [架构设计](https://github.com/lcq225/MemoryCoreClaw/blob/main/docs/ARCHITECTURE.md)
- [部署文档](https://github.com/lcq225/MemoryCoreClaw/blob/main/docs/DEPLOYMENT.md)