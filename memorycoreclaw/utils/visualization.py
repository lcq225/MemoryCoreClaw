"""
MemoryCoreClaw - Memory Visualization Module

Generate knowledge graphs and visualizations.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json


class MemoryVisualizer:
    """
    Memory Visualizer
    
    Generate HTML knowledge graphs and statistics reports.
    """
    
    def __init__(self, memory_engine):
        self.engine = memory_engine
    
    def generate_knowledge_graph(self, output_path: str = None) -> str:
        """
        Generate an interactive knowledge graph HTML.
        
        Args:
            output_path: Optional file path to save
            
        Returns:
            HTML content
        """
        relations = self.engine.get_stats()
        
        # Get all relations
        # Note: This is a simplified version
        nodes = set()
        edges = []
        
        # Simple force-directed graph HTML
        html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>MemoryCoreClaw - Knowledge Graph</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body { margin: 0; font-family: Arial, sans-serif; }
        .node { cursor: pointer; }
        .node circle { fill: #4a90d9; stroke: #fff; stroke-width: 2px; }
        .node text { font-size: 12px; fill: #333; }
        .link { stroke: #999; stroke-opacity: 0.6; }
        .link-label { font-size: 10px; fill: #666; }
    </style>
</head>
<body>
    <svg id="graph" width="100%" height="800"></svg>
    <script>
        // Graph data will be injected here
        const data = {nodes: [], links: []};
        
        const svg = d3.select("#graph");
        const width = svg.node().getBoundingClientRect().width;
        const height = 800;
        
        const simulation = d3.forceSimulation(data.nodes)
            .force("link", d3.forceLink(data.links).id(d => d.id))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2));
        
        const link = svg.append("g")
            .selectAll("line")
            .data(data.links)
            .enter().append("line")
            .attr("class", "link")
            .attr("stroke-width", 2);
        
        const node = svg.append("g")
            .selectAll("g")
            .data(data.nodes)
            .enter().append("g")
            .attr("class", "node")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));
        
        node.append("circle").attr("r", 10);
        node.append("text").attr("dx", 12).attr("dy", ".35em").text(d => d.id);
        
        simulation.on("tick", () => {
            link.attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            node.attr("transform", d => `translate(${d.x},${d.y})`);
        });
        
        function dragstarted(event) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }
        function dragged(event) {
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }
        function dragended(event) {
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }
    </script>
</body>
</html>'''
        
        if output_path:
            Path(output_path).write_text(html, encoding='utf-8')
        
        return html
    
    def generate_stats_report(self, output_path: str = None) -> str:
        """
        Generate a statistics report HTML.
        
        Args:
            output_path: Optional file path to save
            
        Returns:
            HTML content
        """
        stats = self.engine.get_stats()
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>MemoryCoreClaw - Statistics Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; }}
        h1 {{ color: #333; }}
        .stat-card {{ background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #4a90d9; }}
        .stat-label {{ color: #666; }}
    </style>
</head>
<body>
    <h1>MemoryCoreClaw Statistics</h1>
    <p>Generated: {datetime.now().isoformat()}</p>
    
    <div class="stat-card">
        <div class="stat-value">{stats['facts']}</div>
        <div class="stat-label">Facts</div>
    </div>
    
    <div class="stat-card">
        <div class="stat-value">{stats['experiences']}</div>
        <div class="stat-label">Lessons</div>
    </div>
    
    <div class="stat-card">
        <div class="stat-value">{stats['relations']}</div>
        <div class="stat-label">Relations</div>
    </div>
    
    <div class="stat-card">
        <div class="stat-value">{stats['entities']}</div>
        <div class="stat-label">Entities</div>
    </div>
</body>
</html>'''
        
        if output_path:
            Path(output_path).write_text(html, encoding='utf-8')
        
        return html