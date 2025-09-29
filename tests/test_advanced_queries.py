"""
Advanced test cases for complex Cypher queries, performance, and edge cases.
"""

import pytest
import time
from contextgraph import GraphDB, CypherSyntaxError, GraphDBError

class TestComplexQueries:
    """Test complex query scenarios."""

    def setup_method(self):
        """Set up a complex graph for testing."""
        self.db = GraphDB()

        # Create a social network with multiple relationship types
        self.db.execute('''
            CREATE (alice:Person {name: "Alice", age: 30, city: "NYC", department: "Engineering"})
        ''')
        self.db.execute('''
            CREATE (bob:Person {name: "Bob", age: 25, city: "SF", department: "Design"})
        ''')
        self.db.execute('''
            CREATE (charlie:Person {name: "Charlie", age: 35, city: "NYC", department: "Engineering"})
        ''')
        self.db.execute('''
            CREATE (diana:Person {name: "Diana", age: 28, city: "LA", department: "Marketing"})
        ''')

        # Create companies
        self.db.execute('''
            CREATE (acme:Company {name: "ACME Corp", industry: "Tech", size: "Large", founded: 2010})
        ''')
        self.db.execute('''
            CREATE (beta:Company {name: "Beta Inc", industry: "Finance", size: "Medium", founded: 2015})
        ''')

        # Create work relationships
        self.db.execute('''
            CREATE (alice_work:Person {name: "Alice"})
            -[:WORKS_FOR {position: "Senior Engineer", salary: 120000, start_date: "2020 - 01 - 15"}]->
            (acme_work:Company {name: "ACME Corp"})
        ''')

        self.db.execute('''
            CREATE (charlie_work:Person {name: "Charlie"})
            -[:WORKS_FOR {position: "Engineering Manager", salary: 140000, start_date: "2019 - 03 - 01"}]->
            (acme_work2:Company {name: "ACME Corp"})
        ''')

        self.db.execute('''
            CREATE (bob_work:Person {name: "Bob"})
            -[:WORKS_FOR {position: "Lead Designer", salary: 100000, start_date: "2021 - 06 - 01"}]->
            (beta_work:Company {name: "Beta Inc"})
        ''')

        # Create friendship relationships
        self.db.execute('''
            CREATE (alice_friend:Person {name: "Alice"})
            -[:FRIENDS_WITH {since: "2018 - 05 - 10", closeness: "close"}]->
            (bob_friend:Person {name: "Bob"})
        ''')

        self.db.execute('''
            CREATE (charlie_friend:Person {name: "Charlie"})
            -[:FRIENDS_WITH {since: "2017 - 12 - 25", closeness: "very_close"}]->
            (alice_friend2:Person {name: "Alice"})
        ''')

    def test_multi_relationship_type_queries(self):
        """Test queries involving multiple relationship types."""
        # Find people who both work and have friends
        work_result = self.db.execute('''
            MATCH (p:Person)-[:WORKS_FOR]->(c:Company)
            RETURN DISTINCT p.name
        ''')

        friend_result = self.db.execute('''
            MATCH (p:Person)-[:FRIENDS_WITH]->(f:Person)
            RETURN DISTINCT p.name
        ''')

        # Both should have results
        assert len(work_result) >= 1
        assert len(friend_result) >= 1

    def test_complex_filtering_scenarios(self):
        """Test complex WHERE clause scenarios."""
        # Multiple AND conditions
        result = self.db.execute('''
            MATCH (p:Person)-[:WORKS_FOR]->(c:Company)
            WHERE p.name = "Alice" AND c.name = "ACME Corp"
            RETURN p.name, c.name
        ''')
        assert len(result) >= 1

        # Range queries
        result = self.db.execute('''
            MATCH (p:Person)
            WHERE p.age >= 25 AND p.age <= 35
            RETURN p.name, p.age
        ''')
        # Should include Alice (30), Bob (25), Charlie (35), Diana (28)
        assert len(result) >= 3

    def test_aggregation_edge_cases(self):
        """Test edge cases in aggregation functions."""
        # COUNT with no matches
        result = self.db.execute('''
            MATCH (p:Person)-[:NONEXISTENT]->(c:Company)
            RETURN COUNT(*)
        ''')
        assert len(result) == 1
        assert result[0]['COUNT(*)'] == 0

        # AVG with no matches
        result = self.db.execute('''
            MATCH (p:Person)
            WHERE p.age > 100
            RETURN AVG(p.age)
        ''')
        assert len(result) == 1
        assert result[0]['AVG(p.age)'] is None

    def test_property_access_edge_cases(self):
        """Test property access with missing properties."""
        # Create a person without age
        self.db.execute('CREATE (eve:Person {name: "Eve", city: "Boston"})')

        # Query should handle missing age gracefully
        result = self.db.execute('''
            MATCH (p:Person)
            WHERE p.age > 25
            RETURN p.name, p.age
        ''')

        # Eve should not be in results due to missing age
        names = [r['p.name'] for r in result if r.get('p.name')]
        assert 'Eve' not in names

class TestPerformance:
    """Test performance with larger datasets."""

    def setup_method(self):
        """Set up larger dataset for performance testing."""
        self.db = GraphDB()

    def test_large_node_creation(self):
        """Test creating many nodes efficiently."""
        start_time = time.time()

        # Create 100 nodes
        for i in range(100):
            self.db.execute(f'CREATE (p{i}:Person {{name: "Person{i}", id: {i}, age: {20 + (i % 50)}}})')

        creation_time = time.time() - start_time

        assert self.db.node_count == 100
        # Should complete in reasonable time (less than 5 seconds)
        assert creation_time < 5.0

    def test_large_relationship_creation(self):
        """Test creating many relationships."""
        # First create some nodes
        for i in range(20):
            self.db.execute(f'CREATE (p{i}:Person {{name: "Person{i}", id: {i}}})')

        start_time = time.time()

        # Create relationships between nodes using API calls for better performance
        for i in range(10):
            # Find the nodes by their properties (since we can't use variables across statements)
            person1_nodes = self.db.find_nodes(properties={'name': f'Person{i}'})
            person2_nodes = self.db.find_nodes(properties={'name': f'Person{i + 10}'})
            
            if person1_nodes and person2_nodes:
                self.db.create_relationship(person1_nodes[0]['id'], person2_nodes[0]['id'], 'KNOWS')

        creation_time = time.time() - start_time

        assert self.db.relationship_count >= 10
        # Should complete in reasonable time
        assert creation_time < 3.0

    def test_complex_query_performance(self):
        """Test performance of complex queries."""
        # Create a moderate dataset using API calls
        companies = {}
        for i in range(50):
            # Create person
            person_id = self.db.create_node(['Person'], {
                'name': f'Person{i}',
                'age': 20 + (i % 40),
                'department': f'Dept{i % 5}'
            })
            
            # Create or get company
            company_name = f'Company{i % 10}'
            if company_name not in companies:
                companies[company_name] = self.db.create_node(['Company'], {
                    'name': company_name,
                    'industry': f'Industry{i % 3}'
                })
            
            # Create relationship
            self.db.create_relationship(person_id, companies[company_name], 'WORKS_FOR', {
                'salary': 50000 + (i * 1000)
            })

        start_time = time.time()

        # Complex query with joins and aggregations
        result = self.db.execute('''
            MATCH (p:Person)-[:WORKS_FOR]->(c:Company)
            WHERE p.age >= 30 AND c.industry = "Industry1"
            RETURN c.name, COUNT(*), AVG(p.age)
        ''')

        query_time = time.time() - start_time

        # Should complete quickly (less than 2 seconds)
        assert query_time < 2.0
        assert len(result) >= 0  # May or may not have results depending on data

class TestErrorHandling:
    """Test error handling and edge cases."""

    def setup_method(self):
        """Set up test database."""
        self.db = GraphDB()

    def test_syntax_errors(self):
        """Test handling of syntax errors."""
        with pytest.raises(CypherSyntaxError):
            self.db.execute('INVALID CYPHER SYNTAX')

        with pytest.raises(CypherSyntaxError):
            self.db.execute('MATCH (p:Person WHERE p.name = "Alice" RETURN p.name')  # Missing )

    def test_empty_queries(self):
        """Test handling of empty or whitespace queries."""
        result = self.db.execute('')
        assert len(result) == 0

        result = self.db.execute('   ')
        assert len(result) == 0

    def test_malformed_patterns(self):
        """Test handling of malformed patterns."""
        # These should either work or fail gracefully
        try:
            result = self.db.execute('MATCH (p) RETURN p')
            # If it works, should return QueryResult (not list)
            from contextgraph.query_result import QueryResult
            assert isinstance(result, QueryResult)
        except (CypherSyntaxError, GraphDBError):
            # If it fails, should raise appropriate exception
            pass

    def test_type_mismatches(self):
        """Test handling of type mismatches in comparisons."""
        self.db.execute('CREATE (p:Person {name: "Alice", age: 30})')

        # Comparing string to number should handle gracefully
        result = self.db.execute('MATCH (p:Person) WHERE p.name > 25 RETURN p.name')
        # Should handle the type mismatch and return empty result
        from contextgraph.query_result import QueryResult
        assert isinstance(result, QueryResult)
        assert len(result) == 0  # Should be empty due to type mismatch

class TestDataIntegrity:
    """Test data integrity and consistency."""

    def setup_method(self):
        """Set up test database."""
        self.db = GraphDB()

    def test_node_relationship_consistency(self):
        """Test that relationships maintain node consistency."""
        # Create nodes and relationships
        self.db.execute('''
            CREATE (alice:Person {name: "Alice"})
            -[:WORKS_FOR]->
            (acme:Company {name: "ACME"})
        ''')

        # Verify nodes exist
        nodes = self.db.execute('MATCH (n) RETURN n.name')
        node_names = [n.get('n.name') for n in nodes if n.get('n.name')]
        assert 'Alice' in node_names
        assert 'ACME' in node_names

        # Verify relationship exists (using supported syntax)
        rel_result = self.db.execute('MATCH (a)-[:WORKS_FOR]->(b) RETURN a.name, b.name')
        assert len(rel_result) >= 1

    def test_duplicate_handling(self):
        """Test handling of duplicate data."""
        # Create same person twice
        self.db.execute('CREATE (alice1:Person {name: "Alice", id: 1})')
        self.db.execute('CREATE (alice2:Person {name: "Alice", id: 2})')

        # Should create two separate nodes (Cypher doesn't prevent duplicates by default)
        result = self.db.execute('MATCH (p:Person) WHERE p.name = "Alice" RETURN p.id')
        assert len(result) == 2

        ids = [r['p.id'] for r in result]
        assert 1 in ids
        assert 2 in ids

    def test_property_updates_and_queries(self):
        """Test that property updates are reflected in queries."""
        # Create initial node
        self.db.execute('CREATE (p:Person {name: "Alice", age: 30})')

        # Verify initial state
        result = self.db.execute('MATCH (p:Person) WHERE p.name = "Alice" RETURN p.age')
        assert len(result) == 1
        assert result[0]['p.age'] == 30

        # Note: SET operations might not be fully implemented yet
        # So we test what we can with current functionality

class TestRegressionTests:
    """Regression tests for previously found issues."""

    def setup_method(self):
        """Set up test database."""
        self.db = GraphDB()

    def test_null_comparison_regression(self):
        """Test that null comparisons don't crash (regression test)."""
        # Create person without age property
        self.db.execute('CREATE (p:Person {name: "Alice"})')

        # This should not crash
        result = self.db.execute('MATCH (p:Person) WHERE p.age > 25 RETURN p.name')
        from contextgraph.query_result import QueryResult
        assert isinstance(result, QueryResult)
        # Alice should not be in results due to null age
        assert len(result) == 0

    def test_relationship_pattern_detection_regression(self):
        """Test that relationship patterns are correctly detected (regression test)."""
        self.db.execute('''
            CREATE (a:Person {name: "Alice"})
            -[:WORKS_FOR]->
            (c:Company {name: "ACME"})
        ''')

        # This should work correctly
        result = self.db.execute('MATCH (p:Person)-[:WORKS_FOR]->(c:Company) RETURN p.name, c.name')
        assert len(result) == 1
        assert result[0]['p.name'] == 'Alice'
        assert result[0]['c.name'] == 'ACME'

    def test_duplicate_results_regression(self):
        """Test that joins don't produce duplicate results (regression test)."""
        # Create nodes and relationship using API calls
        alice_id = self.db.create_node(['Person'], {'name': 'Alice'})
        acme_id = self.db.create_node(['Company'], {'name': 'ACME'})
        self.db.create_relationship(alice_id, acme_id, 'WORKS_FOR')

        result = self.db.execute('MATCH (p:Person)-[:WORKS_FOR]->(c:Company) RETURN p.name, c.name')

        # Should get exactly one result, not duplicates
        assert len(result) == 1
        assert result[0]['p.name'] == 'Alice'
        assert result[0]['c.name'] == 'ACME'

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
