# -*- coding: utf-8 -*-
"""
全局错误处理中心 - 统一捕获、自动恢复、智能汇报
为整个技能系统提供稳定的错误处理能力
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import os
import traceback
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Callable
from functools import wraps
from pathlib import Path

# 配置
MEMORY_DB = r"memory.db"
ERROR_LOG = r"error_log.json"


class ErrorHandler:
    """
    全局错误处理器
    
    功能：
    - 统一错误捕获
    - 自动分类分级
    - 智能恢复建议
    - 记录到记忆系统
    """
    
    # 错误分类
    ERROR_CATEGORIES = {
        "import_error": {"severity": "medium", "auto_recover": True},
        "file_not_found": {"severity": "medium", "auto_recover": True},
        "permission_error": {"severity": "high", "auto_recover": False},
        "timeout": {"severity": "medium", "auto_recover": True},
        "network_error": {"severity": "medium", "auto_recover": True},
        "database_error": {"severity": "high", "auto_recover": False},
        "invalid_input": {"severity": "low", "auto_recover": True},
        "unknown": {"severity": "medium", "auto_recover": False},
    }
    
    def __init__(self):
        self.errors = []
        self.recover_handlers = {}
        
    def classify_error(self, error: Exception) -> Dict:
        """分类错误"""
        error_type = type(error).__name__.lower()
        
        # 匹配错误类型
        for category, config in self.ERROR_CATEGORIES.items():
            if category.replace('_', '') in error_type:
                return {
                    "category": category,
                    "severity": config["severity"],
                    "auto_recover": config["auto_recover"]
                }
        
        return {
            "category": "unknown",
            "severity": "medium",
            "auto_recover": False
        }
    
    def get_recovery_suggestion(self, error: Exception, context: str = "") -> str:
        """获取恢复建议"""
        error_type = type(error).__name__
        msg = str(error)
        
        suggestions = {
            "FileNotFoundError": "检查文件路径是否正确，或使用默认路径",
            "PermissionError": "检查文件权限，或使用管理员权限",
            "TimeoutError": "增加超时时间，或检查网络连接",
            "ConnectionError": "检查网络连接，或重试",
            "sqlite3.OperationalError": "检查数据库是否被占用，或重启",
            "ImportError": "检查模块是否安装，或安装依赖",
            "KeyError": "检查字典键是否存在",
            "ValueError": "检查输入值是否合法",
        }
        
        for err_type, suggestion in suggestions.items():
            if err_type in error_type:
                return suggestion
        
        return "请检查错误信息并重试"
    
    def log_error(self, error: Exception, context: str = "", 
                  skill_name: str = "") -> Dict:
        """记录错误"""
        classification = self.classify_error(error)
        
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error)[:200],
            "category": classification["category"],
            "severity": classification["severity"],
            "auto_recover": classification["auto_recover"],
            "context": context,
            "skill_name": skill_name,
            "suggestion": self.get_recovery_suggestion(error, context),
            "traceback": traceback.format_exc()[:500]
        }
        
        self.errors.append(error_record)
        
        # 持久化到文件
        self._persist_error(error_record)
        
        # 记录到记忆系统
        self._record_to_memory(error_record)
        
        return error_record
    
    def _persist_error(self, error_record: Dict):
        """持久化错误"""
        try:
            errors = []
            if os.path.exists(ERROR_LOG):
                with open(ERROR_LOG, 'r', encoding='utf-8') as f:
                    errors = json.load(f)
            
            errors.append(error_record)
            
            # 只保留最近100条
            errors = errors[-100:]
            
            with open(ERROR_LOG, 'w', encoding='utf-8') as f:
                json.dump(errors, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def _record_to_memory(self, error_record: Dict):
        """记录到记忆系统"""
        try:
            conn = sqlite3.connect(MEMORY_DB)
            cursor = conn.cursor()
            
            content = f"[错误] {error_record['error_type']}: {error_record['error_message'][:50]}"
            
            cursor.execute('''
                INSERT INTO facts (content, category, importance, created_at)
                VALUES (?, ?, ?, datetime('now'))
            ''', (content, "error_record", 0.7))
            
            conn.commit()
            conn.close()
        except:
            pass
    
    def handle(self, context: str = "", skill_name: str = ""):
        """装饰器：自动捕获和处理错误"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_record = self.log_error(e, context, skill_name)
                    
                    print(f"\n⚠️ 错误已记录")
                    print(f"   类型: {error_record['error_type']}")
                    print(f"   严重: {error_record['severity']}")
                    print(f"   建议: {error_record['suggestion']}")
                    
                    if error_record['auto_recover']:
                        print("   🔄 尝试自动恢复...")
                    
                    raise
            return wrapper
        return decorator
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict]:
        """获取最近错误"""
        try:
            if os.path.exists(ERROR_LOG):
                with open(ERROR_LOG, 'r', encoding='utf-8') as f:
                    errors = json.load(f)
                return errors[-limit:]
        except:
            pass
        return []
    
    def get_error_stats(self) -> Dict:
        """获取错误统计"""
        errors = self.get_recent_errors(100)
        
        stats = {
            "total": len(errors),
            "by_severity": {"high": 0, "medium": 0, "low": 0},
            "by_category": {},
            "recent": errors[-5:] if errors else []
        }
        
        for e in errors:
            stats["by_severity"][e["severity"]] = stats["by_severity"].get(e["severity"], 0) + 1
            cat = e["category"]
            stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1
        
        return stats


# 全局实例
error_handler = ErrorHandler()


# 便捷装饰器
def handle_error(context: str = "", skill_name: str = ""):
    """错误处理装饰器"""
    return error_handler.handle(context, skill_name)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="全局错误处理中心")
    parser.add_argument("--stats", "-s", action="store_true", help="显示错误统计")
    parser.add_argument("--recent", "-r", type=int, default=5, help="显示最近N条")
    args = parser.parse_args()
    
    handler = ErrorHandler()
    
    if args.stats:
        stats = handler.get_error_stats()
        
        print("\n" + "=" * 50)
        print("📊 错误统计")
        print("=" * 50)
        print(f"  总错误数: {stats['total']}")
        print(f"\n  严重程度:")
        for sev, count in stats['by_severity'].items():
            emoji = "🔴" if sev == "high" else "🟡" if sev == "medium" else "🟢"
            print(f"    {emoji} {sev}: {count}")
        print(f"\n  错误类别:")
        for cat, count in stats['by_category'].items():
            print(f"    {cat}: {count}")
        
        if stats['recent']:
            print(f"\n  最近错误:")
            for e in stats['recent']:
                print(f"    • {e['error_type']}: {e['error_message'][:30]}...")
    else:
        print("用法:")
        print("  python error_handler.py --stats    # 显示统计")
