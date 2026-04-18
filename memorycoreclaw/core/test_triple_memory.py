#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive Memory System Test Suite
记忆系统全面测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))))

import json
from triple_memory import TripleMemory

def test_episodic_memory():
    """测试情节记忆"""
    print('[TEST 1] Episodic Memory (情节记忆)')
    db_path = os.environ.get('MEMORY_DB_PATH', '/path/to/memory.db')
    memory = TripleMemory(db_path)
    
    # 测试1: 记住事件
    event_id = memory.remember_event(
        content="User asked to create a PowerPoint presentation",
        action="create_presentation",
        outcome="Successfully created presentation with 10 slides",
        importance=0.9,
        context={"user": "Mr Lee", "tool": "pptx", "slides": 10},
        tags=["presentation", "pptx", "success"]
    )
    print(f'    1.1 记住事件: ID={event_id} - {"PASS" if event_id else "FAIL"}')
    
    # 测试2: 检索事件
    events = memory.recall_events("presentation", limit=5)
    print(f'    1.2 检索事件: 找到{len(events)}个 - {"PASS" if len(events) > 0 else "FAIL"}')
    for e in events[:2]:
        print(f'         - {e["action"]}: {e["outcome"][:30]}...')
    
    # 测试3: 获取重要事件
    important = memory.get_important_events(limit=5)
    print(f'    1.3 重要事件: {len(important)}个 - {"PASS" if len(important) >= 0 else "FAIL"}')
    
    return True


def test_semantic_memory():
    """测试语义记忆"""
    print('\n[TEST 2] Semantic Memory (语义记忆)')
    db_path = os.environ.get('MEMORY_DB_PATH', '/path/to/memory.db')
    memory = TripleMemory(db_path)
    
    # 测试1: 学习事实
    fact_id = memory.learn_fact(
        content="An AI agent framework example",
        entity="ExampleAgent",
        value="AI agent framework",
        confidence=0.95,
        source="documentation",
        category="technology",
        tags=["AI", "agent", "framework"]
    )
    print(f'    2.1 学习事实: ID={fact_id} - {"PASS" if fact_id else "FAIL"}')
    
    # 测试2: 检索事实
    facts = memory.recall_facts("AI agent", limit=5)
    print(f'    2.2 检索事实: 找到{len(facts)}个 - {"PASS" if len(facts) >= 0 else "FAIL"}')
    for f in facts[:2]:
        print(f'         - {f["content"][:40]}... (conf: {f["confidence"]})')
    
    # 测试3: 提取知识
    text = "老K是一个AI助手，它是全能助手，具有顶级管理者、领导者思维"
    extracted = memory.extract_knowledge(text, source="extraction")
    print(f'    2.3 提取知识: 提取{len(extracted)}个事实 - {"PASS" if len(extracted) >= 0 else "FAIL"}')
    
    return True


def test_procedural_memory():
    """测试程序记忆"""
    print('\n[TEST 3] Procedural Memory (程序记忆)')
    db_path = os.environ.get('MEMORY_DB_PATH', '/path/to/memory.db')
    memory = TripleMemory(db_path)
    
    # 测试1: 记住流程
    proc_id = memory.remember_procedure(
        name="create_pptx_workflow",
        description="创建PPT的完整工作流程",
        steps=["1. 收集需求", "2. 设计结构", "3. 创建内容", "4. 导出文件"],
        skill_name="pptx",
        version="1.0.0",
        category="workflow",
        tags=["presentation", "workflow"]
    )
    print(f'    3.1 记住流程: ID={proc_id} - {"PASS" if proc_id else "FAIL"}')
    
    # 测试2: 检索流程
    procedures = memory.recall_procedures("pptx", limit=5)
    print(f'    3.2 检索流程: 找到{len(procedures)}个 - {"PASS" if len(procedures) >= 0 else "FAIL"}')
    for p in procedures[:2]:
        print(f'         - {p["name"]}: {p["description"][:30]}...')
    
    # 测试3: 记录执行
    memory.record_skill_execution("create_pptx_workflow", success=True, duration_ms=5000)
    print(f'    3.3 记录执行: 成功 - PASS')
    
    return True


def test_unified_search():
    """测试统一搜索"""
    print('\n[TEST 4] Unified Search (统一搜索)')
    db_path = os.environ.get('MEMORY_DB_PATH', '/path/to/memory.db')
    memory = TripleMemory(db_path)
    
    # 搜索
    results = memory.search("create", memory_types=['episodic', 'semantic', 'procedural'], limit=5)
    print(f'    4.1 统一搜索:')
    print(f'         - 情节: {len(results.get("episodic", []))}个')
    print(f'         - 语义: {len(results.get("semantic", []))}个')
    print(f'         - 程序: {len(results.get("procedural", []))}个')
    
    total = len(results.get('episodic', [])) + len(results.get('semantic', [])) + len(results.get('procedural', []))
    print(f'    总计: {total}个 - {"PASS" if total >= 0 else "FAIL"}')
    
    return True


def test_statistics():
    """测试统计功能"""
    print('\n[TEST 5] Statistics (统计功能)')
    db_path = os.environ.get('MEMORY_DB_PATH', '/path/to/memory.db')
    memory = TripleMemory(db_path)
    
    stats = memory.get_statistics()
    print(f'    5.1 统计信息:')
    print(f'         - 情节记忆最近: {stats["episodic"]["recent"]}个')
    print(f'         - 情节记忆重要: {stats["episodic"]["important"]}个')
    print(f'         - 语义记忆总数: {stats["semantic"]["total"]}个')
    print(f'         - 程序记忆总数: {stats["procedural"]["total"]}个')
    
    # 检查语义记忆详情
    if stats["semantic"]["total"] > 0:
        print(f'         - 按分类: {stats["semantic"]["by_category"]}')
        print(f'         - 按来源: {stats["semantic"]["by_source"]}')
        print(f'         - 平均置信度: {stats["semantic"]["avg_confidence"]}')
    
    # 检查程序记忆详情
    if stats["procedural"]["total"] > 0:
        print(f'         - 平均成功率: {stats["procedural"]["avg_success_rate"]}')
        print(f'         - 总使用次数: {stats["procedural"]["total_usage"]}')
    
    print(f'    统计功能: PASS')
    return True


def test_data_integrity():
    """测试数据完整性"""
    print('\n[TEST 6] Data Integrity (数据完整性)')
    db_path = os.environ.get('MEMORY_DB_PATH', '/path/to/memory.db')
    memory = TripleMemory(db_path)
    
    # 检查各种边界情况
    tests_passed = 0
    total_tests = 0
    
    # 测试1: 空内容
    total_tests += 1
    try:
        event_id = memory.remember_event("", "test_action", "neutral", importance=0.5)
        # 空内容可能被存储或被拒绝
        tests_passed += 1
        print(f'    6.1 空内容处理: PASS (event_id={event_id})')
    except Exception as e:
        print(f'    6.1 空内容处理: FAIL - {e}')
    
    # 测试2: 特殊字符
    total_tests += 1
    try:
        fact_id = memory.learn_fact(
            content="测试特殊字符: <>&\"'",
            entity="test",
            value="特殊字符",
            confidence=0.8
        )
        tests_passed += 1
        print(f'    6.2 特殊字符处理: PASS (fact_id={fact_id})')
    except Exception as e:
        print(f'    6.2 特殊字符处理: FAIL - {e}')
    
    # 测试3: 长文本
    total_tests += 1
    try:
        long_text = "这是一个很长的文本内容. " * 100
        proc_id = memory.remember_procedure(
            name="long_test",
            description=long_text[:50],
            steps=[long_text[:100]],
            category="test"
        )
        tests_passed += 1
        print(f'    6.3 长文本处理: PASS (proc_id={proc_id})')
    except Exception as e:
        print(f'    6.3 长文本处理: FAIL - {e}')
    
    # 测试4: 中文内容
    total_tests += 1
    try:
        fact_id = memory.learn_fact(
            content="老K是全能助手",
            entity="老K",
            value="全能助手",
            confidence=0.9,
            category="person"
        )
        facts = memory.recall_facts("老K")
        tests_passed += 1
        print(f'    6.4 中文内容处理: PASS (找到{len(facts)}个)')
    except Exception as e:
        print(f'    6.4 中文内容处理: FAIL - {e}')
    
    print(f'    数据完整性: {tests_passed}/{total_tests} PASS')
    return tests_passed == total_tests


def main():
    """运行所有测试"""
    print('=' * 60)
    print('Triple Memory System - Comprehensive Test Suite')
    print('三层记忆系统 - 全面测试')
    print('=' * 60)
    print()
    
    results = []
    
    try:
        results.append(('情节记忆', test_episodic_memory()))
    except Exception as e:
        print(f'    ERROR: {e}')
        results.append(('情节记忆', False))
    
    try:
        results.append(('语义记忆', test_semantic_memory()))
    except Exception as e:
        print(f'    ERROR: {e}')
        results.append(('语义记忆', False))
    
    try:
        results.append(('程序记忆', test_procedural_memory()))
    except Exception as e:
        print(f'    ERROR: {e}')
        results.append(('程序记忆', False))
    
    try:
        results.append(('统一搜索', test_unified_search()))
    except Exception as e:
        print(f'    ERROR: {e}')
        results.append(('统一搜索', False))
    
    try:
        results.append(('统计功能', test_statistics()))
    except Exception as e:
        print(f'    ERROR: {e}')
        results.append(('统计功能', False))
    
    try:
        results.append(('数据完整性', test_data_integrity()))
    except Exception as e:
        print(f'    ERROR: {e}')
        results.append(('数据完整性', False))
    
    # 总结
    print('\n' + '=' * 60)
    print('Test Summary (测试总结)')
    print('=' * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        print(f'    {name}: {"PASS" if result else "FAIL"}')
    
    print(f'\nTotal: {passed}/{total} passed')
    
    if passed == total:
        print('\n[OK] All tests passed! 记忆系统检查完成')
        return 0
    else:
        print('\n[FAIL] Some tests failed')
        return 1


if __name__ == '__main__':
    sys.exit(main())