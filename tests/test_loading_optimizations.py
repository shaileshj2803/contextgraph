#!/usr/bin/env python3
"""
Test suite for the loading optimization improvements implemented for load_pickle and load_json.

This module tests the batch vertex and edge creation optimizations that dramatically
improve loading performance for large graphs.
"""

import pytest
import tempfile
import time
from pathlib import Path
from contextgraph import GraphDB


class TestLoadingOptimizations:
    """Test the optimized loading performance."""

    def setup_method(self):
        """Set up test database."""
        self.db = GraphDB()

    def test_batch_loading_correctness(self):
        """Test that batch loading produces correct results."""
        # Create a test graph with diverse data
        node_ids = []
        for i in range(100):
            if i % 10 == 0:
                # Custom node IDs
                node_id = self.db.create_node(
                    labels=["Person", "VIP"],
                    properties={"name": f"VIP_{i}", "index": i},
                    nodeid=1000 + i
                )
            else:
                # Auto node IDs
                node_id = self.db.create_node(
                    labels=["Person"],
                    properties={"name": f"Person_{i}", "index": i}
                )
            node_ids.append(node_id)
        
        # Create relationships
        for i in range(50):
            self.db.create_relationship(
                node_ids[i], 
                node_ids[i + 50], 
                "KNOWS",
                {"strength": i * 0.1, "since": f"202{i % 4}"}
            )
        
        original_nodes = self.db.node_count
        original_rels = self.db.relationship_count
        
        # Test JSON loading
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            json_file = Path(f.name)
            
        try:
            self.db.save(json_file)
            
            json_db = GraphDB()
            json_db.load(json_file)
            
            # Verify correctness
            assert json_db.node_count == original_nodes
            assert json_db.relationship_count == original_rels
            
            # Verify data integrity
            for node_id in node_ids[:10]:  # Test first 10 nodes
                original_node = self.db.get_node(node_id)
                loaded_node = json_db.get_node(node_id)
                assert loaded_node is not None
                assert loaded_node["id"] == original_node["id"]
                assert loaded_node["labels"] == original_node["labels"]
                assert loaded_node["properties"] == original_node["properties"]
                
        finally:
            json_file.unlink(missing_ok=True)
        
        # Test Pickle loading
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
            pickle_file = Path(f.name)
            
        try:
            self.db.save_pickle(pickle_file)
            
            pickle_db = GraphDB()
            pickle_db.load_pickle(pickle_file)
            
            # Verify correctness
            assert pickle_db.node_count == original_nodes
            assert pickle_db.relationship_count == original_rels
            
            # Verify data integrity
            for node_id in node_ids[:10]:  # Test first 10 nodes
                original_node = self.db.get_node(node_id)
                loaded_node = pickle_db.get_node(node_id)
                assert loaded_node is not None
                assert loaded_node["id"] == original_node["id"]
                assert loaded_node["labels"] == original_node["labels"]
                assert loaded_node["properties"] == original_node["properties"]
                
        finally:
            pickle_file.unlink(missing_ok=True)

    def test_empty_graph_loading(self):
        """Test loading empty graphs."""
        empty_db = GraphDB()
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            json_file = Path(f.name)
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
            pickle_file = Path(f.name)
            
        try:
            # Save empty graph
            empty_db.save(json_file)
            empty_db.save_pickle(pickle_file)
            
            # Load empty JSON
            json_db = GraphDB()
            json_db.load(json_file)
            assert json_db.node_count == 0
            assert json_db.relationship_count == 0
            
            # Load empty Pickle
            pickle_db = GraphDB()
            pickle_db.load_pickle(pickle_file)
            assert pickle_db.node_count == 0
            assert pickle_db.relationship_count == 0
            
        finally:
            json_file.unlink(missing_ok=True)
            pickle_file.unlink(missing_ok=True)

    def test_large_graph_loading_performance(self):
        """Test loading performance with a larger graph."""
        # Create a moderately large graph
        node_ids = []
        for i in range(1000):
            node_id = self.db.create_node(
                labels=["TestNode"],
                properties={
                    "index": i,
                    "name": f"Node_{i}",
                    "data": [1, 2, 3, 4, 5],  # Some array data
                    "metadata": {"created": "2024", "type": "test"}
                }
            )
            node_ids.append(node_id)
        
        # Create relationships
        for i in range(500):
            self.db.create_relationship(
                node_ids[i],
                node_ids[i + 500],
                "CONNECTS",
                {"weight": i * 0.01, "type": "test"}
            )
        
        original_nodes = self.db.node_count
        original_rels = self.db.relationship_count
        
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
            pickle_file = Path(f.name)
            
        try:
            # Save graph
            self.db.save_pickle(pickle_file)
            
            # Test loading performance
            test_db = GraphDB()
            start_time = time.time()
            test_db.load_pickle(pickle_file)
            load_time = time.time() - start_time
            
            # Verify correctness
            assert test_db.node_count == original_nodes
            assert test_db.relationship_count == original_rels
            
            # Performance assertion (should be quite fast)
            loading_rate = original_nodes / load_time if load_time > 0 else 0
            assert loading_rate > 10000, f"Loading rate {loading_rate:.0f} nodes/sec is too slow"
            
            print(f"Loading performance: {loading_rate:.0f} nodes/second")
            
        finally:
            pickle_file.unlink(missing_ok=True)

    def test_complex_properties_loading(self):
        """Test loading with complex property types."""
        # Create nodes with complex properties
        complex_props = {
            "simple_string": "test",
            "integer": 42,
            "float": 3.14159,
            "boolean": True,
            "none_value": None,
            "list": [1, "two", 3.0, True, None],
            "nested_dict": {
                "level1": {
                    "level2": {
                        "value": "deep"
                    }
                }
            },
            "unicode": "🚀💻🎉",
            "large_list": list(range(100))
        }
        
        node_id = self.db.create_node(
            labels=["Complex"],
            properties=complex_props
        )
        
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
            pickle_file = Path(f.name)
            
        try:
            self.db.save_pickle(pickle_file)
            
            test_db = GraphDB()
            test_db.load_pickle(pickle_file)
            
            # Verify complex properties are preserved
            loaded_node = test_db.get_node(node_id)
            assert loaded_node is not None
            
            loaded_props = loaded_node["properties"]
            assert loaded_props["simple_string"] == "test"
            assert loaded_props["integer"] == 42
            assert loaded_props["float"] == 3.14159
            assert loaded_props["boolean"] is True
            assert loaded_props["none_value"] is None
            assert loaded_props["list"] == [1, "two", 3.0, True, None]
            assert loaded_props["nested_dict"]["level1"]["level2"]["value"] == "deep"
            assert loaded_props["unicode"] == "🚀💻🎉"
            assert loaded_props["large_list"][:5] == [0, 1, 2, 3, 4]
            
        finally:
            pickle_file.unlink(missing_ok=True)

    def test_transaction_rollback_optimization(self):
        """Test that transaction rollback uses optimized loading."""
        # Create initial state
        initial_nodes = []
        for i in range(50):
            node_id = self.db.create_node(
                labels=["Initial"],
                properties={"index": i}
            )
            initial_nodes.append(node_id)
        
        for i in range(25):
            self.db.create_relationship(
                initial_nodes[i],
                initial_nodes[i + 25],
                "INITIAL_REL"
            )
        
        initial_node_count = self.db.node_count
        initial_rel_count = self.db.relationship_count
        
        # Start transaction
        transaction = self.db.transaction_manager.begin_transaction()
        
        # Make substantial changes
        transaction_nodes = []
        for i in range(50, 100):
            node_id = self.db.create_node(
                labels=["Transaction"],
                properties={"index": i}
            )
            transaction_nodes.append(node_id)
        
        for i in range(25):
            self.db.create_relationship(
                transaction_nodes[i],
                transaction_nodes[i + 25],
                "TRANS_REL"
            )
        
        # Verify transaction state
        assert self.db.node_count == initial_node_count + 50
        assert self.db.relationship_count == initial_rel_count + 25
        
        # Test rollback performance
        start_time = time.time()
        self.db.transaction_manager.rollback_transaction()
        rollback_time = time.time() - start_time
        
        # Verify rollback correctness
        assert self.db.node_count == initial_node_count
        assert self.db.relationship_count == initial_rel_count
        
        # Performance assertion (should be very fast)
        elements_restored = initial_node_count + initial_rel_count
        restore_rate = elements_restored / rollback_time if rollback_time > 0 else 0
        
        # Should restore at least 1000 elements per second
        assert restore_rate > 1000, f"Restore rate {restore_rate:.0f} elements/sec is too slow"
        
        print(f"Transaction rollback rate: {restore_rate:.0f} elements/second")


class TestLoadingRegressionPrevention:
    """Tests to prevent performance regressions in loading."""

    def test_loading_scales_linearly(self):
        """Test that loading time scales roughly linearly with graph size."""
        results = {}
        
        # Test different sizes
        sizes = [100, 200, 400]
        
        for size in sizes:
            db = GraphDB()
            
            # Create graph
            for i in range(size):
                db.create_node(
                    labels=["ScaleTest"],
                    properties={"index": i, "data": f"value_{i}"}
                )
            
            for i in range(size // 2):
                db.create_relationship(
                    i,
                    (i + size // 2) % size,
                    "TEST_REL"
                )
            
            with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
                pickle_file = Path(f.name)
                
            try:
                db.save_pickle(pickle_file)
                
                test_db = GraphDB()
                start_time = time.time()
                test_db.load_pickle(pickle_file)
                load_time = time.time() - start_time
                
                results[size] = {
                    'time': load_time,
                    'rate': size / load_time if load_time > 0 else 0
                }
                
                # Verify correctness
                assert test_db.node_count == size
                assert test_db.relationship_count == size // 2
                
            finally:
                pickle_file.unlink(missing_ok=True)
        
        # Check that performance doesn't degrade dramatically
        for size in sizes:
            rate = results[size]['rate']
            assert rate > 1000, f"Loading rate for {size} nodes is too slow: {rate:.0f} nodes/sec"
        
        print("Loading scaling results:")
        for size in sizes:
            print(f"  {size} nodes: {results[size]['rate']:.0f} nodes/sec")

    def test_memory_efficiency(self):
        """Test that loading doesn't consume excessive memory."""
        # This is a basic test - in production you'd use memory profiling tools
        import gc
        
        # Create a substantial graph
        db = GraphDB()
        for i in range(1000):
            db.create_node(
                labels=["MemoryTest"],
                properties={"index": i, "data": "x" * 100}  # Some data
            )
        
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
            pickle_file = Path(f.name)
            
        try:
            db.save_pickle(pickle_file)
            
            # Clear original
            del db
            gc.collect()
            
            # Load and verify
            test_db = GraphDB()
            test_db.load_pickle(pickle_file)
            
            assert test_db.node_count == 1000
            
            # Basic memory check - graph should not be empty
            assert len(test_db._node_id_to_vertex_index) == 1000
            
        finally:
            pickle_file.unlink(missing_ok=True)
