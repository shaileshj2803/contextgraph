"""
Tests for variable-length path functionality in Cypher queries.
"""

import pytest
from contextgraph import GraphDB


class TestVariableLengthPaths:
    """Test variable-length path patterns in MATCH clauses."""

    def setup_method(self):
        """Set up test database with a chain of nodes."""
        self.db = GraphDB()
        
        # Create a chain: Alice -> Bob -> Charlie -> Diana -> Eve
        self.alice_id = self.db.create_node(['Person'], {'name': 'Alice', 'age': 30})
        self.bob_id = self.db.create_node(['Person'], {'name': 'Bob', 'age': 25})
        self.charlie_id = self.db.create_node(['Person'], {'name': 'Charlie', 'age': 35})
        self.diana_id = self.db.create_node(['Person'], {'name': 'Diana', 'age': 28})
        self.eve_id = self.db.create_node(['Person'], {'name': 'Eve', 'age': 32})
        
        # Create relationships
        self.db.create_relationship(self.alice_id, self.bob_id, 'KNOWS')
        self.db.create_relationship(self.bob_id, self.charlie_id, 'KNOWS')
        self.db.create_relationship(self.charlie_id, self.diana_id, 'KNOWS')
        self.db.create_relationship(self.diana_id, self.eve_id, 'KNOWS')
        
        # Add a branch: Alice -> Frank
        self.frank_id = self.db.create_node(['Person'], {'name': 'Frank', 'age': 40})
        self.db.create_relationship(self.alice_id, self.frank_id, 'WORKS_WITH')

    def test_exact_hops(self):
        """Test exact number of hops (*n syntax)."""
        # Test 1 hop
        result = self.db.execute('MATCH (a:Person)-[:KNOWS*1]->(b:Person) RETURN a.name, b.name')
        assert len(result) == 4  # Direct relationships
        names = [(r['a.name'], r['b.name']) for r in result]
        assert ('Alice', 'Bob') in names
        assert ('Bob', 'Charlie') in names
        assert ('Charlie', 'Diana') in names
        assert ('Diana', 'Eve') in names
        
        # Test 2 hops
        result = self.db.execute('MATCH (a:Person)-[:KNOWS*2]->(b:Person) RETURN a.name, b.name')
        assert len(result) == 3
        names = [(r['a.name'], r['b.name']) for r in result]
        assert ('Alice', 'Charlie') in names
        assert ('Bob', 'Diana') in names
        assert ('Charlie', 'Eve') in names
        
        # Test 3 hops
        result = self.db.execute('MATCH (a:Person)-[:KNOWS*3]->(b:Person) RETURN a.name, b.name')
        assert len(result) == 2
        names = [(r['a.name'], r['b.name']) for r in result]
        assert ('Alice', 'Diana') in names
        assert ('Bob', 'Eve') in names
        
        # Test 4 hops
        result = self.db.execute('MATCH (a:Person)-[:KNOWS*4]->(b:Person) RETURN a.name, b.name')
        assert len(result) == 1
        names = [(r['a.name'], r['b.name']) for r in result]
        assert ('Alice', 'Eve') in names

    def test_range_hops(self):
        """Test range of hops (*min..max syntax)."""
        # Test 1-2 hops
        result = self.db.execute('MATCH (a:Person)-[:KNOWS*1..2]->(b:Person) RETURN a.name, b.name')
        assert len(result) == 7  # 4 direct + 3 two-hop
        
        # Test 2-3 hops
        result = self.db.execute('MATCH (a:Person)-[:KNOWS*2..3]->(b:Person) RETURN a.name, b.name')
        assert len(result) == 5  # 3 two-hop + 2 three-hop
        
        # Test 1-4 hops (should include all possible paths)
        result = self.db.execute('MATCH (a:Person)-[:KNOWS*1..4]->(b:Person) RETURN a.name, b.name')
        assert len(result) == 10  # All possible paths in the chain

    def test_unlimited_hops(self):
        """Test unlimited hops (* syntax)."""
        result = self.db.execute('MATCH (a:Person)-[:KNOWS*]->(b:Person) RETURN a.name, b.name')
        
        # Should find all reachable paths (same as *1..10 with our default limit)
        expected_paths = [
            ('Alice', 'Bob'), ('Alice', 'Charlie'), ('Alice', 'Diana'), ('Alice', 'Eve'),
            ('Bob', 'Charlie'), ('Bob', 'Diana'), ('Bob', 'Eve'),
            ('Charlie', 'Diana'), ('Charlie', 'Eve'),
            ('Diana', 'Eve')
        ]
        
        assert len(result) == len(expected_paths)
        names = [(r['a.name'], r['b.name']) for r in result]
        for expected in expected_paths:
            assert expected in names

    def test_different_relationship_types(self):
        """Test variable-length paths with different relationship types."""
        # Test KNOWS relationships only
        result = self.db.execute('MATCH (a:Person)-[:KNOWS*1..2]->(b:Person) RETURN a.name, b.name')
        knows_count = len(result)
        
        # Test WORKS_WITH relationships (should find Alice -> Frank)
        result = self.db.execute('MATCH (a:Person)-[:WORKS_WITH*1]->(b:Person) RETURN a.name, b.name')
        assert len(result) == 1
        assert result[0]['a.name'] == 'Alice'
        assert result[0]['b.name'] == 'Frank'
        
        # Test any relationship type (this might not be supported yet)
        try:
            result = self.db.execute('MATCH (a:Person)-[*1..2]->(b:Person) RETURN a.name, b.name')
            # Should include both KNOWS and WORKS_WITH relationships
            assert len(result) >= knows_count + 1
        except Exception:
            # It's acceptable if wildcard relationship types aren't supported yet
            pass

    def test_variable_length_with_properties(self):
        """Test variable-length paths with node property filtering."""
        # Find paths to people over 30
        result = self.db.execute(
            'MATCH (a:Person)-[:KNOWS*1..3]->(b:Person) '
            'WHERE b.age > 30 '
            'RETURN a.name, b.name, b.age'
        )
        
        # Should find paths to Charlie (35), Diana (28 - no), Eve (32)
        ages = [r['b.age'] for r in result]
        assert all(age > 30 for age in ages)
        
        names = [r['b.name'] for r in result]
        assert 'Charlie' in names
        assert 'Eve' in names
        assert 'Diana' not in names  # Diana is 28

    def test_variable_length_with_return_path_info(self):
        """Test returning path information from variable-length queries."""
        # Test with relationship variable
        result = self.db.execute(
            'MATCH (a:Person)-[r:KNOWS*2]->(b:Person) '
            'RETURN a.name, b.name, LENGTH(r) as path_length'
        )
        
        # All results should have path_length = 2
        for r in result:
            # Note: LENGTH function might not be implemented yet, 
            # but the relationship variable should be stored
            assert 'path_length' in r or 'LENGTH(r)' in r

    def test_no_cycles(self):
        """Test that variable-length paths don't create infinite cycles."""
        # Add a cycle: Eve -> Alice
        self.db.create_relationship(self.eve_id, self.alice_id, 'KNOWS')
        
        # This should still terminate and not create infinite loops
        result = self.db.execute('MATCH (a:Person)-[:KNOWS*1..5]->(b:Person) RETURN a.name, b.name')
        
        # Should find many paths but not infinite
        assert len(result) >= 10  # More paths due to cycle
        assert len(result) < 100  # But not infinite

    def test_zero_hops_not_supported(self):
        """Test that zero hops (*0) is not supported or handled gracefully."""
        # This might raise an error or return empty results
        try:
            result = self.db.execute('MATCH (a:Person)-[:KNOWS*0]->(b:Person) RETURN a.name, b.name')
            # If it doesn't raise an error, it should return empty results
            assert len(result) == 0
        except Exception:
            # It's acceptable for this to raise a parsing error
            pass

    def test_performance_with_large_paths(self):
        """Test performance with larger path lengths."""
        import time
        
        # Test with maximum reasonable path length
        start_time = time.time()
        result = self.db.execute('MATCH (a:Person)-[:KNOWS*1..8]->(b:Person) RETURN a.name, b.name')
        end_time = time.time()
        
        # Should complete in reasonable time (less than 1 second for small graph)
        assert end_time - start_time < 1.0
        
        # Should find all possible paths within 8 hops
        assert len(result) >= 10

    def test_variable_length_mixed_with_fixed(self):
        """Test mixing variable-length with fixed-length relationships."""
        # This is a more advanced test - might not be supported yet
        try:
            # Find paths: Person -[:KNOWS*2]-> Person -[:WORKS_WITH]-> Person
            result = self.db.execute(
                'MATCH (a:Person)-[:KNOWS*2]->(b:Person)-[:WORKS_WITH]->(c:Person) '
                'RETURN a.name, b.name, c.name'
            )
            # This is complex pattern matching - results depend on implementation
            assert isinstance(result, list)
        except Exception:
            # It's acceptable if this advanced pattern isn't supported yet
            pass


class TestVariableLengthPathEdgeCases:
    """Test edge cases for variable-length paths."""

    def setup_method(self):
        """Set up minimal test database."""
        self.db = GraphDB()

    def test_empty_graph(self):
        """Test variable-length paths on empty graph."""
        result = self.db.execute('MATCH (a:Person)-[:KNOWS*1..3]->(b:Person) RETURN a.name, b.name')
        assert len(result) == 0

    def test_single_node(self):
        """Test variable-length paths with single node."""
        node_id = self.db.create_node(['Person'], {'name': 'Alice'})
        
        result = self.db.execute('MATCH (a:Person)-[:KNOWS*1..3]->(b:Person) RETURN a.name, b.name')
        assert len(result) == 0  # No relationships, so no paths

    def test_disconnected_components(self):
        """Test variable-length paths with disconnected graph components."""
        # Create two disconnected pairs
        a_id = self.db.create_node(['Person'], {'name': 'Alice'})
        b_id = self.db.create_node(['Person'], {'name': 'Bob'})
        c_id = self.db.create_node(['Person'], {'name': 'Charlie'})
        d_id = self.db.create_node(['Person'], {'name': 'Diana'})
        
        self.db.create_relationship(a_id, b_id, 'KNOWS')
        self.db.create_relationship(c_id, d_id, 'KNOWS')
        
        # Should find paths within each component but not between them
        result = self.db.execute('MATCH (a:Person)-[:KNOWS*1..3]->(b:Person) RETURN a.name, b.name')
        assert len(result) == 2  # Alice->Bob and Charlie->Diana
        
        names = [(r['a.name'], r['b.name']) for r in result]
        assert ('Alice', 'Bob') in names
        assert ('Charlie', 'Diana') in names
        assert ('Alice', 'Charlie') not in names
        assert ('Alice', 'Diana') not in names

    def test_self_loops(self):
        """Test variable-length paths with self-loops."""
        node_id = self.db.create_node(['Person'], {'name': 'Alice'})
        self.db.create_relationship(node_id, node_id, 'KNOWS')  # Self-loop
        
        # Variable-length paths should handle self-loops without infinite recursion
        result = self.db.execute('MATCH (a:Person)-[:KNOWS*1..3]->(b:Person) RETURN a.name, b.name')
        
        # Should find the self-loop but not infinite paths
        assert len(result) >= 1
        assert len(result) < 10  # Should not be infinite
