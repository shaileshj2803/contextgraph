"""
Tests for the GraphDB class.
"""

import pytest
import tempfile
import os

from contextgraph import GraphDB
from contextgraph.exceptions import (
    NodeNotFoundError,
    RelationshipNotFoundError,
    CypherSyntaxError
)

class TestGraphDB:
    """Test cases for GraphDB class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.db = GraphDB()

    def test_initialization(self):
        """Test GraphDB initialization."""
        assert self.db.is_directed is True
        assert self.db.node_count == 0
        assert self.db.relationship_count == 0

    def test_initialization_undirected(self):
        """Test GraphDB initialization with undirected graph."""
        db = GraphDB(directed=False)
        assert db.is_directed is False

    def test_create_node_basic(self):
        """Test basic node creation."""
        node_id = self.db.create_node()
        assert isinstance(node_id, int)
        assert self.db.node_count == 1

    def test_create_node_with_labels(self):
        """Test node creation with labels."""
        node_id = self.db.create_node(labels=["Person", "Employee"])
        node = self.db.get_node(node_id)

        assert node is not None
        assert node["labels"] == ["Person", "Employee"]
        assert node["id"] == node_id

    def test_create_node_with_properties(self):
        """Test node creation with properties."""
        properties = {"name": "Alice", "age": 30}
        node_id = self.db.create_node(properties=properties)
        node = self.db.get_node(node_id)

        assert node is not None
        assert node["properties"] == properties

    def test_create_node_with_labels_and_properties(self):
        """Test node creation with both labels and properties."""
        labels = ["Person"]
        properties = {"name": "Bob", "age": 25}
        node_id = self.db.create_node(labels=labels, properties=properties)
        node = self.db.get_node(node_id)

        assert node is not None
        assert node["labels"] == labels
        assert node["properties"] == properties

    def test_get_node_nonexistent(self):
        """Test getting a non - existent node."""
        node = self.db.get_node(999)
        assert node is None

    def test_create_relationship_basic(self):
        """Test basic relationship creation."""
        node1_id = self.db.create_node()
        node2_id = self.db.create_node()

        rel_id = self.db.create_relationship(node1_id, node2_id, "KNOWS")
        assert isinstance(rel_id, int)
        assert self.db.relationship_count == 1

    def test_create_relationship_with_properties(self):
        """Test relationship creation with properties."""
        node1_id = self.db.create_node()
        node2_id = self.db.create_node()
        properties = {"since": "2020", "strength": 0.8}

        rel_id = self.db.create_relationship(
            node1_id, node2_id, "KNOWS", properties)
        rel = self.db.get_relationship(rel_id)

        assert rel is not None
        assert rel["type"] == "KNOWS"
        assert rel["properties"] == properties
        assert rel["source"] == node1_id
        assert rel["target"] == node2_id

    def test_create_relationship_invalid_nodes(self):
        """Test relationship creation with invalid nodes."""
        with pytest.raises(NodeNotFoundError):
            self.db.create_relationship(999, 888, "KNOWS")

    def test_get_relationship_nonexistent(self):
        """Test getting a non - existent relationship."""
        rel = self.db.get_relationship(999)
        assert rel is None

    def test_delete_node(self):
        """Test node deletion."""
        node_id = self.db.create_node()
        assert self.db.node_count == 1

        result = self.db.delete_node(node_id)
        assert result is True
        assert self.db.node_count == 0
        assert self.db.get_node(node_id) is None

    def test_delete_node_nonexistent(self):
        """Test deleting a non - existent node."""
        result = self.db.delete_node(999)
        assert result is False

    def test_delete_node_with_relationships(self):
        """Test that deleting a node also deletes its relationships."""
        node1_id = self.db.create_node()
        node2_id = self.db.create_node()
        rel_id = self.db.create_relationship(node1_id, node2_id, "KNOWS")

        assert self.db.relationship_count == 1

        self.db.delete_node(node1_id)
        assert self.db.node_count == 1
        assert self.db.relationship_count == 0
        assert self.db.get_relationship(rel_id) is None

    def test_delete_relationship(self):
        """Test relationship deletion."""
        node1_id = self.db.create_node()
        node2_id = self.db.create_node()
        rel_id = self.db.create_relationship(node1_id, node2_id, "KNOWS")

        assert self.db.relationship_count == 1

        result = self.db.delete_relationship(rel_id)
        assert result is True
        assert self.db.relationship_count == 0
        assert self.db.get_relationship(rel_id) is None

    def test_delete_relationship_nonexistent(self):
        """Test deleting a non - existent relationship."""
        result = self.db.delete_relationship(999)
        assert result is False

    def test_find_nodes_by_labels(self):
        """Test finding nodes by labels."""
        node1_id = self.db.create_node(labels=["Person"])
        node2_id = self.db.create_node(labels=["Person", "Employee"])
        node3_id = self.db.create_node(labels=["Company"])

        # Find nodes with Person label
        person_nodes = self.db.find_nodes(labels=["Person"])
        assert len(person_nodes) == 2

        node_ids = [node["id"] for node in person_nodes]
        assert node1_id in node_ids
        assert node2_id in node_ids
        assert node3_id not in node_ids

    def test_find_nodes_by_properties(self):
        """Test finding nodes by properties."""
        node1_id = self.db.create_node(properties={"name": "Alice", "age": 30})
        node2_id = self.db.create_node(properties={"name": "Bob", "age": 30})
        node3_id = self.db.create_node(properties={"name": "Charlie", "age": 25})

        # Find nodes with age 30
        age_30_nodes = self.db.find_nodes(properties={"age": 30})
        assert len(age_30_nodes) == 2

        node_ids = [node["id"] for node in age_30_nodes]
        assert node1_id in node_ids
        assert node2_id in node_ids
        assert node3_id not in node_ids

    def test_find_nodes_by_labels_and_properties(self):
        """Test finding nodes by both labels and properties."""
        node1_id = self.db.create_node(
            labels=["Person"], properties={"age": 30})
        node2_id = self.db.create_node(
            labels=["Person"], properties={"age": 25})
        node3_id = self.db.create_node(
            labels=["Company"], properties={"age": 30})

        # Find Person nodes with age 30
        matching_nodes = self.db.find_nodes(
            labels=["Person"], properties={"age": 30})
        assert len(matching_nodes) == 1
        assert matching_nodes[0]["id"] == node1_id

    def test_find_relationships_by_type(self):
        """Test finding relationships by type."""
        node1_id = self.db.create_node()
        node2_id = self.db.create_node()
        node3_id = self.db.create_node()

        knows_rel_id = self.db.create_relationship(node1_id, node2_id, "KNOWS")
        self.db.create_relationship(node1_id, node3_id, "WORKS_WITH")

        # Find KNOWS relationships
        knows_rels = self.db.find_relationships(rel_type="KNOWS")
        assert len(knows_rels) == 1
        assert knows_rels[0]["id"] == knows_rel_id

    def test_find_relationships_by_properties(self):
        """Test finding relationships by properties."""
        node1_id = self.db.create_node()
        node2_id = self.db.create_node()
        node3_id = self.db.create_node()

        rel1_id = self.db.create_relationship(
            node1_id, node2_id, "KNOWS", {"strength": "strong"})
        rel2_id = self.db.create_relationship(
            node1_id, node3_id, "KNOWS", {"strength": "weak"})

        # Find strong relationships
        strong_rels = self.db.find_relationships(
            properties={"strength": "strong"})
        assert len(strong_rels) == 1
        assert strong_rels[0]["id"] == rel1_id

    def test_clear(self):
        """Test clearing the graph."""
        self.db.create_node()
        self.db.create_node()
        node1_id = self.db.create_node()
        node2_id = self.db.create_node()
        self.db.create_relationship(node1_id, node2_id, "KNOWS")

        assert self.db.node_count == 4
        assert self.db.relationship_count == 1

        self.db.clear()

        assert self.db.node_count == 0
        assert self.db.relationship_count == 0

    def test_save_and_load(self):
        """Test saving and loading the database."""
        # Create some data
        node1_id = self.db.create_node(
            labels=["Person"], properties={"name": "Alice"})
        node2_id = self.db.create_node(
            labels=["Person"], properties={"name": "Bob"})
        rel_id = self.db.create_relationship(
            node1_id, node2_id, "KNOWS", {"since": "2020"})

        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            self.db.save(temp_path)

            # Create new database and load
            new_db = GraphDB()
            new_db.load(temp_path)

            # Verify data
            assert new_db.node_count == 2
            assert new_db.relationship_count == 1

            # Check nodes
            alice_nodes = new_db.find_nodes(properties={"name": "Alice"})
            assert len(alice_nodes) == 1
            assert alice_nodes[0]["labels"] == ["Person"]

            bob_nodes = new_db.find_nodes(properties={"name": "Bob"})
            assert len(bob_nodes) == 1
            assert bob_nodes[0]["labels"] == ["Person"]

            # Check relationship
            knows_rels = new_db.find_relationships(rel_type="KNOWS")
            assert len(knows_rels) == 1
            assert knows_rels[0]["properties"] == {"since": "2020"}

        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_get_igraph(self):
        """Test getting the underlying igraph object."""
        igraph_obj = self.db.get_igraph()
        assert hasattr(igraph_obj, 'vcount')
        assert hasattr(igraph_obj, 'ecount')
        assert igraph_obj.vcount() == 0
        assert igraph_obj.ecount() == 0
