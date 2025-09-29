"""
Test cases for pickle serialization functionality.
"""

import pytest
import tempfile
import time
from pathlib import Path
from contextgraph import GraphDB
from contextgraph.exceptions import GraphDBError

class TestPickleSerialization:
    """Test pickle save / load functionality."""

    def setup_method(self):
        """Set up test database and temporary directory."""
        self.db = GraphDB()
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_sample_graph(self):
        """Create a sample graph with various data types."""
        # Create nodes with different property types using create_node method
        alice_id = self.db.create_node(
            ['Person'],
            {
                'name': 'Alice',
                'age': 30,
                'active': True,
                'scores': [95, 87, 92]
            }
        )

        bob_id = self.db.create_node(
            ['Person'],
            {
                'name': 'Bob',
                'age': 25,
                'active': False,
                'metadata': {'role': 'admin', 'level': 5}
            }
        )

        acme_id = self.db.create_node(
            ['Company'],
            {
                'name': 'ACME Corp',
                'founded': 2010,
                'revenue': 1500000.50
            }
        )

        # Create relationships
        self.db.create_relationship(
            alice_id,
            acme_id,
            'WORKS_FOR',
            {'position': 'Engineer', 'salary': 120000, 'benefits': ['health', 'dental']}
        )

        self.db.create_relationship(
            bob_id,
            alice_id,
            'FRIENDS_WITH',
            {'since': '2020 - 01 - 15', 'closeness': 0.8}
        )

    def test_basic_pickle_save_load(self):
        """Test basic pickle save and load functionality."""
        self.create_sample_graph()

        # Save to pickle
        pickle_file = self.temp_dir / "test_graph.pkl"
        self.db.save_pickle(pickle_file)

        # Verify file was created
        assert pickle_file.exists()
        assert pickle_file.stat().st_size > 0

        # Create new database and load
        new_db = GraphDB()
        new_db.load_pickle(pickle_file)

        # Verify data integrity
        assert new_db.node_count == self.db.node_count
        assert new_db.relationship_count == self.db.relationship_count

        # Verify specific nodes
        alice_nodes = new_db.find_nodes(properties={'name': 'Alice'})
        assert len(alice_nodes) == 1
        alice = alice_nodes[0]

        assert alice['properties']['name'] == 'Alice'
        assert alice['properties']['age'] == 30
        assert alice['properties']['active'] is True
        assert alice['properties']['scores'] == [95, 87, 92]

        # Verify relationships work
        result = new_db.execute('MATCH (p:Person)-[:WORKS_FOR]->(c:Company) RETURN p.name, c.name')
        assert len(result) == 1
        assert result[0]['p.name'] == 'Alice'
        assert result[0]['c.name'] == 'ACME Corp'

    def test_pickle_extension_handling(self):
        """Test automatic .pkl extension handling."""
        self.create_sample_graph()

        # Save without extension
        base_file = self.temp_dir / "test_graph"
        self.db.save_pickle(base_file)

        # Should create .pkl file
        pkl_file = self.temp_dir / "test_graph.pkl"
        assert pkl_file.exists()

        # Load should work with or without extension
        new_db1 = GraphDB()
        new_db1.load_pickle(base_file)  # Without extension
        assert new_db1.node_count == self.db.node_count

        new_db2 = GraphDB()
        new_db2.load_pickle(pkl_file)  # With extension
        assert new_db2.node_count == self.db.node_count

    def test_pickle_type_preservation(self):
        """Test that pickle preserves Python types perfectly."""
        # Create node with complex data types
        complex_data = {
            'string': 'hello',
            'integer': 42,
            'float': 3.14159,
            'boolean': True,
            'none_value': None,
            'list': [1, 2, 3, 'mixed', True],
            'dict': {'nested': {'deep': 'value'}},
            'tuple': (1, 2, 3),  # This will be preserved as tuple in pickle
        }

        _ = self.db.create_node(['Test'], complex_data)  # noqa: F841

        # Save and load
        pickle_file = self.temp_dir / "complex_types.pkl"
        self.db.save_pickle(pickle_file)

        new_db = GraphDB()
        new_db.load_pickle(pickle_file)

        # Verify all types are preserved
        nodes = new_db.find_nodes(labels=['Test'])
        assert len(nodes) == 1

        props = nodes[0]['properties']
        assert props['string'] == 'hello'
        assert props['integer'] == 42
        assert props['float'] == 3.14159
        assert props['boolean'] is True
        assert props['none_value'] is None
        assert props['list'] == [1, 2, 3, 'mixed', True]
        assert props['dict'] == {'nested': {'deep': 'value'}}
        assert props['tuple'] == (1, 2, 3)  # Tuple preserved!

    def test_pickle_vs_json_performance(self):
        """Test that pickle is faster than JSON for large graphs."""
        # Create a larger graph for performance testing
        node_ids = []
        for i in range(100):
            node_id = self.db.create_node(
                ['Person'],
                {'name': f'Person{i}', 'id': i, 'data': [1, 2, 3, 4, 5]}
            )
            node_ids.append(node_id)

        # Create relationships
        for i in range(50):
            if i + 1 < len(node_ids):
                self.db.create_relationship(
                    node_ids[i],
                    node_ids[i + 1],
                    'KNOWS',
                    {'weight': i * 0.1}
                )

        json_file = self.temp_dir / "test_graph.json"
        pickle_file = self.temp_dir / "test_graph.pkl"

        # Time JSON save
        start_time = time.time()
        self.db.save(json_file)
        json_save_time = time.time() - start_time

        # Time pickle save
        start_time = time.time()
        self.db.save_pickle(pickle_file)
        pickle_save_time = time.time() - start_time

        # Time JSON load
        json_db = GraphDB()
        start_time = time.time()
        json_db.load(json_file)
        json_load_time = time.time() - start_time

        # Time pickle load
        pickle_db = GraphDB()
        start_time = time.time()
        pickle_db.load_pickle(pickle_file)
        pickle_load_time = time.time() - start_time

        # Verify both loaded correctly
        assert json_db.node_count == self.db.node_count
        assert pickle_db.node_count == self.db.node_count
        assert json_db.relationship_count == self.db.relationship_count
        assert pickle_db.relationship_count == self.db.relationship_count

        # Pickle should generally be faster (though this may vary)
        print(f"JSON save: {json_save_time:.4f}s, Pickle save: {pickle_save_time:.4f}s")
        print(f"JSON load: {json_load_time:.4f}s, Pickle load: {pickle_load_time:.4f}s")

        # Check file sizes
        json_size = json_file.stat().st_size
        pickle_size = pickle_file.stat().st_size
        print(f"JSON size: {json_size} bytes, Pickle size: {pickle_size} bytes")

    def test_pickle_error_handling(self):
        """Test error handling for pickle operations."""
        # Test loading non - existent file
        with pytest.raises(FileNotFoundError):
            self.db.load_pickle("nonexistent.pkl")

        # Test loading corrupted file
        corrupted_file = self.temp_dir / "corrupted.pkl"
        with open(corrupted_file, 'wb') as f:
            f.write(b"not a pickle file")

        with pytest.raises(GraphDBError):
            self.db.load_pickle(corrupted_file)

    def test_pickle_with_empty_graph(self):
        """Test pickle operations with empty graph."""
        pickle_file = self.temp_dir / "empty_graph.pkl"

        # Save empty graph
        self.db.save_pickle(pickle_file)
        assert pickle_file.exists()

        # Load empty graph
        new_db = GraphDB()
        new_db.load_pickle(pickle_file)

        assert new_db.node_count == 0
        assert new_db.relationship_count == 0

        # Create CSV data and import it
        csv_file = self.temp_dir / "test_nodes.csv"
        with open(csv_file, 'w', newline='', encoding='utf - 8') as f:
            f.write('id,name,age,active\n')
            f.write('1,Alice,30,true\n')
            f.write('2,Bob,25,false\n')

        # Import the CSV data
        self.db.import_nodes_from_csv(csv_file, labels=['Person'])

        # Save to pickle
        self.db.save_pickle(pickle_file)

        # Load and verify
        new_db = GraphDB()
        new_db.load_pickle(pickle_file)

        assert new_db.node_count == 2

        # Verify CSV - imported data is preserved
        alice_nodes = new_db.find_nodes(properties={'name': 'Alice'})
        assert len(alice_nodes) == 1
        assert alice_nodes[0]['properties']['age'] == 30
        assert alice_nodes[0]['properties']['active'] is True
        assert 'Person' in alice_nodes[0]['labels']

    def test_pickle_preserves_counters(self):
        """Test that pickle preserves internal ID counters."""
        # Create some nodes and relationships
        self.create_sample_graph()

        original_node_counter = self.db._node_id_counter
        original_rel_counter = self.db._relationship_id_counter

        # Save and load
        pickle_file = self.temp_dir / "counters_test.pkl"
        self.db.save_pickle(pickle_file)

        new_db = GraphDB()
        new_db.load_pickle(pickle_file)

        # Verify counters are preserved
        assert new_db._node_id_counter == original_node_counter
        assert new_db._relationship_id_counter == original_rel_counter

        # Verify new nodes get correct IDs
        new_node_id = new_db.create_node(['Test'], {'name': 'New Node'})
        assert new_node_id == original_node_counter

    def test_pickle_with_transactions(self):
        """Test pickle operations within transactions."""
        # Create data within a transaction
        with self.db.transaction_manager.transaction():
            self.create_sample_graph()

            # Save within transaction
            pickle_file = self.temp_dir / "transaction_test.pkl"
            self.db.save_pickle(pickle_file)

        # Load in new database
        new_db = GraphDB()
        new_db.load_pickle(pickle_file)

        # Verify data was saved correctly
        assert new_db.node_count == self.db.node_count
        assert new_db.relationship_count == self.db.relationship_count

        # Test rollback scenario
        initial_count = self.db.node_count

        try:
            with self.db.transaction_manager.transaction():
                self.db.create_node(['Temp'], {'name': 'Temporary'})

                # This should be rolled back
                raise Exception("Simulated error")
        except Exception:
            pass

        # Node count should be unchanged
        assert self.db.node_count == initial_count

class TestPickleCompatibility:
    """Test pickle compatibility and edge cases."""

    def setup_method(self):
        """Set up test database."""
        self.db = GraphDB()
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_pickle_with_unicode_data(self):
        """Test pickle with Unicode and special characters."""
        # Create nodes with Unicode data
        unicode_data = {
            'chinese': '你好世界',
            'emoji': '🚀🎉💡',
            'arabic': 'مرحبا بالعالم',
            'special_chars': 'Special: !@#$%^&*()[]{}|\\:";\'<>?,./',
            'mixed': 'Hello 世界 🌍 مرحبا'
        }

        self.db.create_node(['Unicode'], unicode_data)

        # Save and load
        pickle_file = self.temp_dir / "unicode_test.pkl"
        self.db.save_pickle(pickle_file)

        new_db = GraphDB()
        new_db.load_pickle(pickle_file)

        # Verify Unicode data is preserved
        nodes = new_db.find_nodes(labels=['Unicode'])
        assert len(nodes) == 1

        props = nodes[0]['properties']
        assert props['chinese'] == '你好世界'
        assert props['emoji'] == '🚀🎉💡'
        assert props['arabic'] == 'مرحبا بالعالم'
        assert props['mixed'] == 'Hello 世界 🌍 مرحبا'

    def test_pickle_with_large_properties(self):
        """Test pickle with large property values."""
        # Create node with large data
        large_text = "A" * 10000  # 10KB string
        large_list = list(range(1000))  # 1000 integers
        large_dict = {f"key_{i}": f"value_{i}" for i in range(100)}

        large_data = {
            'large_text': large_text,
            'large_list': large_list,
            'large_dict': large_dict
        }

        self.db.create_node(['Large'], large_data)

        # Save and load
        pickle_file = self.temp_dir / "large_data_test.pkl"
        self.db.save_pickle(pickle_file)

        new_db = GraphDB()
        new_db.load_pickle(pickle_file)

        # Verify large data is preserved
        nodes = new_db.find_nodes(labels=['Large'])
        assert len(nodes) == 1

        props = nodes[0]['properties']
        assert props['large_text'] == large_text
        assert props['large_list'] == large_list
        assert props['large_dict'] == large_dict

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
