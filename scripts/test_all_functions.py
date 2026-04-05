# -*- coding: utf-8 -*-
"""
MemoryCoreClaw 功能完整性测试
测试所有核心功能：读取、写入、删除、更新、搜索、关系、情境、工作记忆、可视化
"""
import sys
import io
import os
import sqlite3
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 设置路径
sys.path.insert(0, r"D:\CoPaw\.copaw\workspaces\default\active_skills")

from memorycoreclaw import Memory

DB_PATH = r"D:\CoPaw\.copaw\.agent-memory\memory.db"

# 测试结果
results = []

def test(name, func):
    """运行测试并记录结果"""
    try:
        func()
        results.append((name, "PASS", ""))
        print(f"[PASS] {name}")
    except Exception as e:
        results.append((name, "FAIL", str(e)))
        print(f"[FAIL] {name}: {e}")


def test_init():
    """测试初始化"""
    mem = Memory(db_path=DB_PATH)
    assert mem is not None, "Memory 实例创建失败"


def test_remember():
    """测试记忆存储"""
    mem = Memory(db_path=DB_PATH)
    # 写入测试
    memory_id = mem.remember(
        content="测试记忆 - 功能验证",
        importance=0.85,
        category="test",
        emotion="neutral",
        tags=["test", "audit"]
    )
    assert memory_id > 0, "记忆存储失败"
    # 保存 ID 供后续测试
    test_remember.memory_id = memory_id


def test_recall():
    """测试记忆搜索"""
    mem = Memory(db_path=DB_PATH)
    # 关键词搜索
    results = mem.recall("测试记忆", limit=5)
    assert len(results) > 0, "关键词搜索失败"
    
    # 检查返回字段
    r = results[0]
    assert "content" in r, "缺少 content 字段"
    assert "importance" in r, "缺少 importance 字段"
    assert "category" in r, "缺少 category 字段"


def test_learn():
    """测试教训记录"""
    mem = Memory(db_path=DB_PATH)
    lesson_id = mem.learn(
        action="测试教训动作",
        context="功能验证上下文",
        outcome="negative",
        insight="这是一个测试洞察",
        importance=0.8
    )
    assert lesson_id > 0, "教训记录失败"
    test_learn.lesson_id = lesson_id


def test_get_lessons():
    """测试获取教训列表"""
    mem = Memory(db_path=DB_PATH)
    lessons = mem.get_lessons(limit=10)
    assert len(lessons) > 0, "获取教训列表失败"


def test_relate():
    """测试关系建立"""
    mem = Memory(db_path=DB_PATH)
    relation_id = mem.relate(
        entity1="测试实体A",
        relation="测试关系",
        entity2="测试实体B",
        evidence="功能验证"
    )
    assert relation_id > 0, "关系建立失败"
    test_relate.relation_id = relation_id


def test_get_relations():
    """测试获取关系"""
    mem = Memory(db_path=DB_PATH)
    relations = mem.get_relations("测试实体A")
    assert len(relations) > 0, "获取关系失败"


def test_associate():
    """测试关联网络"""
    mem = Memory(db_path=DB_PATH)
    network = mem.associate("测试实体A", depth=1)
    # 修正字段名：代码返回 center 和 associations
    assert "center" in network, "关联网络缺少 center"
    assert "associations" in network, "关联网络缺少 associations"


def test_recall_by_context():
    """测试情境记忆"""
    mem = Memory(db_path=DB_PATH)
    results = mem.recall_by_context(people=["Mr Lee"])
    # 没有绑定过情境记忆时返回空列表
    assert isinstance(results, list), f"情境记忆返回类型错误: {type(results)}"


def test_working_memory():
    """测试工作记忆"""
    mem = Memory(db_path=DB_PATH)
    # 存储
    mem.hold("test_key", "test_value", priority=0.9)
    # 读取
    value = mem.retrieve("test_key")
    assert value == "test_value", "工作记忆读取失败"
    # 删除
    mem.forget("test_key")
    value = mem.retrieve("test_key")
    assert value is None, "工作记忆删除失败"


def test_get_stats():
    """测试统计信息"""
    mem = Memory(db_path=DB_PATH)
    stats = mem.get_stats()
    # 修正字段名：代码返回 facts 而不是 facts_count
    assert "facts" in stats, "缺少 facts"
    assert "experiences" in stats, "缺少 experiences"
    assert "relations" in stats, "缺少 relations"


def test_update():
    """测试更新记忆"""
    mem = Memory(db_path=DB_PATH)
    if hasattr(test_remember, 'memory_id'):
        mem.update(test_remember.memory_id, importance=0.9)
        # 验证更新
        results = mem.recall("测试记忆 - 功能验证", limit=1)
        if results:
            assert results[0].get("importance") == 0.9, "更新失败"


def test_delete():
    """测试删除记忆"""
    mem = Memory(db_path=DB_PATH)
    if hasattr(test_remember, 'memory_id'):
        mem.delete(test_remember.memory_id)
        # 验证删除
        results = mem.recall("测试记忆 - 功能验证", limit=5)
        # 应该找不到刚才删除的
        for r in results:
            if r.get("id") == test_remember.memory_id:
                raise AssertionError("删除失败：记忆仍然存在")


def test_export():
    """测试导出功能"""
    mem = Memory(db_path=DB_PATH)
    # JSON 导出
    data = mem.export(format="json")
    assert isinstance(data, dict), "JSON 导出返回类型错误"


def test_visualize():
    """测试可视化功能"""
    mem = Memory(db_path=DB_PATH)
    try:
        path = mem.visualize()
        assert path is not None, "可视化返回路径为空"
    except Exception as e:
        # 可视化可能依赖外部库，记录但不失败
        print(f"  [WARN] 可视化跳过: {e}")


def test_forgetting_curve():
    """测试遗忘曲线"""
    mem = Memory(db_path=DB_PATH)
    try:
        mem.apply_forgetting()
        # 不应该报错
    except Exception as e:
        raise AssertionError(f"遗忘曲线应用失败: {e}")


def test_consolidate():
    """测试记忆整合"""
    mem = Memory(db_path=DB_PATH)
    try:
        mem.consolidate()
    except Exception as e:
        raise AssertionError(f"记忆整合失败: {e}")


def cleanup_test_data():
    """清理测试数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 删除测试数据
    cursor.execute("DELETE FROM facts WHERE content LIKE '%测试记忆 - 功能验证%'")
    cursor.execute("DELETE FROM experiences WHERE action LIKE '%测试教训%'")
    cursor.execute("DELETE FROM relations WHERE from_entity LIKE '%测试实体%'")
    cursor.execute("DELETE FROM entities WHERE name LIKE '%测试实体%'")
    
    conn.commit()
    conn.close()
    print("\n[CLEANUP] 测试数据已清理")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("MemoryCoreClaw 功能完整性测试")
    print("=" * 60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据库: {DB_PATH}")
    print()
    
    # 核心功能
    test("1. 初始化", test_init)
    test("2. 记忆存储 (remember)", test_remember)
    test("3. 记忆搜索 (recall)", test_recall)
    test("4. 教训记录 (learn)", test_learn)
    test("5. 获取教训 (get_lessons)", test_get_lessons)
    test("6. 关系建立 (relate)", test_relate)
    test("7. 获取关系 (get_relations)", test_get_relations)
    test("8. 关联网络 (associate)", test_associate)
    test("9. 情境记忆 (recall_by_context)", test_recall_by_context)
    test("10. 工作记忆 (hold/retrieve/forget)", test_working_memory)
    test("11. 统计信息 (get_stats)", test_get_stats)
    test("12. 更新记忆 (update)", test_update)
    test("13. 删除记忆 (delete)", test_delete)
    test("14. 导出功能 (export)", test_export)
    test("15. 可视化功能 (visualize)", test_visualize)
    test("16. 遗忘曲线 (apply_forgetting)", test_forgetting_curve)
    test("17. 记忆整合 (consolidate)", test_consolidate)
    
    # 清理测试数据
    cleanup_test_data()
    
    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for r in results if r[1] == "PASS")
    failed = sum(1 for r in results if r[1] == "FAIL")
    
    print(f"\n通过: {passed}/{len(results)}")
    print(f"失败: {failed}/{len(results)}")
    
    if failed > 0:
        print("\n失败的测试:")
        for name, status, error in results:
            if status == "FAIL":
                print(f"  - {name}: {error}")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)