"""
MemoryCoreClaw - Contextual Memory Module

Implements context-based memory recall.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import sqlite3


@dataclass
class Context:
    """Memory context"""
    location: Optional[str] = None
    people: List[str] = field(default_factory=list)
    emotion: Optional[str] = None
    activity: Optional[str] = None
    channel: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class ContextualMemory:
    """
    Contextual Memory Engine
    
    Features:
    - Bind memories to contexts
    - Trigger recall by context
    - Score context matches
    
    Usage:
        cm = ContextualMemory()
        ctx = Context(location="office", people=["Alice"])
        cm.bind("fact", 1, ctx)
        results = cm.recall(people=["Alice"])
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_tables()
    
    def _init_tables(self):
        """Initialize context tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 使用与 engine.py 一致的表结构
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contexts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                context_hash TEXT,
                time TEXT,
                time_period TEXT,
                date TEXT,
                weekday TEXT,
                location TEXT,
                location_type TEXT,
                people TEXT,
                emotion TEXT,
                emotion_intensity REAL,
                activity TEXT,
                topic TEXT,
                weather TEXT,
                environment TEXT,
                channel TEXT,
                session_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_context_bindings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_type TEXT NOT NULL,
                memory_id INTEGER NOT NULL,
                context_id INTEGER NOT NULL,
                binding_strength REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_context(self, context: Context) -> int:
        """Create a context record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        import json
        cursor.execute('''
            INSERT INTO contexts (location, people, emotion, activity, channel)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            context.location,
            json.dumps(context.people) if context.people else None,
            context.emotion,
            context.activity,
            context.channel
        ))
        
        context_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return context_id
    
    def bind_memory(self, memory_type: str, memory_id: int, context: Context) -> int:
        """Bind a memory to a context"""
        context_id = self.create_context(context)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO memory_context_bindings (memory_type, memory_id, context_id)
            VALUES (?, ?, ?)
        ''', (memory_type, memory_id, context_id))
        
        binding_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return binding_id
    
    def recall_by_context(
        self,
        location: str = None,
        people: List[str] = None,
        emotion: str = None,
        activity: str = None
    ) -> List[Dict]:
        """Recall memories matching context"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        import json
        
        # 构建查询条件
        conditions = []
        params = []
        
        if location:
            conditions.append("c.location = ?")
            params.append(location)
        
        if people:
            # 使用 LIKE 查询 JSON 数组中的元素
            for person in people:
                conditions.append("c.people LIKE ?")
                params.append(f'%{person}%')
        
        if emotion:
            conditions.append("c.emotion = ?")
            params.append(emotion)
        
        if activity:
            conditions.append("c.activity = ?")
            params.append(activity)
        
        if not conditions:
            conn.close()
            return []
        
        # 查询匹配的记忆
        query = f'''
            SELECT DISTINCT mcb.memory_type, mcb.memory_id
            FROM memory_context_bindings mcb
            JOIN contexts c ON mcb.context_id = c.id
            WHERE {' AND '.join(conditions)}
        '''
        
        cursor.execute(query, params)
        bindings = cursor.fetchall()
        
        results = []
        for memory_type, memory_id in bindings:
            # 根据类型获取记忆内容
            if memory_type == 'fact':
                cursor.execute('SELECT * FROM facts WHERE id = ?', (memory_id,))
                row = cursor.fetchone()
                if row:
                    results.append({
                        'type': 'fact',
                        'id': row[0],
                        'content': row[1],
                        'importance': row[3],
                        'category': row[5]
                    })
            elif memory_type == 'experience':
                cursor.execute('SELECT * FROM experiences WHERE id = ?', (memory_id,))
                row = cursor.fetchone()
                if row:
                    results.append({
                        'type': 'experience',
                        'id': row[0],
                        'action': row[1],
                        'context': row[2],
                        'outcome': row[3],
                        'insight': row[4]
                    })
        
        conn.close()
        return results
    
    def score_match(self, query_context: Context, memory_context: Context) -> float:
        """
        Score how well two contexts match.
        
        Args:
            query_context: The search context
            memory_context: The memory's context
            
        Returns:
            Match score (0-1)
        """
        score = 0.0
        total = 0
        
        # Location match
        if query_context.location or memory_context.location:
            total += 1
            if query_context.location == memory_context.location:
                score += 1
        
        # People match (overlap ratio)
        if query_context.people or memory_context.people:
            total += 1
            query_people = set(query_context.people or [])
            memory_people = set(memory_context.people or [])
            if query_people and memory_people:
                overlap = len(query_people & memory_people)
                union = len(query_people | memory_people)
                score += overlap / union if union > 0 else 0
        
        # Emotion match
        if query_context.emotion or memory_context.emotion:
            total += 1
            if query_context.emotion == memory_context.emotion:
                score += 1
        
        # Activity match
        if query_context.activity or memory_context.activity:
            total += 1
            if query_context.activity == memory_context.activity:
                score += 1
        
        return score / total if total > 0 else 0.5