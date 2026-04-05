"""
生成记忆可视化报告

使用方法：
    python scripts/generate_visualization.py

环境变量：
    MEMORY_DB_PATH - 数据库路径
    MEMORY_OUTPUT_DIR - 输出目录
"""
import os
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from memorycoreclaw.utils.visualization import MemoryVisualization

DB_PATH = os.environ.get('MEMORY_DB_PATH', 'memory.db')
OUTPUT_DIR = os.environ.get('MEMORY_OUTPUT_DIR', 'output')


def generate_visualization():
    """生成可视化报告"""
    
    print("=" * 60)
    print("📊 生成记忆可视化")
    print("=" * 60)
    print(f"\n数据库路径: {DB_PATH}")
    print(f"输出目录: {OUTPUT_DIR}\n")
    
    # 创建输出目录
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # 生成可视化
    viz = MemoryVisualization(db_path=DB_PATH, output_dir=OUTPUT_DIR)
    
    # 生成知识图谱
    print("生成知识图谱...")
    graph_path = viz.generate_knowledge_graph()
    print(f"  ✅ {graph_path}")
    
    # 生成统计报告
    print("生成统计报告...")
    stats_path = viz.generate_stats_report()
    print(f"  ✅ {stats_path}")
    
    # 生成记忆浏览器
    print("生成记忆浏览器...")
    browser_path = viz.generate_memory_browser()
    print(f"  ✅ {browser_path}")
    
    print("\n" + "=" * 60)
    print("✅ 可视化生成完成")
    print(f"输出目录: {Path(OUTPUT_DIR).absolute()}")
    print("=" * 60)


if __name__ == "__main__":
    generate_visualization()
