"""
Graph Layout Algorithms for OSINT-Nexus.
Provides different layout strategies for visualizing entities.
"""

import math
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class LayoutNode:
    id: int
    x: float
    y: float

class GraphLayouts:
    """Collection of graph layout algorithms."""
    
    @staticmethod
    def circle_layout(node_ids: List[int], center: Tuple[float, float] = (0, 0), radius: float = 400) -> Dict[int, Tuple[float, float]]:
        """Arrange nodes in a circle."""
        positions = {}
        count = len(node_ids)
        if count == 0:
            return positions
            
        angle_step = 2 * math.pi / count
        cx, cy = center
        
        for i, node_id in enumerate(node_ids):
            angle = i * angle_step
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            positions[node_id] = (x, y)
            
        return positions

    @staticmethod
    def grid_layout(node_ids: List[int], width: float = 1000, spacing: float = 150) -> Dict[int, Tuple[float, float]]:
        """Arrange nodes in a grid."""
        positions = {}
        count = len(node_ids)
        if count == 0:
            return positions
            
        cols = math.ceil(math.sqrt(count))
        
        # Center the grid
        start_x = -(cols * spacing) / 2
        start_y = -(cols * spacing) / 2
        
        for i, node_id in enumerate(node_ids):
            row = i // cols
            col = i % cols
            
            x = start_x + (col * spacing)
            y = start_y + (row * spacing)
            positions[node_id] = (x, y)
            
        return positions
    
    @staticmethod
    def radial_layout(node_ids: List[int], root_id: int, edges: list, radius_step: float = 200) -> Dict[int, Tuple[float, float]]:
        """
        Arrange nodes in concentric circles around a root.
        This is a simple BFS-based layering.
        """
        positions = {}
        if not node_ids:
            return positions
            
        # Build adjacency
        adj = {n: [] for n in node_ids}
        for u, v in edges:
            if u in adj and v in adj:
                adj[u].append(v)
                adj[v].append(u)
                
        # BFS for layers
        layers = {}
        visited = {root_id}
        queue = [(root_id, 0)]
        layers[0] = [root_id]
        
        while queue:
            node, depth = queue.pop(0)
            
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_depth = depth + 1
                    if new_depth not in layers:
                        layers[new_depth] = []
                    layers[new_depth].append(neighbor)
                    queue.append((neighbor, new_depth))
        
        # Assign remaining unconnected nodes to outer layer
        unconnected = [n for n in node_ids if n not in visited]
        if unconnected:
            max_depth = max(layers.keys()) + 1 if layers else 0
            layers[max_depth] = unconnected
            
        # Calculate positions
        for depth, nodes in layers.items():
            radius = depth * radius_step
            count = len(nodes)
            angle_step = 2 * math.pi / count if count > 0 else 0
            
            for i, node_id in enumerate(nodes):
                angle = i * angle_step
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                positions[node_id] = (x, y)
                
        return positions
