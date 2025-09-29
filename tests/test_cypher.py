"""
Tests for Cypher query functionality.
"""

import pytest

from contextgraph import GraphDB
from contextgraph.exceptions import CypherSyntaxError
from contextgraph.query_result import QueryResult, QueryRecord

class TestCypherQueries:
    """Test cases for Cypher query execution."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.db = GraphDB()

    def test_create_node_simple(self):
        """Test simple node creation with Cypher."""
        result = self.db.execute("CREATE (n)")
        assert isinstance(result, QueryResult)
        assert self.db.node_count == 1

    def test_create_node_with_label(self):
        """Test node creation with label."""
        result = self.db.execute("CREATE (n:Person)")
        assert self.db.node_count == 1

        # Verify the node was created with correct label
        nodes = self.db.find_nodes(labels=["Person"])
        assert len(nodes) == 1

    def test_create_node_with_properties(self):
        """Test node creation with properties."""
        result = self.db.execute("CREATE (n {name: 'Alice', age: 30})")
        assert self.db.node_count == 1

        # Verify the node was created with correct properties
        nodes = self.db.find_nodes(properties={"name": "Alice", "age": 30})
        assert len(nodes) == 1

    def test_create_node_with_label_and_properties(self):
        """Test node creation with both label and properties."""
        result = self.db.execute("CREATE (n:Person {name: 'Bob', age: 25})")
        assert self.db.node_count == 1

        # Verify the node was created correctly
        nodes = self.db.find_nodes(
            labels=["Person"], properties={"name": "Bob"})
        assert len(nodes) == 1
        assert nodes[0]["properties"]["age"] == 25

    def test_match_node_simple(self):
        """Test simple node matching."""
        # Create a node first
        self.db.create_node(labels=["Person"], properties={"name": "Alice"})

        # Match the node
        result = self.db.execute("MATCH (n:Person) RETURN n")
        assert len(result) == 1

    def test_match_node_with_properties(self):
        """Test node matching with property conditions."""
        # Create some nodes
        self.db.create_node(labels=["Person"], properties={"name": "Alice", "age": 30})
        self.db.create_node(labels=["Person"], properties={"name": "Bob", "age": 25})

        # Match nodes with specific property
        result = self.db.execute("MATCH (n:Person {name: 'Alice'}) RETURN n")
        assert len(result) == 1

    def test_return_property(self):
        """Test returning node properties."""
        # Create a node
        self.db.create_node(labels=["Person"], properties={"name": "Alice", "age": 30})

        # Return specific property
        result = self.db.execute("MATCH (n:Person) RETURN n.name")
        assert len(result) == 1
        # Note: The actual property access might need refinement in the parser

    def test_syntax_error(self):
        """Test that syntax errors are properly caught."""
        with pytest.raises(CypherSyntaxError):
            self.db.execute("INVALID CYPHER SYNTAX")

    def test_empty_result(self):
        """Test queries that return no results."""
        result = self.db.execute("MATCH (n:NonExistent) RETURN n")
        assert len(result) == 0
        assert bool(result) is False

    def test_multiple_creates(self):
        """Test creating multiple nodes in one query."""
        result = self.db.execute("CREATE (a:Person), (b:Company)")
        assert self.db.node_count == 2

        # Verify both nodes were created
        person_nodes = self.db.find_nodes(labels=["Person"])
        company_nodes = self.db.find_nodes(labels=["Company"])
        assert len(person_nodes) == 1
        assert len(company_nodes) == 1

class TestQueryResult:
    """Test cases for QueryResult class."""

    def test_empty_result(self):
        """Test empty query result."""
        result = QueryResult([], [])
        assert len(result) == 0
        assert bool(result) is False
        assert result.columns == []
        assert result.records == []

    def test_result_with_data(self):
        """Test query result with data."""
        columns = ["name", "age"]
        records = [["Alice", 30], ["Bob", 25]]
        result = QueryResult(columns, records)

        assert len(result) == 2
        assert bool(result) is True
        assert result.columns == columns
        assert len(result.records) == 2

    def test_result_iteration(self):
        """Test iterating over query results."""
        columns = ["name", "age"]
        records = [["Alice", 30], ["Bob", 25]]
        result = QueryResult(columns, records)

        records_list = list(result)
        assert len(records_list) == 2
        assert all(isinstance(record, QueryRecord) for record in records_list)

    def test_result_indexing(self):
        """Test indexing query results."""
        columns = ["name", "age"]
        records = [["Alice", 30], ["Bob", 25]]
        result = QueryResult(columns, records)

        first_record = result[0]
        assert isinstance(first_record, QueryRecord)
        assert first_record["name"] == "Alice"
        assert first_record["age"] == 30

    def test_result_indexing_out_of_bounds(self):
        """Test indexing out of bounds."""
        result = QueryResult(["name"], [["Alice"]])

        with pytest.raises(IndexError):
            _ = result[1]

    def test_to_dict_list(self):
        """Test converting result to list of dictionaries."""
        columns = ["name", "age"]
        records = [["Alice", 30], ["Bob", 25]]
        result = QueryResult(columns, records)

        dict_list = result.to_dict_list()
        expected = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        assert dict_list == expected

    def test_to_table(self):
        """Test converting result to table string."""
        columns = ["name", "age"]
        records = [["Alice", 30], ["Bob", 25]]
        result = QueryResult(columns, records)

        table_str = result.to_table()
        assert "name" in table_str
        assert "age" in table_str
        assert "Alice" in table_str
        assert "Bob" in table_str

    def test_to_table_empty(self):
        """Test converting empty result to table string."""
        result = QueryResult([], [])
        table_str = result.to_table()
        assert table_str == "No records found."

    def test_single_record(self):
        """Test getting single record."""
        columns = ["name"]
        records = [["Alice"]]
        result = QueryResult(columns, records)

        single_record = result.single()
        assert isinstance(single_record, QueryRecord)
        assert single_record["name"] == "Alice"

    def test_single_record_empty(self):
        """Test getting single record from empty result."""
        result = QueryResult([], [])
        single_record = result.single()
        assert single_record is None

    def test_single_record_multiple(self):
        """Test getting single record when multiple exist."""
        columns = ["name"]
        records = [["Alice"], ["Bob"]]
        result = QueryResult(columns, records)

        with pytest.raises(ValueError, match="Expected single record, got 2"):
            result.single()

    def test_value_single_column(self):
        """Test getting single value from single column result."""
        columns = ["count"]
        records = [[42]]
        result = QueryResult(columns, records)

        value = result.value()
        assert value == 42

    def test_value_specific_column(self):
        """Test getting value from specific column."""
        columns = ["name", "age"]
        records = [["Alice", 30]]
        result = QueryResult(columns, records)

        name_value = result.value("name")
        age_value = result.value("age")
        assert name_value == "Alice"
        assert age_value == 30

    def test_value_no_records(self):
        """Test getting value when no records exist."""
        result = QueryResult(["name"], [])

        with pytest.raises(ValueError, match="No records found"):
            result.value()

    def test_value_multiple_columns_no_column_specified(self):
        """Test getting value when multiple columns exist but none specified."""
        columns = ["name", "age"]
        records = [["Alice", 30]]
        result = QueryResult(columns, records)

        with pytest.raises(ValueError, match="Expected single column, got 2"):
            result.value()

class TestQueryRecord:
    """Test cases for QueryRecord class."""

    def test_record_creation(self):
        """Test creating a query record."""
        columns = ["name", "age"]
        values = ["Alice", 30]
        record = QueryRecord(columns, values)

        assert record["name"] == "Alice"
        assert record["age"] == 30
        assert len(record) == 2

    def test_record_creation_mismatched_lengths(self):
        """Test creating record with mismatched column / value lengths."""
        with pytest.raises(ValueError, match="Column count .* doesn't match value count"):
            QueryRecord(["name"], ["Alice", 30])

    def test_record_iteration(self):
        """Test iterating over record columns."""
        columns = ["name", "age"]
        values = ["Alice", 30]
        record = QueryRecord(columns, values)

        column_list = list(record)
        assert column_list == columns

    def test_record_contains(self):
        """Test checking if record contains a column."""
        columns = ["name", "age"]
        values = ["Alice", 30]
        record = QueryRecord(columns, values)

        assert "name" in record
        assert "age" in record
        assert "height" not in record

    def test_record_get(self):
        """Test getting values with default."""
        columns = ["name", "age"]
        values = ["Alice", 30]
        record = QueryRecord(columns, values)

        assert record.get("name") == "Alice"
        assert record.get("height", "unknown") == "unknown"

    def test_record_keys_values_items(self):
        """Test keys, values, and items methods."""
        columns = ["name", "age"]
        values = ["Alice", 30]
        record = QueryRecord(columns, values)

        assert list(record.keys()) == columns
        assert list(record.values()) == values
        assert list(record.items()) == [("name", "Alice"), ("age", 30)]

    def test_record_to_dict(self):
        """Test converting record to dictionary."""
        columns = ["name", "age"]
        values = ["Alice", 30]
        record = QueryRecord(columns, values)

        record_dict = record.to_dict()
        expected = {"name": "Alice", "age": 30}
        assert record_dict == expected

    def test_record_repr(self):
        """Test string representation of record."""
        columns = ["name", "age"]
        values = ["Alice", 30]
        record = QueryRecord(columns, values)

        repr_str = repr(record)
        assert "QueryRecord" in repr_str
        assert "name='Alice'" in repr_str
        assert "age=30" in repr_str
