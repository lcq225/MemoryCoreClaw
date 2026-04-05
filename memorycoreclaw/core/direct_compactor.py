# -*- coding: utf-8 -*-
"""
Direct Compactor - 绕过 ReActAgent 直接调用模型进行压缩

解决问题：
- ReMe 的 Compactor 使用 ReActAgent，会注入额外内容干扰模型
- 本模块直接调用模型，避免注入问题
"""
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from agentscope.message import Msg
from agentscope.model import ChatModelBase
from agentscope.formatter import FormatterBase
from agentscope.token import HuggingFaceTokenCounter


# 压缩提示词（包含 OpenClaw 风格的记忆提取）
COMPACTION_SYSTEM_PROMPT = """你是一个专业的上下文压缩助手。你的任务是将对话历史压缩成简洁的摘要，同时提取重要的记忆信息。

## 输出格式要求

请按以下格式输出：

### 一、对话摘要
[用简洁的语言总结对话的核心内容，保留关键信息和决策]

### 二、关键进展
[列出对话中的重要进展和结果]

### 三、待处理事项
[列出对话中提到的待办事项]

### 四、记忆提取
请提取以下类型的信息（如果存在）：

```json
{
  "decisions": [
    {"decision": "做了什么决定", "reason": "决定原因"}
  ],
  "lessons": [
    {"lesson": "学到了什么", "context": "在什么情境下"}
  ],
  "todos": [
    {"task": "待办事项", "priority": "high/medium/low"}
  ],
  "facts": [
    {"fact": "需要记住的事实", "category": "technical/preference/project"}
  ]
}
```

注意：
1. 只提取确实有价值的信息，不要强行提取
2. 如果某类信息不存在，对应数组为空
3. 决策要记录完整（决策+原因）
4. 待办要标注优先级"""

COMPACTION_USER_PROMPT_INITIAL = """请压缩以下对话历史：

{conversation}

请按照系统提示的格式输出压缩结果。"""

COMPACTION_USER_PROMPT_UPDATE = """请压缩以下对话历史，并结合之前的摘要：

{conversation}

## 之前的摘要
{previous_summary}

请按照系统提示的格式输出压缩结果，注意保留之前摘要中的重要信息。"""


class DirectCompactor:
    """直接调用模型的压缩器，绕过 ReActAgent"""
    
    def __init__(
        self,
        model: ChatModelBase,
        formatter: FormatterBase = None,
        token_counter: HuggingFaceTokenCounter = None,
        language: str = "zh",
    ):
        self.model = model
        self.formatter = formatter
        self.token_counter = token_counter
        self.language = language
    
    async def compact(
        self,
        messages: List[Msg],
        previous_summary: str = "",
        max_tokens: int = 4000,
    ) -> Dict[str, Any]:
        """
        执行压缩
        
        Args:
            messages: 对话消息列表
            previous_summary: 之前的摘要
            max_tokens: 最大输出 tokens
            
        Returns:
            {
                "history_compact": "压缩后的文本",
                "memory_extraction": {...},  # 提取的记忆 JSON
                "is_valid": True/False,
            }
        """
        # 1. 格式化对话历史
        conversation_text = self._format_messages(messages)
        
        # 2. 构建提示
        if previous_summary:
            user_prompt = COMPACTION_USER_PROMPT_UPDATE.format(
                conversation=conversation_text,
                previous_summary=previous_summary,
            )
        else:
            user_prompt = COMPACTION_USER_PROMPT_INITIAL.format(
                conversation=conversation_text,
            )
        
        # 3. 构建消息列表（必须使用字典格式，OpenAIChatModel 不支持 Msg 对象）
        msgs = [
            {"role": "system", "content": COMPACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        
        # 4. 调用模型（非流式）
        try:
            # 使用模型的 __call__ 方法，确保非流式
            response = self.model(msgs)
            
            # 如果是协程，await 它
            import asyncio
            if asyncio.iscoroutine(response):
                response = await response
            
            # 处理响应 - 安全获取内容
            content = ""
            
            # 方法1：尝试 get_text_content
            if hasattr(response, 'get_text_content'):
                try:
                    content = response.get_text_content()
                except Exception:
                    pass
            
            # 方法2：直接访问 content 属性
            if not content and hasattr(response, 'content'):
                raw = response.content
                if isinstance(raw, str):
                    content = raw
                elif isinstance(raw, list):
                    # 提取文本块
                    parts = []
                    for item in raw:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            parts.append(item.get('text', ''))
                        elif isinstance(item, str):
                            parts.append(item)
                    content = '\n'.join(parts)
                elif raw is not None:
                    content = str(raw)
            
            # 方法3：直接字符串化
            if not content:
                content = str(response) if response else ""
            
            # 5. 解析记忆提取 JSON
            memory_extraction = self._parse_memory_extraction(content)
            
            # 6. 验证结果
            is_valid = self._is_valid_summary(content)
            
            return {
                "history_compact": content,
                "memory_extraction": memory_extraction,
                "is_valid": is_valid,
            }
            
        except Exception as e:
            print(f"压缩失败: {e}")
            return {
                "history_compact": "",
                "memory_extraction": None,
                "is_valid": False,
                "error": str(e),
            }
    
    def _format_messages(self, messages: List[Msg]) -> str:
        """格式化消息列表为文本"""
        lines = []
        for msg in messages:
            # 安全获取属性
            role = getattr(msg, 'role', 'user') if hasattr(msg, 'role') else 'user'
            name = getattr(msg, 'name', 'unknown') if hasattr(msg, 'name') else 'unknown'
            
            # 获取内容 - 使用更安全的方式
            try:
                content = msg.get_text_content() if hasattr(msg, 'get_text_content') else str(getattr(msg, 'content', ''))
            except Exception:
                content = str(getattr(msg, 'content', ''))
            
            # 添加时间戳（如果有）
            timestamp = ""
            if hasattr(msg, 'timestamp') and msg.timestamp:
                timestamp = f"[{msg.timestamp}]"
            
            lines.append(f"**{name}** ({role}){timestamp}:\n{content}\n")
        
        return '\n---\n'.join(lines)
    
    def _parse_memory_extraction(self, content: str) -> Optional[Dict]:
        """从压缩结果中解析记忆提取 JSON"""
        import re
        
        # 查找 JSON 代码块
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        match = re.search(json_pattern, content)
        
        if not match:
            return None
        
        json_str = match.group(1).strip()
        
        try:
            data = json.loads(json_str)
            
            # 验证结构
            if not isinstance(data, dict):
                return None
            
            # 确保所有必需字段存在
            for key in ["decisions", "lessons", "todos", "facts"]:
                if key not in data:
                    data[key] = []
            
            return data
            
        except json.JSONDecodeError:
            return None
    
    def _is_valid_summary(self, content: str) -> bool:
        """验证摘要是否有效"""
        if not content or not content.strip():
            return False
        
        # 检查是否包含必要的章节
        required_sections = ["摘要", "进展"]
        has_section = any(s in content for s in required_sections)
        
        return has_section


# 便捷函数
async def direct_compact(
    model: ChatModelBase,
    messages: List[Msg],
    previous_summary: str = "",
) -> Dict[str, Any]:
    """
    直接压缩对话
    
    Args:
        model: 模型实例
        messages: 对话消息列表
        previous_summary: 之前的摘要
        
    Returns:
        压缩结果
    """
    compactor = DirectCompactor(model=model)
    return await compactor.compact(messages, previous_summary)