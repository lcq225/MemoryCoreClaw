"""
初始化记忆数据库示例脚本

使用方法：
    python scripts/init_memory.py

自定义配置：
    设置环境变量 MEMORY_DB_PATH 指定数据库路径
"""

import sys
import os
import io

# 修复 Windows GBK 编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加模块路径
skill_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(skill_dir))

from memorycoreclaw import Memory

# 数据库路径（支持环境变量）
DB_PATH = os.environ.get('MEMORY_DB_PATH', 'memory.db')


def init_database():
    """初始化数据库并写入示例数据"""
    
    print("=" * 60)
    print("MemoryCoreClaw 数据库初始化")
    print("=" * 60)
    print(f"\n数据库路径: {DB_PATH}\n")
    
    # 创建 Memory 实例（会自动创建数据库和表）
    mem = Memory(db_path=DB_PATH)
    
    print("✅ 数据库创建成功\n")
    
    # ========== 1. 用户核心信息示例 ==========
    print("📝 写入用户核心信息示例...")
    
    user_facts = [
        ("用户名字是 [用户名]", 0.95, "identity"),
        ("用户公司在 [公司名称]", 0.95, "identity"),
        ("用户部门是 [部门名称]", 0.85, "identity"),
        ("用户职业是 [职业描述]", 0.85, "identity"),
        ("用户偏好专业、高效的工作方式", 0.8, "preference"),
        ("用户沟通风格是 BLUF（结论先行）", 0.85, "preference"),
    ]
    
    for content, importance, category in user_facts:
        mem.remember(content, importance=importance, category=category)
    
    print(f"   写入 {len(user_facts)} 条用户信息")
    
    # ========== 2. 本地环境配置示例 ==========
    print("📝 写入本地环境配置示例...")
    
    env_facts = [
        ("操作系统是 Windows 11", 0.7, "environment"),
        ("用户目录是 C:\\Users\\[用户名]", 0.8, "environment"),
        ("文档库路径是 [文档路径]", 0.9, "environment"),
        ("Python 版本是 3.11", 0.6, "environment"),
        ("Node.js 版本是 v20.x", 0.6, "environment"),
    ]
    
    for content, importance, category in env_facts:
        mem.remember(content, importance=importance, category=category)
    
    print(f"   写入 {len(env_facts)} 条环境配置")
    
    # ========== 3. 教训示例 ==========
    print("📝 写入经验教训示例...")
    
    lessons = [
        ("修改关键配置前必须备份", "修改配置文件时", "positive", "出问题可快速回滚", 0.85),
        ("敏感信息严禁对外泄露", "提交 Issue/PR 时", "positive", "Token、密码等必须脱敏", 0.95),
        ("权限检查必须在执行前完成", "收到操作请求时", "positive", "避免未授权操作", 0.9),
        ("临时文件用完必须删除", "使用临时目录时", "positive", "保持工作区整洁", 0.75),
    ]
    
    for action, context, outcome, insight, importance in lessons:
        mem.learn(action, context, outcome, insight, importance=importance)
    
    print(f"   写入 {len(lessons)} 条教训")
    
    # ========== 4. 关系示例 ==========
    print("📝 写入实体关系示例...")
    
    relations = [
        ("[用户名]", "works_at", "[公司名称]"),
        ("[公司名称]", "located_in", "[城市]"),
        ("MemoryCoreClaw", "developed_by", "[作者]"),
        ("MemoryCoreClaw", "github", "https://github.com/lcq225/MemoryCoreClaw"),
    ]
    
    for from_entity, relation, to_entity in relations:
        mem.relate(from_entity, relation, to_entity)
    
    print(f"   写入 {len(relations)} 条关系")
    
    # ========== 5. 项目信息 ==========
    print("📝 写入项目信息...")
    
    project_facts = [
        ("MemoryCoreClaw 是类人脑长期记忆引擎项目", 0.8, "project"),
        ("MemoryCoreClaw 仓库地址是 https://github.com/lcq225/MemoryCoreClaw", 0.85, "project"),
        ("MemoryCoreClaw 支持分层记忆、遗忘曲线、情境记忆", 0.8, "project"),
    ]
    
    for content, importance, category in project_facts:
        mem.remember(content, importance=importance, category=category)
    
    print(f"   写入 {len(project_facts)} 条项目信息")
    
    # ========== 统计 ==========
    print("\n" + "=" * 60)
    print("📊 数据库统计")
    print("=" * 60)
    
    stats = mem.get_stats()
    print(f"""
📝 事实记忆：{stats['facts']} 条
📚 经验教训：{stats['experiences']} 条
🔗 实体关系：{stats['relations']} 条
👤 实体数量：{stats['entities']} 条
💼 工作记忆：{stats['working_memory']} 条
""")
    
    print("=" * 60)
    print("✅ 初始化完成！")
    print("=" * 60)
    
    return mem


if __name__ == "__main__":
    init_database()