"""
OSINT-Nexus Graph Analytics
Advanced graph analysis algorithms for intelligence extraction.
Implements community detection, centrality analysis, and anomaly detection.
"""

import math
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import random

import networkx as nx


@dataclass
class CentralityMetrics:
    """Centrality metrics for a node."""
    node_id: int
    degree: float = 0.0
    betweenness: float = 0.0
    closeness: float = 0.0
    pagerank: float = 0.0
    eigenvector: float = 0.0


@dataclass
class Community:
    """A detected community/cluster of nodes."""
    id: int
    node_ids: List[int]
    label: str = ""
    density: float = 0.0
    

@dataclass
class Anomaly:
    """An anomalous pattern in the graph."""
    node_id: int
    anomaly_type: str  # outlier, hub, bridge, isolated
    score: float
    description: str


@dataclass
class PathResult:
    """Result of path analysis."""
    source_id: int
    target_id: int
    path: List[int]
    length: int
    relationships: List[str]


class GraphAnalytics:
    """
    Advanced graph analytics for OSINT intelligence.
    
    Uses NetworkX for graph algorithms with custom analysis layers.
    """
    
    def __init__(self):
        self.graph: Optional[nx.Graph] = None
        self.directed_graph: Optional[nx.DiGraph] = None
        self._communities: List[Community] = []
        self._centrality_cache: Dict[int, CentralityMetrics] = {}
        
    def build_graph(
        self, 
        nodes: List[Dict[str, Any]], 
        edges: List[Tuple[int, int, str]]
    ):
        """
        Build NetworkX graph from nodes and edges.
        
        Args:
            nodes: List of node dicts with 'id', 'type', 'value', 'attributes'
            edges: List of (source_id, target_id, relationship) tuples
        """
        self.graph = nx.Graph()
        self.directed_graph = nx.DiGraph()
        
        # Add nodes
        for node in nodes:
            node_id = node.get('id', 0)
            self.graph.add_node(
                node_id,
                type=node.get('type', ''),
                value=node.get('value', ''),
                label=node.get('label', node.get('value', '')),
                attributes=node.get('attributes', {})
            )
            self.directed_graph.add_node(
                node_id,
                type=node.get('type', ''),
                value=node.get('value', ''),
                label=node.get('label', node.get('value', '')),
                attributes=node.get('attributes', {})
            )
        
        # Add edges
        for src, tgt, rel in edges:
            self.graph.add_edge(src, tgt, relationship=rel, weight=1.0)
            self.directed_graph.add_edge(src, tgt, relationship=rel, weight=1.0)
        
        # Clear caches
        self._centrality_cache.clear()
        self._communities.clear()
    
    def detect_communities(self) -> List[Community]:
        """
        Detect communities using the Louvain algorithm.
        
        Returns:
            List of Community objects with node assignments
        """
        if not self.graph or len(self.graph.nodes()) == 0:
            return []
        
        try:
            # Use Louvain community detection
            import networkx.algorithms.community as nx_comm
            communities = nx_comm.louvain_communities(self.graph, seed=42)
            
            self._communities = []
            for i, community_set in enumerate(communities):
                node_ids = list(community_set)
                
                # Calculate community density
                subgraph = self.graph.subgraph(node_ids)
                n = len(node_ids)
                if n > 1:
                    density = nx.density(subgraph)
                else:
                    density = 0.0
                
                # Generate label based on dominant entity type
                type_counts: Dict[str, int] = defaultdict(int)
                for nid in node_ids:
                    if nid in self.graph.nodes:
                        ntype = self.graph.nodes[nid].get('type', 'unknown')
                        type_counts[ntype] += 1
                
                dominant_type = max(type_counts, key=type_counts.get) if type_counts else "mixed"
                label = f"Community {i+1} ({dominant_type})"
                
                self._communities.append(Community(
                    id=i,
                    node_ids=node_ids,
                    label=label,
                    density=density
                ))
            
            return self._communities
            
        except Exception as e:
            print(f"Community detection error: {e}")
            return []
    
    def calculate_centrality(self) -> Dict[int, CentralityMetrics]:
        """
        Calculate centrality metrics for all nodes.
        
        Computes:
        - Degree centrality
        - Betweenness centrality
        - Closeness centrality
        - PageRank
        - Eigenvector centrality
        """
        if not self.graph or len(self.graph.nodes()) == 0:
            return {}
        
        if self._centrality_cache:
            return self._centrality_cache
        
        try:
            # Calculate all centrality metrics
            degree = nx.degree_centrality(self.graph)
            betweenness = nx.betweenness_centrality(self.graph)
            
            # Closeness might fail on disconnected graphs
            try:
                closeness = nx.closeness_centrality(self.graph)
            except:
                closeness = {n: 0.0 for n in self.graph.nodes()}
            
            # PageRank on directed graph
            try:
                pagerank = nx.pagerank(self.directed_graph, max_iter=100)
            except:
                pagerank = {n: 1.0 / len(self.graph.nodes()) for n in self.graph.nodes()}
            
            # Eigenvector might fail on disconnected graphs
            try:
                eigenvector = nx.eigenvector_centrality(self.graph, max_iter=100)
            except:
                eigenvector = {n: 0.0 for n in self.graph.nodes()}
            
            # Combine into CentralityMetrics
            for node_id in self.graph.nodes():
                self._centrality_cache[node_id] = CentralityMetrics(
                    node_id=node_id,
                    degree=degree.get(node_id, 0.0),
                    betweenness=betweenness.get(node_id, 0.0),
                    closeness=closeness.get(node_id, 0.0),
                    pagerank=pagerank.get(node_id, 0.0),
                    eigenvector=eigenvector.get(node_id, 0.0)
                )
            
            return self._centrality_cache
            
        except Exception as e:
            print(f"Centrality calculation error: {e}")
            return {}
    
    def get_top_entities(self, metric: str = "pagerank", n: int = 10) -> List[Tuple[int, float]]:
        """
        Get top N entities by centrality metric.
        
        Args:
            metric: One of 'degree', 'betweenness', 'closeness', 'pagerank', 'eigenvector'
            n: Number of top entities to return
        """
        centrality = self.calculate_centrality()
        if not centrality:
            return []
        
        # Extract metric values
        scores = []
        for node_id, metrics in centrality.items():
            score = getattr(metrics, metric, 0.0)
            scores.append((node_id, score))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:n]
    
    def find_shortest_paths(self, source_id: int, target_id: int) -> List[PathResult]:
        """
        Find all shortest paths between two nodes.
        """
        if not self.graph:
            return []
        
        try:
            paths = list(nx.all_shortest_paths(self.graph, source_id, target_id))
            results = []
            
            for path in paths[:5]:  # Limit to 5 paths
                relationships = []
                for i in range(len(path) - 1):
                    edge_data = self.graph.get_edge_data(path[i], path[i+1])
                    rel = edge_data.get('relationship', 'connected') if edge_data else 'connected'
                    relationships.append(rel)
                
                results.append(PathResult(
                    source_id=source_id,
                    target_id=target_id,
                    path=path,
                    length=len(path) - 1,
                    relationships=relationships
                ))
            
            return results
            
        except nx.NetworkXNoPath:
            return []
        except Exception as e:
            print(f"Path finding error: {e}")
            return []
    
    def detect_anomalies(self, sensitivity: float = 2.0) -> List[Anomaly]:
        """
        Detect anomalous nodes using statistical analysis.
        
        Identifies:
        - Outliers: Nodes with unusually high/low connectivity
        - Hubs: Nodes connecting many different entity types
        - Bridges: Nodes that connect otherwise disconnected communities
        - Isolated: Nodes with no connections
        """
        if not self.graph or len(self.graph.nodes()) == 0:
            return []
        
        anomalies = []
        centrality = self.calculate_centrality()
        
        # Calculate statistics
        degrees = [self.graph.degree(n) for n in self.graph.nodes()]
        if not degrees:
            return []
            
        avg_degree = sum(degrees) / len(degrees)
        std_degree = math.sqrt(sum((d - avg_degree) ** 2 for d in degrees) / len(degrees)) if len(degrees) > 1 else 0
        
        for node_id in self.graph.nodes():
            degree = self.graph.degree(node_id)
            
            # Check for isolated nodes
            if degree == 0:
                anomalies.append(Anomaly(
                    node_id=node_id,
                    anomaly_type="isolated",
                    score=1.0,
                    description="Node has no connections"
                ))
                continue
            
            # Check for outlier (unusually high degree)
            if std_degree > 0 and (degree - avg_degree) / std_degree > sensitivity:
                score = min(1.0, (degree - avg_degree) / (sensitivity * std_degree))
                anomalies.append(Anomaly(
                    node_id=node_id,
                    anomaly_type="outlier",
                    score=score,
                    description=f"Unusually high connectivity ({degree} connections)"
                ))
            
            # Check for bridge nodes (high betweenness)
            metrics = centrality.get(node_id)
            if metrics and metrics.betweenness > 0.3:
                anomalies.append(Anomaly(
                    node_id=node_id,
                    anomaly_type="bridge",
                    score=metrics.betweenness,
                    description="Acts as a bridge between different parts of the graph"
                ))
            
            # Check for hub (connects many different entity types)
            neighbor_types: Set[str] = set()
            for neighbor in self.graph.neighbors(node_id):
                ntype = self.graph.nodes[neighbor].get('type', '')
                neighbor_types.add(ntype)
            
            if len(neighbor_types) >= 3:
                score = min(1.0, len(neighbor_types) / 5.0)
                anomalies.append(Anomaly(
                    node_id=node_id,
                    anomaly_type="hub",
                    score=score,
                    description=f"Hub connecting {len(neighbor_types)} different entity types"
                ))
        
        return anomalies
    
    def cluster_by_type(self) -> Dict[str, List[int]]:
        """Group nodes by entity type."""
        if not self.graph:
            return {}
        
        clusters: Dict[str, List[int]] = defaultdict(list)
        for node_id in self.graph.nodes():
            node_type = self.graph.nodes[node_id].get('type', 'unknown')
            clusters[node_type].append(node_id)
        
        return dict(clusters)
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get overall graph statistics."""
        if not self.graph:
            return {}
        
        stats = {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "density": nx.density(self.graph) if self.graph.number_of_nodes() > 1 else 0,
            "connected_components": nx.number_connected_components(self.graph),
            "is_connected": nx.is_connected(self.graph) if self.graph.number_of_nodes() > 0 else False,
        }
        
        # Add average clustering coefficient
        try:
            stats["avg_clustering"] = nx.average_clustering(self.graph)
        except:
            stats["avg_clustering"] = 0.0
        
        # Diameter (only for connected graphs)
        if stats["is_connected"] and self.graph.number_of_nodes() > 1:
            try:
                stats["diameter"] = nx.diameter(self.graph)
            except:
                stats["diameter"] = None
        else:
            stats["diameter"] = None
        
        return stats
    
    def export_gexf(self, filepath: str):
        """Export graph to GEXF format (for Gephi)."""
        if self.graph:
            nx.write_gexf(self.graph, filepath)
    
    def export_graphml(self, filepath: str):
        """Export graph to GraphML format."""
        if self.graph:
            nx.write_graphml(self.graph, filepath)


# Global instance for easy access
graph_analytics = GraphAnalytics()
