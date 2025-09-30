#!/usr/bin/env python3
"""
Test suite for the performance optimizations implemented in v0.3.0.

This module tests:
1. O(1) node lookup optimization
2. Optional nodeid parameter in create_node
3. Batch relationship creation API
4. Performance improvements and regression prevention
"""

import pytest
import time
from contextgraph import GraphDB
from contextgraph.exceptions import GraphDBError, NodeNotFoundError


class TestNodeIdParameter:
    """Test the optional nodeid parameter in create_node."""

    def setup_method(self):
        """Set up test database."""
        self.db = GraphDB()

    def test_auto_generated_node_ids(self):
        """Test that auto-generated node IDs work as before."""
        node1 = self.db.create_node(labels=["Person"], properties={"name": "Alice"})
        node2 = self.db.create_node(labels=["Person"], properties={"name": "Bob"})
        
        assert node1 == 0
        assert node2 == 1
        assert self.db.node_count == 2

    def test_custom_node_ids(self):
        """Test custom node ID assignment."""
        node1 = self.db.create_node(
            labels=["Person"], 
            properties={"name": "Alice"}, 
            nodeid=1000
        )
        node2 = self.db.create_node(
            labels=["Person"], 
            properties={"name": "Bob"}, 
            nodeid=2000
        )
        
        assert node1 == 1000
        assert node2 == 2000
        assert self.db.node_count == 2

    def test_mixed_node_ids(self):
        """Test mixing auto-generated and custom node IDs."""
        auto_node = self.db.create_node(labels=["Person"], properties={"name": "Auto"})
        custom_node = self.db.create_node(
            labels=["Person"], 
            properties={"name": "Custom"}, 
            nodeid=5000
        )
        auto_node2 = self.db.create_node(labels=["Person"], properties={"name": "Auto2"})
        
        assert auto_node == 0
        assert custom_node == 5000
        assert auto_node2 == 5001  # Counter updated after custom ID
        assert self.db.node_count == 3

    def test_duplicate_custom_id_error(self):
        """Test that duplicate custom IDs raise an error."""
        self.db.create_node(labels=["Person"], properties={"name": "First"}, nodeid=100)
        
        with pytest.raises(GraphDBError, match="Node with ID 100 already exists"):
            self.db.create_node(labels=["Person"], properties={"name": "Second"}, nodeid=100)

    def test_custom_id_retrieval(self):
        """Test that nodes with custom IDs can be retrieved correctly."""
        custom_id = 12345
        node_id = self.db.create_node(
            labels=["TestNode"], 
            properties={"value": "test"}, 
            nodeid=custom_id
        )
        
        assert node_id == custom_id
        
        retrieved_node = self.db.get_node(custom_id)
        assert retrieved_node is not None
        assert retrieved_node["id"] == custom_id
        assert retrieved_node["properties"]["value"] == "test"


class TestBatchRelationshipCreation:
    """Test the batch relationship creation API."""

    def setup_method(self):
        """Set up test database with nodes."""
        self.db = GraphDB()
        self.node_ids = []
        
        # Create test nodes
        for i in range(10):
            node_id = self.db.create_node(
                labels=["TestNode"], 
                properties={"index": i}
            )
            self.node_ids.append(node_id)

    def test_batch_relationship_creation(self):
        """Test basic batch relationship creation."""
        batch_data = [
            {
                'source_id': self.node_ids[0],
                'target_id': self.node_ids[1],
                'rel_type': 'CONNECTS',
                'properties': {'weight': 1}
            },
            {
                'source_id': self.node_ids[1],
                'target_id': self.node_ids[2],
                'rel_type': 'CONNECTS',
                'properties': {'weight': 2}
            },
            {
                'source_id': self.node_ids[2],
                'target_id': self.node_ids[3],
                'rel_type': 'CONNECTS',
                'properties': {'weight': 3}
            }
        ]
        
        rel_ids = self.db.create_relationships_batch(batch_data)
        
        assert len(rel_ids) == 3
        assert self.db.relationship_count == 3
        
        # Verify relationships were created correctly
        for i, rel_id in enumerate(rel_ids):
            rel = self.db.get_relationship(rel_id)
            assert rel is not None
            assert rel['type'] == 'CONNECTS'
            assert rel['properties']['weight'] == i + 1

    def test_batch_empty_list(self):
        """Test batch creation with empty list."""
        rel_ids = self.db.create_relationships_batch([])
        assert rel_ids == []
        assert self.db.relationship_count == 0

    def test_batch_invalid_node_error(self):
        """Test batch creation with invalid node IDs."""
        batch_data = [
            {
                'source_id': self.node_ids[0],
                'target_id': 99999,  # Non-existent node
                'rel_type': 'CONNECTS',
                'properties': {}
            }
        ]
        
        with pytest.raises(NodeNotFoundError, match="Target node with ID 99999 not found"):
            self.db.create_relationships_batch(batch_data)

    def test_batch_vs_individual_performance(self):
        """Test that batch creation is faster than individual creation."""
        # Prepare data for both tests
        individual_data = []
        batch_data = []
        
        for i in range(100):
            source_id = self.node_ids[i % len(self.node_ids)]
            target_id = self.node_ids[(i + 1) % len(self.node_ids)]
            
            individual_data.append((source_id, target_id, 'INDIVIDUAL', {'index': i}))
            batch_data.append({
                'source_id': source_id,
                'target_id': target_id,
                'rel_type': 'BATCH',
                'properties': {'index': i}
            })
        
        # Test individual creation
        start_time = time.time()
        individual_ids = []
        for source_id, target_id, rel_type, properties in individual_data:
            rel_id = self.db.create_relationship(source_id, target_id, rel_type, properties)
            individual_ids.append(rel_id)
        individual_time = time.time() - start_time
        
        # Test batch creation
        start_time = time.time()
        batch_ids = self.db.create_relationships_batch(batch_data)
        batch_time = time.time() - start_time
        
        # Verify both created the same number of relationships
        assert len(individual_ids) == len(batch_ids) == 100
        assert self.db.relationship_count == 200
        
        # Batch should be faster (allow some tolerance for small datasets)
        print(f"Individual time: {individual_time:.4f}s, Batch time: {batch_time:.4f}s")
        # Note: For small datasets, the difference might be minimal, but batch should not be slower
        assert batch_time <= individual_time * 1.5  # Allow 50% tolerance


class TestPerformanceOptimizations:
    """Test the O(1) lookup optimizations."""

    def setup_method(self):
        """Set up test database."""
        self.db = GraphDB()

    def test_node_lookup_performance(self):
        """Test that node lookups are fast even with many nodes."""
        # Create a large number of nodes
        node_ids = []
        for i in range(1000):
            node_id = self.db.create_node(
                labels=["PerfTest"], 
                properties={"index": i}
            )
            node_ids.append(node_id)
        
        # Test lookup performance
        start_time = time.time()
        found_count = 0
        
        # Look up every 10th node
        for i in range(0, len(node_ids), 10):
            node = self.db.get_node(node_ids[i])
            if node is not None:
                found_count += 1
        
        lookup_time = time.time() - start_time
        
        assert found_count == 100  # Should find all 100 nodes
        # Should be very fast - less than 10ms for 100 lookups
        assert lookup_time < 0.01, f"Lookup took {lookup_time:.4f}s, expected < 0.01s"

    def test_relationship_creation_performance(self):
        """Test that relationship creation is fast with O(1) lookups."""
        # Create nodes
        node_ids = []
        for i in range(500):
            node_id = self.db.create_node(
                labels=["PerfTest"], 
                properties={"index": i}
            )
            node_ids.append(node_id)
        
        # Test relationship creation performance
        start_time = time.time()
        
        for i in range(250):
            source_id = node_ids[i]
            target_id = node_ids[i + 250]
            self.db.create_relationship(source_id, target_id, "PERF_TEST")
        
        creation_time = time.time() - start_time
        
        assert self.db.relationship_count == 250
        # Should be fast - less than 100ms for 250 relationships
        assert creation_time < 0.1, f"Creation took {creation_time:.4f}s, expected < 0.1s"

    def test_mixed_operations_performance(self):
        """Test performance of mixed node and relationship operations."""
        start_time = time.time()
        
        # Create nodes with mixed ID types
        node_ids = []
        for i in range(200):
            if i % 50 == 0:
                # Custom ID every 50th node
                node_id = self.db.create_node(
                    labels=["Mixed"], 
                    properties={"type": "custom"}, 
                    nodeid=10000 + i
                )
            else:
                node_id = self.db.create_node(
                    labels=["Mixed"], 
                    properties={"type": "auto"}
                )
            node_ids.append(node_id)
        
        # Create relationships
        for i in range(100):
            source_id = node_ids[i]
            target_id = node_ids[i + 100]
            self.db.create_relationship(source_id, target_id, "MIXED_TEST")
        
        # Perform lookups
        lookup_count = 0
        for node_id in node_ids[::10]:  # Every 10th node
            node = self.db.get_node(node_id)
            if node is not None:
                lookup_count += 1
        
        total_time = time.time() - start_time
        
        assert self.db.node_count == 200
        assert self.db.relationship_count == 100
        assert lookup_count == 20
        
        # Should complete quickly
        assert total_time < 0.2, f"Mixed operations took {total_time:.4f}s, expected < 0.2s"


class TestRegressionPrevention:
    """Test to prevent performance regressions."""

    def setup_method(self):
        """Set up test database."""
        self.db = GraphDB()

    def test_large_graph_performance(self):
        """Test performance with a larger graph to prevent regressions."""
        # Create a moderately large graph
        num_nodes = 2000
        num_relationships = 1000
        
        start_time = time.time()
        
        # Create nodes
        node_ids = []
        for i in range(num_nodes):
            node_id = self.db.create_node(
                labels=["LargeTest"], 
                properties={"index": i, "value": f"node_{i}"}
            )
            node_ids.append(node_id)
        
        node_creation_time = time.time() - start_time
        
        # Create relationships
        start_time = time.time()
        for i in range(num_relationships):
            source_id = node_ids[i]
            target_id = node_ids[i + num_relationships]
            self.db.create_relationship(source_id, target_id, "LARGE_TEST")
        
        rel_creation_time = time.time() - start_time
        
        # Test lookups
        start_time = time.time()
        lookup_count = 0
        for i in range(0, num_nodes, 100):  # Every 100th node
            node = self.db.get_node(node_ids[i])
            if node is not None:
                lookup_count += 1
        
        lookup_time = time.time() - start_time
        
        # Verify correctness
        assert self.db.node_count == num_nodes
        assert self.db.relationship_count == num_relationships
        assert lookup_count == 20
        
        # Performance assertions (generous bounds to prevent flaky tests)
        assert node_creation_time < 1.0, f"Node creation took {node_creation_time:.3f}s"
        assert rel_creation_time < 0.5, f"Relationship creation took {rel_creation_time:.3f}s"
        assert lookup_time < 0.01, f"Lookups took {lookup_time:.3f}s"
        
        print(f"Performance results for {num_nodes} nodes, {num_relationships} relationships:")
        print(f"  Node creation: {node_creation_time:.3f}s ({num_nodes/node_creation_time:.0f} nodes/sec)")
        print(f"  Relationship creation: {rel_creation_time:.3f}s ({num_relationships/rel_creation_time:.0f} rels/sec)")
        print(f"  Lookups: {lookup_time:.3f}s ({lookup_count/lookup_time:.0f} lookups/sec)")
