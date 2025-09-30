"""
Core GraphDB class implementation using igraph as the backend.
"""

import json
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import igraph as ig

from .exceptions import (
    GraphDBError,
    NodeNotFoundError,
    RelationshipNotFoundError,
    PropertyError,
)
from .cypher_parser import CypherParser
from .query_result import QueryResult
from .transaction import TransactionManager
from .csv_importer import CSVImporter

class GraphDB:
    """
    An embedded graph database using igraph with Cypher query support.

    This class provides a graph database interface that uses igraph as the
    underlying graph structure and supports Cypher queries for data manipulation
    and retrieval.
    """

    def __init__(self, directed: bool = True):
        """
        Initialize a new GraphDB instance.

        Args:
            directed: Whether the graph should be directed (default: True)
        """
        self._graph = ig.Graph(directed=directed)
        self._cypher_parser = CypherParser(self)
        self._node_id_counter = 0
        self._relationship_id_counter = 0
        self.transaction_manager = TransactionManager(self)
        self.csv_importer = CSVImporter(self)
        
        # Performance optimization: O(1) lookup for node ID to vertex index
        self._node_id_to_vertex_index: Dict[int, int] = {}

        # Initialize vertex and edge attributes for properties
        self._graph.vs["id"] = []
        self._graph.vs["labels"] = []
        self._graph.vs["properties"] = []
        self._graph.es["id"] = []
        self._graph.es["type"] = []
        self._graph.es["properties"] = []

    @property
    def is_directed(self) -> bool:
        """Return whether the graph is directed."""
        return self._graph.is_directed()

    @property
    def node_count(self) -> int:
        """Return the number of nodes in the graph."""
        return self._graph.vcount()

    @property
    def relationship_count(self) -> int:
        """Return the number of relationships in the graph."""
        return self._graph.ecount()

    def execute(self, cypher_query: str, parameters: Optional[Dict[str, Any]] = None) -> QueryResult:
        """
        Execute a Cypher query against the graph database.

        Args:
            cypher_query: The Cypher query string to execute
            parameters: Optional parameters to substitute in the query

        Returns:
            QueryResult: The result of the query execution

        Raises:
            CypherSyntaxError: If the query has syntax errors
            GraphDBError: If there's an error during query execution
        """
        if parameters is None:
            parameters = {}

        return self._cypher_parser.parse_and_execute(cypher_query, parameters)

    def create_node(self, labels: Optional[List[str]] = None,
                    properties: Optional[Dict[str, Any]] = None,
                    nodeid: Optional[int] = None) -> int:
        """
        Create a new node in the graph.

        Args:
            labels: List of labels for the node
            properties: Dictionary of properties for the node
            nodeid: Optional specific node ID to use (if None, auto-generates)

        Returns:
            int: The internal node ID
            
        Raises:
            GraphDBError: If the specified nodeid already exists
        """
        if labels is None:
            labels = []
        if properties is None:
            properties = {}

        # Handle optional nodeid parameter
        if nodeid is not None:
            if nodeid in self._node_id_to_vertex_index:
                raise GraphDBError(f"Node with ID {nodeid} already exists")
            node_id = nodeid
            # Update counter if necessary to avoid conflicts
            if nodeid >= self._node_id_counter:
                self._node_id_counter = nodeid + 1
        else:
            node_id = self._node_id_counter
            self._node_id_counter += 1

        # Add vertex to igraph
        self._graph.add_vertex()
        vertex_index = self._graph.vcount() - 1

        # Set attributes
        self._graph.vs[vertex_index]["id"] = node_id
        self._graph.vs[vertex_index]["labels"] = labels
        self._graph.vs[vertex_index]["properties"] = properties
        
        # Update O(1) lookup table
        self._node_id_to_vertex_index[node_id] = vertex_index

        return node_id

    def create_relationship(self, source_id: int, target_id: int,
                            rel_type: str,
                            properties: Optional[Dict[str, Any]] = None) -> int:
        """
        Create a new relationship between two nodes.

        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            rel_type: Type / label of the relationship
            properties: Dictionary of properties for the relationship

        Returns:
            int: The internal relationship ID

        Raises:
            NodeNotFoundError: If either source or target node doesn't exist
        """
        if properties is None:
            properties = {}

        # Optimized O(1) vertex lookup using hash map
        source_vertex_index = self._node_id_to_vertex_index.get(source_id)
        target_vertex_index = self._node_id_to_vertex_index.get(target_id)

        if source_vertex_index is None:
            raise NodeNotFoundError(f"Source node with ID {source_id} not found")
        if target_vertex_index is None:
            raise NodeNotFoundError(f"Target node with ID {target_id} not found")

        relationship_id = self._relationship_id_counter
        self._relationship_id_counter += 1

        # Add edge to igraph using vertex indices directly
        self._graph.add_edge(source_vertex_index, target_vertex_index)
        edge_index = self._graph.ecount() - 1

        # Set attributes
        self._graph.es[edge_index]["id"] = relationship_id
        self._graph.es[edge_index]["type"] = rel_type
        self._graph.es[edge_index]["properties"] = properties

        return relationship_id

    def create_relationships_batch(
            self,
            relationships: List[Dict[str, Any]]
    ) -> List[int]:
        """
        Create multiple relationships in a batch for better performance.

        Args:
            relationships: List of relationship dictionaries, each containing:
                - source_id: ID of the source node
                - target_id: ID of the target node
                - rel_type: Type/label of the relationship
                - properties: Optional dictionary of properties

        Returns:
            List[int]: List of created relationship IDs

        Raises:
            NodeNotFoundError: If any source or target node doesn't exist
        """
        relationship_ids = []
        edges_to_add = []
        edge_attributes = []

        # Validate all nodes exist and prepare edge data
        for rel_data in relationships:
            source_id = rel_data['source_id']
            target_id = rel_data['target_id']
            rel_type = rel_data['rel_type']
            properties = rel_data.get('properties', {})

            # Optimized O(1) vertex lookup
            source_vertex_index = self._node_id_to_vertex_index.get(source_id)
            target_vertex_index = self._node_id_to_vertex_index.get(target_id)

            if source_vertex_index is None:
                raise NodeNotFoundError(
                    f"Source node with ID {source_id} not found")
            if target_vertex_index is None:
                raise NodeNotFoundError(
                    f"Target node with ID {target_id} not found")

            relationship_id = self._relationship_id_counter
            self._relationship_id_counter += 1

            edges_to_add.append((source_vertex_index, target_vertex_index))
            edge_attributes.append({
                'id': relationship_id,
                'type': rel_type,
                'properties': properties
            })
            relationship_ids.append(relationship_id)

        # Batch add all edges to igraph
        if edges_to_add:
            self._graph.add_edges(edges_to_add)

            # Set attributes for all new edges
            start_edge_index = self._graph.ecount() - len(edges_to_add)
            for i, attrs in enumerate(edge_attributes):
                edge_index = start_edge_index + i
                self._graph.es[edge_index]["id"] = attrs['id']
                self._graph.es[edge_index]["type"] = attrs['type']
                self._graph.es[edge_index]["properties"] = attrs['properties']

        return relationship_ids

    def get_node(self, node_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a node by its ID.

        Args:
            node_id: The node ID to look up

        Returns:
            Dictionary containing node data or None if not found
        """
        vertex_index = self._node_id_to_vertex_index.get(node_id)
        if vertex_index is None:
            return None

        vertex = self._graph.vs[vertex_index]
        return {
            "id": vertex["id"],
            "labels": vertex["labels"],
            "properties": vertex["properties"]
        }

    def get_relationship(self, rel_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a relationship by its ID.

        Args:
            rel_id: The relationship ID to look up

        Returns:
            Dictionary containing relationship data or None if not found
        """
        edge = self._find_edge_by_id(rel_id)
        if edge is None:
            return None

        return {
            "id": edge["id"],
            "type": edge["type"],
            "properties": edge["properties"],
            "source": self._graph.vs[edge.source]["id"],
            "target": self._graph.vs[edge.target]["id"]
        }

    def delete_node(self, node_id: int) -> bool:
        """
        Delete a node and all its relationships.

        Args:
            node_id: The node ID to delete

        Returns:
            bool: True if the node was deleted, False if not found
        """
        vertex_index = self._node_id_to_vertex_index.get(node_id)
        if vertex_index is None:
            return False

        # Remove from lookup table
        del self._node_id_to_vertex_index[node_id]
        
        # Update lookup table for vertices that will shift indices
        vertices_to_update = [(vid, idx) for vid, idx in self._node_id_to_vertex_index.items() if idx > vertex_index]
        for vid, idx in vertices_to_update:
            self._node_id_to_vertex_index[vid] = idx - 1
            
        self._graph.delete_vertices(vertex_index)
        return True

    def delete_relationship(self, rel_id: int) -> bool:
        """
        Delete a relationship.

        Args:
            rel_id: The relationship ID to delete

        Returns:
            bool: True if the relationship was deleted, False if not found
        """
        edge = self._find_edge_by_id(rel_id)
        if edge is None:
            return False

        self._graph.delete_edges(edge.index)
        return True

    def find_nodes(self, labels: Optional[List[str]] = None,
                   properties: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Find nodes matching the given criteria.

        Args:
            labels: List of labels that nodes must have
            properties: Dictionary of properties that nodes must match

        Returns:
            List of matching nodes
        """
        matching_nodes = []

        for vertex in self._graph.vs:
            # Check labels
            if labels is not None:
                vertex_labels = vertex["labels"] or []
                if not all(label in vertex_labels for label in labels):
                    continue

            # Check properties
            if properties is not None:
                vertex_props = vertex["properties"] or {}
                if not all(vertex_props.get(k) == v for k, v in properties.items()):
                    continue

            matching_nodes.append({
                "id": vertex["id"],
                "labels": vertex["labels"],
                "properties": vertex["properties"]
            })

        return matching_nodes

    def find_relationships(self, rel_type: Optional[str] = None,
                          properties: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Find relationships matching the given criteria.

        Args:
            rel_type: Type of relationships to find
            properties: Dictionary of properties that relationships must match

        Returns:
            List of matching relationships
        """
        matching_rels = []

        for edge in self._graph.es:
            # Check type
            if rel_type is not None and edge["type"] != rel_type:
                continue

            # Check properties
            if properties is not None:
                edge_props = edge["properties"] or {}
                if not all(edge_props.get(k) == v for k, v in properties.items()):
                    continue

            matching_rels.append({
                "id": edge["id"],
                "type": edge["type"],
                "properties": edge["properties"],
                "source": self._graph.vs[edge.source]["id"],
                "target": self._graph.vs[edge.target]["id"]
            })

        return matching_rels

    def save(self, filepath: Union[str, Path]) -> None:
        """
        Save the graph database to a file.

        Args:
            filepath: Path where to save the database
        """
        filepath = Path(filepath)

        # Create a serializable representation
        data = {
            "directed": self._graph.is_directed(),
            "node_id_counter": self._node_id_counter,
            "relationship_id_counter": self._relationship_id_counter,
            "nodes": [],
            "relationships": []
        }

        # Save nodes
        for vertex in self._graph.vs:
            data["nodes"].append({
                "id": vertex["id"],
                "labels": vertex["labels"],
                "properties": vertex["properties"]
            })

        # Save relationships
        for edge in self._graph.es:
            data["relationships"].append({
                "id": edge["id"],
                "type": edge["type"],
                "properties": edge["properties"],
                "source": self._graph.vs[edge.source]["id"],
                "target": self._graph.vs[edge.target]["id"]
            })

        with open(filepath, 'w', encoding='utf - 8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self, filepath: Union[str, Path]) -> None:
        """
        Load a graph database from a file.

        Args:
            filepath: Path to the database file to load
        """
        filepath = Path(filepath)

        with open(filepath, 'r', encoding='utf - 8') as f:
            data = json.load(f)

        # Recreate the graph
        self._graph = ig.Graph(directed=data["directed"])
        self._node_id_counter = data["node_id_counter"]
        self._relationship_id_counter = data["relationship_id_counter"]

        # Initialize attributes
        self._graph.vs["id"] = []
        self._graph.vs["labels"] = []
        self._graph.vs["properties"] = []
        self._graph.es["id"] = []
        self._graph.es["type"] = []
        self._graph.es["properties"] = []

        # Clear and rebuild the lookup table
        self._node_id_to_vertex_index.clear()

        # OPTIMIZED: Batch recreate nodes
        node_id_to_index = {}
        if data["nodes"]:
            # Add all vertices at once (much faster than individual add_vertex calls)
            self._graph.add_vertices(len(data["nodes"]))
            
            # Prepare batch attribute data
            node_ids = []
            node_labels = []
            node_properties = []
            
            for vertex_index, node_data in enumerate(data["nodes"]):
                node_ids.append(node_data["id"])
                node_labels.append(node_data["labels"])
                node_properties.append(node_data["properties"])
                
                node_id_to_index[node_data["id"]] = vertex_index
                # Update the optimized lookup table
                self._node_id_to_vertex_index[node_data["id"]] = vertex_index
            
            # Set all attributes at once (batch operation)
            self._graph.vs["id"] = node_ids
            self._graph.vs["labels"] = node_labels
            self._graph.vs["properties"] = node_properties

        # OPTIMIZED: Batch recreate relationships  
        if data["relationships"]:
            # Prepare edge list for batch creation
            edges_to_add = []
            rel_ids = []
            rel_types = []
            rel_properties = []
            
            for rel_data in data["relationships"]:
                source_index = node_id_to_index[rel_data["source"]]
                target_index = node_id_to_index[rel_data["target"]]
                
                edges_to_add.append((source_index, target_index))
                rel_ids.append(rel_data["id"])
                rel_types.append(rel_data["type"])
                rel_properties.append(rel_data["properties"])
            
            # Add all edges at once (much faster than individual add_edge calls)
            self._graph.add_edges(edges_to_add)
            
            # Set all edge attributes at once (batch operation)
            self._graph.es["id"] = rel_ids
            self._graph.es["type"] = rel_types
            self._graph.es["properties"] = rel_properties

    def save_pickle(self, filepath: Union[str, Path]) -> None:
        """
        Save the graph database to a pickle file for fast serialization.

        This method is significantly faster than JSON for large graphs and
        preserves Python object types perfectly (no type conversion issues).

        Args:
            filepath: Path where to save the database (will add .pkl extension if not present)

        Note:
            Pickle files are Python - specific and may not be compatible across
            different Python versions. Use save() for cross - platform compatibility.
        """
        filepath = Path(filepath)

        # Add .pkl extension if not present
        if filepath.suffix.lower() not in ['.pkl', '.pickle']:
            filepath = filepath.with_suffix('.pkl')

        # Create a complete serializable representation
        data = {
            "directed": self._graph.is_directed(),
            "node_id_counter": self._node_id_counter,
            "relationship_id_counter": self._relationship_id_counter,
            "nodes": [],
            "relationships": []
        }

        # Save nodes with full type preservation
        for vertex in self._graph.vs:
            data["nodes"].append({
                "id": vertex["id"],
                "labels": vertex["labels"],
                "properties": vertex["properties"]
            })

        # Save relationships with full type preservation
        for edge in self._graph.es:
            data["relationships"].append({
                "id": edge["id"],
                "type": edge["type"],
                "properties": edge["properties"],
                "source": self._graph.vs[edge.source]["id"],
                "target": self._graph.vs[edge.target]["id"]
            })

        # Use highest protocol for best performance and compatibility
        with open(filepath, 'wb') as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

    def load_pickle(self, filepath: Union[str, Path]) -> None:
        """
        Load a graph database from a pickle file.

        This method is significantly faster than JSON loading for large graphs
        and preserves all Python object types perfectly.

        Args:
            filepath: Path to the pickle database file to load

        Raises:
            FileNotFoundError: If the pickle file doesn't exist
            pickle.UnpicklingError: If the file is corrupted or incompatible
            GraphDBError: If there's an error during graph reconstruction
        """
        filepath = Path(filepath)

        # Try with .pkl extension if file not found
        if not filepath.exists() and filepath.suffix.lower() not in ['.pkl', '.pickle']:
            pkl_filepath = filepath.with_suffix('.pkl')
            if pkl_filepath.exists():
                filepath = pkl_filepath

        if not filepath.exists():
            raise FileNotFoundError(f"Pickle file not found: {filepath}")

        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
        except Exception as e:
            raise GraphDBError(f"Error loading pickle file: {str(e)}")

        # Recreate the graph
        self._graph = ig.Graph(directed=data["directed"])
        self._node_id_counter = data["node_id_counter"]
        self._relationship_id_counter = data["relationship_id_counter"]

        # Initialize attributes
        self._graph.vs["id"] = []
        self._graph.vs["labels"] = []
        self._graph.vs["properties"] = []
        self._graph.es["id"] = []
        self._graph.es["type"] = []
        self._graph.es["properties"] = []

        # Clear and rebuild the lookup table
        self._node_id_to_vertex_index.clear()

        # OPTIMIZED: Batch recreate nodes
        node_id_to_index = {}
        if data["nodes"]:
            # Add all vertices at once (much faster than individual add_vertex calls)
            self._graph.add_vertices(len(data["nodes"]))
            
            # Prepare batch attribute data
            node_ids = []
            node_labels = []
            node_properties = []
            
            for vertex_index, node_data in enumerate(data["nodes"]):
                node_ids.append(node_data["id"])
                node_labels.append(node_data["labels"])
                node_properties.append(node_data["properties"])
                
                node_id_to_index[node_data["id"]] = vertex_index
                # Update the optimized lookup table
                self._node_id_to_vertex_index[node_data["id"]] = vertex_index
            
            # Set all attributes at once (batch operation)
            self._graph.vs["id"] = node_ids
            self._graph.vs["labels"] = node_labels
            self._graph.vs["properties"] = node_properties

        # OPTIMIZED: Batch recreate relationships  
        if data["relationships"]:
            # Prepare edge list for batch creation
            edges_to_add = []
            rel_ids = []
            rel_types = []
            rel_properties = []
            
            for rel_data in data["relationships"]:
                source_index = node_id_to_index[rel_data["source"]]
                target_index = node_id_to_index[rel_data["target"]]
                
                edges_to_add.append((source_index, target_index))
                rel_ids.append(rel_data["id"])
                rel_types.append(rel_data["type"])
                rel_properties.append(rel_data["properties"])
            
            # Add all edges at once (much faster than individual add_edge calls)
            self._graph.add_edges(edges_to_add)
            
            # Set all edge attributes at once (batch operation)
            self._graph.es["id"] = rel_ids
            self._graph.es["type"] = rel_types
            self._graph.es["properties"] = rel_properties

    def clear(self) -> None:
        """Clear all nodes and relationships from the graph."""
        self._graph.clear()
        self._node_id_counter = 0
        self._relationship_id_counter = 0
        
        # Clear the lookup table
        self._node_id_to_vertex_index.clear()

        # Reinitialize attributes
        self._graph.vs["id"] = []
        self._graph.vs["labels"] = []
        self._graph.vs["properties"] = []
        self._graph.es["id"] = []
        self._graph.es["type"] = []
        self._graph.es["properties"] = []

    def _find_vertex_by_id(self, node_id: int) -> Optional[ig.Vertex]:
        """Find a vertex by its node ID. Optimized with O(1) lookup."""
        vertex_index = self._node_id_to_vertex_index.get(node_id)
        if vertex_index is None:
            return None
        return self._graph.vs[vertex_index]

    def _find_edge_by_id(self, rel_id: int) -> Optional[ig.Edge]:
        """Find an edge by its relationship ID."""
        for edge in self._graph.es:
            if edge["id"] == rel_id:
                return edge
        return None

    def get_igraph(self) -> ig.Graph:
        """
        Get the underlying igraph Graph object.

        Returns:
            The igraph Graph instance
        """
        return self._graph

    def import_nodes_from_csv(
        self,
        csv_file: Union[str, Path],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Import nodes from a CSV file with high performance.

        Args:
            csv_file: Path to the CSV file

        Returns:

        Example:
            ...     'people.csv',
            ...     id_column='person_id',
            ...     label_column='type',
            ...     labels=['Person']
            ... )
        """
        return self.csv_importer.import_nodes_from_csv(csv_file, **kwargs)

    def import_relationships_from_csv(
        self,
        csv_file: Union[str, Path],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Import relationships from a CSV file with high performance.

        Args:
            csv_file: Path to the CSV file

        Returns:

        Example:
            ...     'friendships.csv',
            ...     source_column='person1_id',
            ...     target_column='person2_id',
            ...     relationship_type='FRIENDS_WITH'
            ... )
        """
        return self.csv_importer.import_relationships_from_csv(csv_file, **kwargs)
    
    def visualize(self, **kwargs):
        """
        Create a visualization of the graph.
        
        This is a convenience method that creates a GraphVisualizer instance
        and calls plot() with the provided arguments.
        
        Args:
            **kwargs: Arguments passed to GraphVisualizer.plot()
            
        Returns:
            Visualization object (depends on backend)
            
        Example:
            >>> db = GraphDB()
            >>> # ... add nodes and relationships ...
            >>> db.visualize(backend='plotly', layout='spring', node_labels=True)
        """
        from .visualization import GraphVisualizer
        visualizer = GraphVisualizer(self)
        return visualizer.plot(**kwargs)
