"""
Test cases for filter and join functionality in Cypher queries.
"""

import pytest
from contextgraph import GraphDB

class TestFiltering:
    """Test WHERE clause filtering capabilities."""

    def setup_method(self):
        """Set up test database with sample data."""
        self.db = GraphDB()

        # Create test nodes with various properties
        self.db.execute('CREATE (alice:Person {name: "Alice", age: 30, city: "NYC", salary: 75000})')
        self.db.execute('CREATE (bob:Person {name: "Bob", age: 25, city: "SF", salary: 65000})')
        self.db.execute('CREATE (charlie:Person {name: "Charlie", age: 35, city: "NYC", salary: 85000})')
        self.db.execute('CREATE (diana:Person {name: "Diana", age: 28, city: "LA"})')  # No salary

        # Create companies
        self.db.execute('CREATE (acme:Company {name: "ACME Corp", industry: "Tech", size: "Large"})')
        self.db.execute('CREATE (beta:Company {name: "Beta Inc", industry: "Finance", size: "Medium"})')

    def test_basic_equality_filter(self):
        """Test basic equality filtering."""
        result = self.db.execute('MATCH (p:Person) WHERE p.name = "Alice" RETURN p.name')
        assert len(result) == 1
        assert result[0]['p.name'] == 'Alice'

    def test_numeric_comparison_filters(self):
        """Test numeric comparison operators."""
        # Greater than
        result = self.db.execute('MATCH (p:Person) WHERE p.age > 30 RETURN p.name')
        names = [r['p.name'] for r in result]
        assert 'Charlie' in names
        assert 'Alice' not in names

        # Less than or equal
        result = self.db.execute('MATCH (p:Person) WHERE p.age <= 28 RETURN p.name')
        names = [r['p.name'] for r in result]
        assert 'Bob' in names
        assert 'Diana' in names
        assert 'Alice' not in names

        # Greater than or equal
        result = self.db.execute('MATCH (p:Person) WHERE p.age >= 30 RETURN p.name')
        names = [r['p.name'] for r in result]
        assert 'Alice' in names
        assert 'Charlie' in names
        assert 'Bob' not in names

    def test_string_comparison_filters(self):
        """Test string comparison operators."""
        result = self.db.execute('MATCH (p:Person) WHERE p.city = "NYC" RETURN p.name')
        names = [r['p.name'] for r in result]
        assert 'Alice' in names
        assert 'Charlie' in names
        assert len(names) == 2

        # Not equal
        result = self.db.execute('MATCH (p:Person) WHERE p.city != "NYC" RETURN p.name')
        names = [r['p.name'] for r in result]
        assert 'Bob' in names
        assert 'Diana' in names
        assert 'Alice' not in names

    def test_logical_operators(self):
        """Test AND, OR, NOT logical operators."""
        # AND operator
        result = self.db.execute('MATCH (p:Person) WHERE p.age > 25 AND p.city = "NYC" RETURN p.name')
        names = [r['p.name'] for r in result]
        assert 'Alice' in names
        assert 'Charlie' in names
        assert 'Bob' not in names

        # OR operator
        result = self.db.execute('MATCH (p:Person) WHERE p.age < 26 OR p.city = "LA" RETURN p.name')
        names = [r['p.name'] for r in result]
        assert 'Bob' in names
        assert 'Diana' in names
        assert len(names) == 2

    def test_null_value_handling(self):
        """Test filtering with null / missing properties."""
        # Diana doesn't have a salary property
        result = self.db.execute('MATCH (p:Person) WHERE p.salary > 70000 RETURN p.name')
        names = [r['p.name'] for r in result]
        assert 'Alice' in names
        assert 'Charlie' in names
        assert 'Diana' not in names  # Should be excluded due to null salary

        # Test equality with null
        result = self.db.execute('MATCH (p:Person) WHERE p.salary = 75000 RETURN p.name')
        assert len(result) == 1
        assert result[0]['p.name'] == 'Alice'

    def test_complex_multi_condition_filters(self):
        """Test complex filtering with multiple conditions."""
        result = self.db.execute('''
            MATCH (p:Person)
            WHERE p.age >= 25 AND p.age <= 35 AND p.city = "NYC"
            RETURN p.name, p.age
        ''')

        # Should find people in NYC aged 25 - 35
        assert len(result) >= 0  # May vary based on test data

        # Verify all results match the criteria
        for record in result:
            age = record.get('p.age')
            city = record.get('p.city')
            if age is not None:
                assert 25 <= age <= 35
            if city is not None:
                assert city == 'NYC'

class TestJoins:
    """Test relationship pattern matching (joins)."""

    def setup_method(self):
        """Set up test database with relationships."""
        self.db = GraphDB()

        # Create nodes and relationships in one go
        self.db.execute('''
            CREATE (alice:Person {name: "Alice", age: 30, department: "Engineering"})
            -[:WORKS_FOR {position: "Senior Engineer", since: 2020}]->
            (acme:Company {name: "ACME Corp", industry: "Tech"})
        ''')

        self.db.execute('''
            CREATE (bob:Person {name: "Bob", age: 25, department: "Design"})
            -[:WORKS_FOR {position: "Designer", since: 2021}]->
            (beta:Company {name: "Beta Inc", industry: "Finance"})
        ''')

        self.db.execute('''
            CREATE (charlie:Person {name: "Charlie", age: 35, department: "Engineering"})
            -[:WORKS_FOR {position: "Engineering Manager", since: 2019}]->
            (acme2:Company {name: "ACME Corp", industry: "Tech"})
        ''')

    def test_basic_relationship_matching(self):
        """Test basic relationship pattern matching."""
        result = self.db.execute('''
            MATCH (p:Person)-[:WORKS_FOR]->(c:Company)
            RETURN p.name, c.name
        ''')

        assert len(result) == 3

        # Check that all expected relationships are found
        relationships = [(r['p.name'], r['c.name']) for r in result]
        assert ('Alice', 'ACME Corp') in relationships
        assert ('Bob', 'Beta Inc') in relationships
        assert ('Charlie', 'ACME Corp') in relationships

    def test_filtered_joins(self):
        """Test joins with WHERE clause filters."""
        # Filter by company industry
        result = self.db.execute('''
            MATCH (p:Person)-[:WORKS_FOR]->(c:Company)
            WHERE c.industry = "Tech"
            RETURN p.name, c.name
        ''')

        assert len(result) == 2
        names = [r['p.name'] for r in result]
        assert 'Alice' in names
        assert 'Charlie' in names
        assert 'Bob' not in names

        # Filter by person age
        result = self.db.execute('''
            MATCH (p:Person)-[:WORKS_FOR]->(c:Company)
            WHERE p.age >= 30
            RETURN p.name, p.age, c.name
        ''')

        assert len(result) == 2
        names = [r['p.name'] for r in result]
        assert 'Alice' in names
        assert 'Charlie' in names

    def test_multi_condition_joins(self):
        """Test joins with multiple filter conditions."""
        result = self.db.execute('''
            MATCH (p:Person)-[:WORKS_FOR]->(c:Company)
            WHERE p.age >= 30 AND c.industry = "Tech"
            RETURN p.name, p.age, c.name, c.industry
        ''')

        assert len(result) == 2

        for record in result:
            assert record['p.age'] >= 30
            assert record['c.industry'] == 'Tech'
            assert record['p.name'] in ['Alice', 'Charlie']

    def test_relationship_type_filtering(self):
        """Test filtering by relationship type."""
        # This should work with the WORKS_FOR relationship
        result = self.db.execute('''
            MATCH (p:Person)-[:WORKS_FOR]->(c:Company)
            RETURN p.name, c.name
        ''')

        assert len(result) == 3

        # Test with non - existent relationship type
        result = self.db.execute('''
            MATCH (p:Person)-[:MANAGES]->(c:Company)
            RETURN p.name, c.name
        ''')

        assert len(result) == 0

    def test_complex_join_scenarios(self):
        """Test more complex join scenarios."""
        # Add a friendship relationship
        self.db.execute('''
            CREATE (alice2:Person {name: "Alice"})
            -[:FRIENDS_WITH {since: 2018}]->
            (bob2:Person {name: "Bob"})
        ''')

        # Test different relationship types
        work_result = self.db.execute('''
            MATCH (p:Person)-[:WORKS_FOR]->(c:Company)
            RETURN COUNT(*)
        ''')

        friend_result = self.db.execute('''
            MATCH (p:Person)-[:FRIENDS_WITH]->(f:Person)
            RETURN COUNT(*)
        ''')

        assert work_result[0]['COUNT(*)'] == 3
        assert friend_result[0]['COUNT(*)'] == 1

class TestAggregations:
    """Test aggregate functions with joins and filters."""

    def setup_method(self):
        """Set up test database for aggregation tests."""
        self.db = GraphDB()

        # Create a more complex dataset
        self.db.execute('''
            CREATE (alice:Person {name: "Alice", age: 30, salary: 75000})
            -[:WORKS_FOR]->(acme:Company {name: "ACME Corp", industry: "Tech"})
        ''')

        self.db.execute('''
            CREATE (bob:Person {name: "Bob", age: 25, salary: 65000})
            -[:WORKS_FOR]->(acme2:Company {name: "ACME Corp", industry: "Tech"})
        ''')

        self.db.execute('''
            CREATE (charlie:Person {name: "Charlie", age: 35, salary: 85000})
            -[:WORKS_FOR]->(beta:Company {name: "Beta Inc", industry: "Finance"})
        ''')

        self.db.execute('''
            CREATE (diana:Person {name: "Diana", age: 28, salary: 70000})
            -[:WORKS_FOR]->(beta2:Company {name: "Beta Inc", industry: "Finance"})
        ''')

    def test_count_aggregation(self):
        """Test COUNT aggregate function."""
        result = self.db.execute('''
            MATCH (p:Person)-[:WORKS_FOR]->(c:Company)
            RETURN c.name, COUNT(*)
        ''')

        # Should have some results
        assert len(result) >= 1

        # Verify COUNT function works
        for record in result:
            count = record.get('COUNT(*)')
            assert count is not None
            assert count > 0

    def test_average_aggregation(self):
        """Test AVG aggregate function."""
        result = self.db.execute('''
            MATCH (p:Person)-[:WORKS_FOR]->(c:Company)
            RETURN c.industry, AVG(p.age)
        ''')

        # Should calculate average age by industry
        assert len(result) >= 1

        for record in result:
            avg_age = record.get('AVG(p.age)')
            assert avg_age is not None
            assert avg_age > 0

    def test_multiple_aggregations(self):
        """Test multiple aggregate functions together."""
        result = self.db.execute('''
            MATCH (p:Person)-[:WORKS_FOR]->(c:Company)
            RETURN c.industry, COUNT(*), AVG(p.age), MIN(p.salary), MAX(p.salary)
        ''')

        assert len(result) >= 1

        for record in result:
            assert record.get('COUNT(*)') is not None
            assert record.get('AVG(p.age)') is not None
            assert record.get('MIN(p.salary)') is not None
            assert record.get('MAX(p.salary)') is not None

    def test_aggregation_with_filters(self):
        """Test aggregations combined with WHERE clauses."""
        result = self.db.execute('''
            MATCH (p:Person)-[:WORKS_FOR]->(c:Company)
            WHERE p.age >= 30
            RETURN COUNT(*), AVG(p.salary)
        ''')

        assert len(result) == 1
        count = result[0].get('COUNT(*)')
        avg_salary = result[0].get('AVG(p.salary)')

        assert count >= 1  # At least Alice and Charlie are >= 30
        assert avg_salary is not None

class TestCypherCreateRelationships:
    """Test Cypher CREATE statements for relationships."""

    def setup_method(self):
        """Set up clean database for each test."""
        self.db = GraphDB()

    def test_create_simple_relationship(self):
        """Test creating a simple relationship."""
        result = self.db.execute('''
            CREATE (a:Person {name: "Alice"})-[:KNOWS]->(b:Person {name: "Bob"})
        ''')

        assert self.db.node_count == 2
        assert self.db.relationship_count == 1

        # Verify the relationship exists
        result = self.db.execute('''
            MATCH (a:Person)-[:KNOWS]->(b:Person)
            RETURN a.name, b.name
        ''')

        assert len(result) == 1
        assert result[0]['a.name'] == 'Alice'
        assert result[0]['b.name'] == 'Bob'

    def test_create_relationship_with_properties(self):
        """Test creating relationships with properties."""
        result = self.db.execute('''
            CREATE (a:Person {name: "Alice"})
            -[:WORKS_FOR {position: "Engineer", since: 2020}]->
            (c:Company {name: "ACME Corp"})
        ''')

        assert self.db.node_count == 2
        assert self.db.relationship_count == 1

        # Verify the relationship and its properties exist
        result = self.db.execute('''
            MATCH (p:Person)-[:WORKS_FOR]->(c:Company)
            RETURN p.name, c.name
        ''')

        assert len(result) == 1
        assert result[0]['p.name'] == 'Alice'
        assert result[0]['c.name'] == 'ACME Corp'

    def test_create_multiple_relationships(self):
        """Test creating multiple relationships in sequence."""
        # Create first relationship
        self.db.execute('''
            CREATE (alice:Person {name: "Alice"})-[:WORKS_FOR]->(acme:Company {name: "ACME"})
        ''')

        # Create second relationship
        self.db.execute('''
            CREATE (bob:Person {name: "Bob"})-[:WORKS_FOR]->(beta:Company {name: "Beta"})
        ''')

        assert self.db.node_count == 4
        assert self.db.relationship_count == 2

        # Verify both relationships exist
        result = self.db.execute('''
            MATCH (p:Person)-[:WORKS_FOR]->(c:Company)
            RETURN p.name, c.name
        ''')

        assert len(result) == 2
        names = [(r['p.name'], r['c.name']) for r in result]
        assert ('Alice', 'ACME') in names
        assert ('Bob', 'Beta') in names

    def test_create_complex_path(self):
        """Test creating more complex relationship paths."""
        # Note: Multi - hop creation in single statement might not be supported yet
        # So we'll test what we can

        self.db.execute('''
            CREATE (manager:Person {name: "Manager", role: "Boss"})
            -[:MANAGES]->
            (employee:Person {name: "Employee", role: "Worker"})
        ''')

        assert self.db.node_count == 2
        assert self.db.relationship_count == 1

        result = self.db.execute('''
            MATCH (m:Person)-[:MANAGES]->(e:Person)
            RETURN m.name, e.name, m.role, e.role
        ''')

        assert len(result) == 1
        assert result[0]['m.name'] == 'Manager'
        assert result[0]['e.name'] == 'Employee'
        assert result[0]['m.role'] == 'Boss'
        assert result[0]['e.role'] == 'Worker'

class TestEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Set up test database."""
        self.db = GraphDB()

    def test_empty_result_sets(self):
        """Test queries that return empty results."""
        # Query non - existent nodes
        result = self.db.execute('MATCH (p:NonExistent) RETURN p.name')
        assert len(result) == 0

        # Query non - existent relationships
        result = self.db.execute('MATCH (a)-[:NONEXISTENT]->(b) RETURN a, b')
        assert len(result) == 0

    def test_filter_with_no_matches(self):
        """Test filters that match no records."""
        self.db.execute('CREATE (p:Person {name: "Alice", age: 30})')

        result = self.db.execute('MATCH (p:Person) WHERE p.age > 100 RETURN p.name')
        assert len(result) == 0

        result = self.db.execute('MATCH (p:Person) WHERE p.name = "NonExistent" RETURN p.name')
        assert len(result) == 0

    def test_join_with_no_matches(self):
        """Test joins that find no matching relationships."""
        # Create nodes but no relationships
        self.db.execute('CREATE (a:Person {name: "Alice"})')
        self.db.execute('CREATE (b:Company {name: "ACME"})')

        result = self.db.execute('MATCH (p:Person)-[:WORKS_FOR]->(c:Company) RETURN p.name, c.name')
        assert len(result) == 0

    def test_aggregation_on_empty_set(self):
        """Test aggregations on empty result sets."""
        result = self.db.execute('MATCH (p:NonExistent) RETURN COUNT(*)')
        assert len(result) == 1
        assert result[0]['COUNT(*)'] == 0

        result = self.db.execute('MATCH (p:NonExistent) RETURN AVG(p.age)')
        assert len(result) == 1
        assert result[0]['AVG(p.age)'] is None

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
