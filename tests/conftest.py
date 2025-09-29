"""
Pytest configuration and fixtures.
"""

import pytest
from contextgraph import GraphDB

@pytest.fixture
def empty_db():
    """Provide an empty GraphDB instance for testing."""
    return GraphDB()

@pytest.fixture
def sample_db():
    """Provide a GraphDB instance with sample data."""
    db = GraphDB()

    # Create some sample nodes
    alice_id = db.create_node(
        labels=["Person"],
        properties={"name": "Alice", "age": 30, "city": "New York"}
    )
    bob_id = db.create_node(
        labels=["Person"],
        properties={"name": "Bob", "age": 25, "city": "San Francisco"}
    )
    charlie_id = db.create_node(
        labels=["Person"],
        properties={"name": "Charlie", "age": 35, "city": "New York"}
    )
    acme_id = db.create_node(
        labels=["Company"],
        properties={"name": "ACME Corp", "industry": "Technology"}
    )

    # Create some relationships
    db.create_relationship(
        alice_id, bob_id, "KNOWS",
        {"since": "2020", "strength": "strong"}
    )
    db.create_relationship(
        alice_id, charlie_id, "KNOWS",
        {"since": "2018", "strength": "medium"}
    )
    db.create_relationship(
        alice_id, acme_id, "WORKS_FOR",
        {"position": "Engineer", "since": "2019"}
    )
    db.create_relationship(
        bob_id, acme_id, "WORKS_FOR",
        {"position": "Designer", "since": "2021"}
    )

    return db
