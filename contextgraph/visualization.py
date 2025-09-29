"""
Graph Visualization Module for igraph-cypher-db

This module provides comprehensive graph visualization capabilities with multiple backends:
- matplotlib + networkx (static plots)
- plotly (interactive plots)
- graphviz (publication-quality layouts)

Features:
- Multiple layout algorithms
- Node/edge styling based on properties
- Interactive exploration
- Export to various formats
- Query result visualization
"""

import warnings
from typing import Dict, List, Optional, Tuple, Any, Union
from collections import defaultdict
import json

# Optional imports - gracefully handle missing dependencies
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    plt = None
    patches = None

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    nx = None

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
    go = None
    px = None
    make_subplots = None

try:
    import graphviz
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False
    graphviz = None


class GraphVisualizer:
    """Main graph visualization class."""
    
    def __init__(self, graph_db):
        """Initialize visualizer with a GraphDB instance."""
        self.graph_db = graph_db
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check which visualization backends are available."""
        self.available_backends = []
        
        if HAS_MATPLOTLIB and HAS_NETWORKX:
            self.available_backends.append('matplotlib')
        if HAS_PLOTLY:
            self.available_backends.append('plotly')
        if HAS_GRAPHVIZ:
            self.available_backends.append('graphviz')
        
        if not self.available_backends:
            warnings.warn(
                "No visualization backends available. Install one of: "
                "matplotlib+networkx, plotly, or graphviz"
            )
    
    def plot(self, 
             backend: str = 'auto',
             layout: str = 'spring',
             node_size_property: Optional[str] = None,
             node_color_property: Optional[str] = None,
             edge_width_property: Optional[str] = None,
             node_labels: bool = True,
             edge_labels: bool = False,
             title: Optional[str] = None,
             figsize: Tuple[int, int] = (12, 8),
             save_path: Optional[str] = None,
             **kwargs) -> Any:
        """
        Create a graph visualization.
        
        Args:
            backend: Visualization backend ('matplotlib', 'plotly', 'graphviz', 'auto')
            layout: Layout algorithm ('spring', 'circular', 'random', 'shell', 'kamada_kawai')
            node_size_property: Node property to use for sizing
            node_color_property: Node property to use for coloring
            edge_width_property: Edge property to use for width
            node_labels: Whether to show node labels
            edge_labels: Whether to show edge labels
            title: Plot title
            figsize: Figure size (width, height)
            save_path: Path to save the plot
            **kwargs: Additional backend-specific arguments
            
        Returns:
            Backend-specific plot object
        """
        if backend == 'auto':
            backend = self._choose_backend()
        
        if backend not in self.available_backends:
            raise ValueError(f"Backend '{backend}' not available. Available: {self.available_backends}")
        
        if backend == 'matplotlib':
            return self._plot_matplotlib(
                layout, node_size_property, node_color_property, edge_width_property,
                node_labels, edge_labels, title, figsize, save_path, **kwargs
            )
        elif backend == 'plotly':
            return self._plot_plotly(
                layout, node_size_property, node_color_property, edge_width_property,
                node_labels, edge_labels, title, figsize, save_path, **kwargs
            )
        elif backend == 'graphviz':
            return self._plot_graphviz(
                layout, node_size_property, node_color_property, edge_width_property,
                node_labels, edge_labels, title, save_path, **kwargs
            )
        else:
            raise ValueError(f"Unknown backend: {backend}")
    
    def _choose_backend(self) -> str:
        """Choose the best available backend."""
        if 'plotly' in self.available_backends:
            return 'plotly'  # Interactive is preferred
        elif 'matplotlib' in self.available_backends:
            return 'matplotlib'
        elif 'graphviz' in self.available_backends:
            return 'graphviz'
        else:
            raise RuntimeError("No visualization backends available")
    
    def _create_networkx_graph(self) -> 'nx.Graph':
        """Create a NetworkX graph from the database."""
        if not HAS_NETWORKX:
            raise ImportError("NetworkX is required for this functionality")
        
        G = nx.DiGraph()  # Use directed graph
        
        # Add nodes
        nodes = self.graph_db.find_nodes()
        for node in nodes:
            # Create node label
            labels = node.get('labels', [])
            props = node.get('properties', {})
            
            # Try to find a good label
            label = None
            for prop_name in ['name', 'title', 'id', 'label']:
                if prop_name in props:
                    label = str(props[prop_name])
                    break
            
            if not label:
                label = f"{':'.join(labels) if labels else 'Node'}({node['id']})"
            
            G.add_node(node['id'], 
                      label=label,
                      labels=labels,
                      **props)
        
        # Add edges
        relationships = self.graph_db.find_relationships()
        for rel in relationships:
            G.add_edge(rel['source'], rel['target'],
                      type=rel['type'],
                      label=rel['type'],
                      **rel.get('properties', {}))
        
        return G
    
    def _plot_matplotlib(self, layout, node_size_property, node_color_property, 
                        edge_width_property, node_labels, edge_labels, title, 
                        figsize, save_path, **kwargs):
        """Create matplotlib visualization."""
        if not (HAS_MATPLOTLIB and HAS_NETWORKX):
            raise ImportError("matplotlib and networkx are required")
        
        G = self._create_networkx_graph()
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Choose layout
        if layout == 'spring':
            pos = nx.spring_layout(G, k=1, iterations=50)
        elif layout == 'circular':
            pos = nx.circular_layout(G)
        elif layout == 'random':
            pos = nx.random_layout(G)
        elif layout == 'shell':
            pos = nx.shell_layout(G)
        elif layout == 'kamada_kawai':
            pos = nx.kamada_kawai_layout(G)
        else:
            pos = nx.spring_layout(G)
        
        # Node styling
        node_sizes = self._get_node_sizes(G, node_size_property)
        node_colors = self._get_node_colors(G, node_color_property)
        
        # Edge styling
        edge_widths = self._get_edge_widths(G, edge_width_property)
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, ax=ax, 
                              width=edge_widths,
                              edge_color='gray',
                              alpha=0.6,
                              arrows=True,
                              arrowsize=20,
                              arrowstyle='->')
        
        # Draw nodes
        nx.draw_networkx_nodes(G, pos, ax=ax,
                              node_size=node_sizes,
                              node_color=node_colors,
                              alpha=0.8,
                              cmap=plt.cm.Set3)
        
        # Draw labels
        if node_labels:
            labels = {node: G.nodes[node].get('label', str(node)) for node in G.nodes()}
            nx.draw_networkx_labels(G, pos, labels, ax=ax, font_size=8)
        
        if edge_labels:
            edge_labels_dict = {(u, v): G[u][v].get('label', '') for u, v in G.edges()}
            nx.draw_networkx_edge_labels(G, pos, edge_labels_dict, ax=ax, font_size=6)
        
        # Styling
        ax.set_title(title or f"Graph Visualization ({len(G.nodes)} nodes, {len(G.edges)} edges)")
        ax.axis('off')
        
        # Add legend for node types if colored by property
        if node_color_property:
            self._add_matplotlib_legend(ax, G, node_color_property)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def _plot_plotly(self, layout, node_size_property, node_color_property,
                    edge_width_property, node_labels, edge_labels, title,
                    figsize, save_path, **kwargs):
        """Create interactive Plotly visualization."""
        if not HAS_PLOTLY:
            raise ImportError("plotly is required")
        
        G = self._create_networkx_graph()
        
        # Choose layout (using networkx for positioning)
        if layout == 'spring':
            pos = nx.spring_layout(G, k=1, iterations=50)
        elif layout == 'circular':
            pos = nx.circular_layout(G)
        elif layout == 'random':
            pos = nx.random_layout(G)
        elif layout == 'shell':
            pos = nx.shell_layout(G)
        elif layout == 'kamada_kawai':
            pos = nx.kamada_kawai_layout(G)
        else:
            pos = nx.spring_layout(G)
        
        # Extract coordinates
        node_x = [pos[node][0] for node in G.nodes()]
        node_y = [pos[node][1] for node in G.nodes()]
        
        # Create edge traces
        edge_x = []
        edge_y = []
        edge_info = []
        
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_info.append(G[edge[0]][edge[1]].get('label', ''))
        
        edge_trace = go.Scatter(x=edge_x, y=edge_y,
                               line=dict(width=2, color='#888'),
                               hoverinfo='none',
                               mode='lines')
        
        # Create node trace
        node_sizes = self._get_node_sizes(G, node_size_property, scale_factor=0.5)
        node_colors = self._get_node_colors_plotly(G, node_color_property)
        
        node_trace = go.Scatter(x=node_x, y=node_y,
                               mode='markers+text' if node_labels else 'markers',
                               hoverinfo='text',
                               text=[G.nodes[node].get('label', str(node)) for node in G.nodes()] if node_labels else None,
                               textposition="middle center",
                               marker=dict(size=node_sizes,
                                         color=node_colors,
                                         colorscale='Viridis',
                                         showscale=True if node_color_property else False,
                                         colorbar=dict(title=node_color_property) if node_color_property else None,
                                         line=dict(width=2, color='white')))
        
        # Create hover text
        node_hover_text = []
        for node in G.nodes():
            node_data = G.nodes[node]
            hover_text = f"Node {node}<br>"
            hover_text += f"Labels: {', '.join(node_data.get('labels', []))}<br>"
            
            # Add properties
            for key, value in node_data.items():
                if key not in ['label', 'labels']:
                    hover_text += f"{key}: {value}<br>"
            
            node_hover_text.append(hover_text)
        
        node_trace.hovertext = node_hover_text
        
        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title=dict(
                               text=title or f"Interactive Graph Visualization ({len(G.nodes)} nodes, {len(G.edges)} edges)",
                               font=dict(size=16)
                           ),
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           annotations=[ dict(
                               text="Drag to pan, scroll to zoom, hover for details",
                               showarrow=False,
                               xref="paper", yref="paper",
                               x=0.005, y=-0.002,
                               xanchor='left', yanchor='bottom',
                               font=dict(color='gray', size=12)
                           )],
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           width=figsize[0]*100,
                           height=figsize[1]*100))
        
        if save_path:
            if save_path.endswith('.html'):
                fig.write_html(save_path)
            else:
                fig.write_image(save_path)
        
        return fig
    
    def _plot_graphviz(self, layout, node_size_property, node_color_property,
                      edge_width_property, node_labels, edge_labels, title,
                      save_path, **kwargs):
        """Create Graphviz visualization."""
        if not HAS_GRAPHVIZ:
            raise ImportError("graphviz is required")
        
        # Create graphviz graph
        dot = graphviz.Digraph(comment=title or 'Graph')
        dot.attr(rankdir='TB' if layout == 'hierarchical' else 'LR')
        
        # Add nodes
        nodes = self.graph_db.find_nodes()
        for node in nodes:
            node_id = str(node['id'])
            
            # Create label
            labels = node.get('labels', [])
            props = node.get('properties', {})
            
            if node_labels:
                label_text = None
                for prop_name in ['name', 'title', 'id', 'label']:
                    if prop_name in props:
                        label_text = str(props[prop_name])
                        break
                
                if not label_text:
                    label_text = f"{':'.join(labels) if labels else 'Node'}({node['id']})"
            else:
                label_text = str(node['id'])
            
            # Node styling
            node_attrs = {'label': label_text}
            
            if labels:
                # Color by node type
                colors = ['lightblue', 'lightgreen', 'lightcoral', 'lightyellow', 'lightpink']
                color = colors[hash(':'.join(labels)) % len(colors)]
                node_attrs['fillcolor'] = color
                node_attrs['style'] = 'filled'
            
            dot.node(node_id, **node_attrs)
        
        # Add edges
        relationships = self.graph_db.find_relationships()
        for rel in relationships:
            source_id = str(rel['source'])
            target_id = str(rel['target'])
            
            edge_attrs = {}
            if edge_labels:
                edge_attrs['label'] = rel['type']
            
            dot.edge(source_id, target_id, **edge_attrs)
        
        if save_path:
            format_ext = save_path.split('.')[-1] if '.' in save_path else 'png'
            dot.render(save_path.rsplit('.', 1)[0], format=format_ext, cleanup=True)
        
        return dot
    
    def _get_node_sizes(self, G, size_property, scale_factor=1.0):
        """Get node sizes based on property."""
        if not size_property:
            return [300 * scale_factor] * len(G.nodes())
        
        sizes = []
        values = [G.nodes[node].get(size_property, 1) for node in G.nodes()]
        
        if all(isinstance(v, (int, float)) for v in values):
            min_val, max_val = min(values), max(values)
            if max_val > min_val:
                normalized = [(v - min_val) / (max_val - min_val) for v in values]
                sizes = [100 + 400 * n * scale_factor for n in normalized]
            else:
                sizes = [300 * scale_factor] * len(values)
        else:
            sizes = [300 * scale_factor] * len(values)
        
        return sizes
    
    def _get_node_colors(self, G, color_property):
        """Get node colors based on property."""
        if not color_property:
            return 'lightblue'
        
        values = [G.nodes[node].get(color_property, '') for node in G.nodes()]
        
        if all(isinstance(v, (int, float)) for v in values):
            return values  # Numeric values for colormap
        else:
            # Categorical values
            unique_values = list(set(values))
            color_map = {val: i for i, val in enumerate(unique_values)}
            return [color_map[val] for val in values]
    
    def _get_node_colors_plotly(self, G, color_property):
        """Get node colors for Plotly."""
        if not color_property:
            return 'lightblue'
        
        values = [G.nodes[node].get(color_property, '') for node in G.nodes()]
        
        if all(isinstance(v, (int, float)) for v in values):
            return values
        else:
            unique_values = list(set(values))
            color_map = {val: i for i, val in enumerate(unique_values)}
            return [color_map[val] for val in values]
    
    def _get_edge_widths(self, G, width_property):
        """Get edge widths based on property."""
        if not width_property:
            return [1.0] * len(G.edges())
        
        widths = []
        values = [G[u][v].get(width_property, 1) for u, v in G.edges()]
        
        if all(isinstance(v, (int, float)) for v in values):
            min_val, max_val = min(values), max(values)
            if max_val > min_val:
                normalized = [(v - min_val) / (max_val - min_val) for v in values]
                widths = [0.5 + 3 * n for n in normalized]
            else:
                widths = [1.0] * len(values)
        else:
            widths = [1.0] * len(values)
        
        return widths
    
    def _add_matplotlib_legend(self, ax, G, property_name):
        """Add legend for matplotlib plot."""
        values = [G.nodes[node].get(property_name, '') for node in G.nodes()]
        unique_values = list(set(values))
        
        if len(unique_values) <= 10:  # Only show legend for reasonable number of categories
            colors = plt.cm.Set3(range(len(unique_values)))
            legend_elements = [patches.Patch(color=colors[i], label=str(val)) 
                             for i, val in enumerate(unique_values)]
            ax.legend(handles=legend_elements, title=property_name, 
                     loc='upper left', bbox_to_anchor=(1, 1))
    
    def plot_query_result(self, query: str, **plot_kwargs):
        """
        Visualize the subgraph returned by a query.
        
        Args:
            query: Cypher query to execute
            **plot_kwargs: Arguments passed to plot()
        """
        # Execute query to get relevant nodes and relationships
        result = self.graph_db.execute(query)
        
        # Extract node and relationship IDs from result
        node_ids = set()
        rel_ids = set()
        
        for record in result:
            for key, value in record.items():
                if isinstance(value, dict):
                    if 'id' in value and 'labels' in value:  # Node
                        node_ids.add(value['id'])
                    elif 'id' in value and 'source' in value and 'target' in value:  # Relationship
                        rel_ids.add(value['id'])
                        node_ids.add(value['source'])
                        node_ids.add(value['target'])
        
        # Create temporary database with filtered data
        temp_viz = SubgraphVisualizer(self.graph_db, node_ids, rel_ids)
        return temp_viz.plot(**plot_kwargs)
    
    def plot_path(self, start_node_id: int, end_node_id: int, 
                  relationship_type: Optional[str] = None, max_hops: int = 5,
                  **plot_kwargs):
        """
        Visualize paths between two nodes.
        
        Args:
            start_node_id: Starting node ID
            end_node_id: Ending node ID  
            relationship_type: Optional relationship type filter
            max_hops: Maximum number of hops to search
            **plot_kwargs: Arguments passed to plot()
        """
        # Build query to find paths
        rel_pattern = f"[:{relationship_type}*1..{max_hops}]" if relationship_type else f"[*1..{max_hops}]"
        query = f"""
        MATCH path = (start)-{rel_pattern}->(end)
        WHERE ID(start) = {start_node_id} AND ID(end) = {end_node_id}
        RETURN path
        """
        
        return self.plot_query_result(query, **plot_kwargs)


class SubgraphVisualizer(GraphVisualizer):
    """Visualizer for a subgraph (filtered nodes and relationships)."""
    
    def __init__(self, graph_db, node_ids: set, rel_ids: set):
        """Initialize with filtered node and relationship IDs."""
        super().__init__(graph_db)
        self.node_ids = node_ids
        self.rel_ids = rel_ids
    
    def _create_networkx_graph(self):
        """Create NetworkX graph from filtered data."""
        if not HAS_NETWORKX:
            raise ImportError("NetworkX is required")
        
        G = nx.DiGraph()
        
        # Add filtered nodes
        all_nodes = self.graph_db.find_nodes()
        for node in all_nodes:
            if node['id'] in self.node_ids:
                labels = node.get('labels', [])
                props = node.get('properties', {})
                
                label = None
                for prop_name in ['name', 'title', 'id', 'label']:
                    if prop_name in props:
                        label = str(props[prop_name])
                        break
                
                if not label:
                    label = f"{':'.join(labels) if labels else 'Node'}({node['id']})"
                
                G.add_node(node['id'], 
                          label=label,
                          labels=labels,
                          **props)
        
        # Add filtered relationships
        all_rels = self.graph_db.find_relationships()
        for rel in all_rels:
            if (rel['id'] in self.rel_ids or 
                (rel['source'] in self.node_ids and rel['target'] in self.node_ids)):
                G.add_edge(rel['source'], rel['target'],
                          type=rel['type'],
                          label=rel['type'],
                          **rel.get('properties', {}))
        
        return G


def install_dependencies():
    """Print installation instructions for visualization dependencies."""
    print("Graph Visualization Dependencies")
    print("=" * 40)
    print()
    print("To use graph visualization features, install one or more of these packages:")
    print()
    print("For static plots (matplotlib + networkx):")
    print("  pip install matplotlib networkx")
    print()
    print("For interactive plots (plotly):")
    print("  pip install plotly")
    print()
    print("For publication-quality plots (graphviz):")
    print("  pip install graphviz")
    print("  # Also install system graphviz: brew install graphviz (macOS) or apt-get install graphviz (Ubuntu)")
    print()
    print("For all visualization features:")
    print("  pip install matplotlib networkx plotly graphviz")
