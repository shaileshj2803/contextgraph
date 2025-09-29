#!/usr/bin/env python3
"""
Basic usage example for ContextGraph.

This example demonstrates the fundamental operations of the graph database:
- Creating nodes and relationships
- Querying with Cypher
- Basic graph operations
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import contextgraph
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextgraph import GraphDB

def main():
    """Demonstrate basic usage of the graph database."""
    print("=== ContextGraph Basic Usage Example ===\n")

    # Create a new graph database
    print("1. Creating a new graph database...")
    db = GraphDB()
    print(f"   Database created (directed: {db.is_directed})")
    print(f"   Initial state: {db.node_count} nodes, {db.relationship_count} relationships\n")

    # Create nodes using the API
    print("2. Creating nodes using the API...")
    alice_id = db.create_node(
        labels=["Person"],
        properties={"name": "Alice", "age": 30, "city": "New York"}
    )
    bob_id = db.create_node(
        labels=["Person"],
        properties={"name": "Bob", "age": 25, "city": "San Francisco"}
    )
    acme_id = db.create_node(
        labels=["Company"],
        properties={"name": "ACME Corp", "industry": "Technology"}
    )
    print(f"   Created nodes: Alice (ID: {alice_id}), Bob (ID: {bob_id}), ACME Corp (ID: {acme_id})")
    print(f"   Current state: {db.node_count} nodes, {db.relationship_count} relationships\n")

    # Create relationships using the API
    print("3. Creating relationships using the API...")
    knows_rel_id = db.create_relationship(
        alice_id, bob_id, "KNOWS",
        {"since": "2020", "strength": "strong"}
    )
    works_rel_id = db.create_relationship(
        alice_id, acme_id, "WORKS_FOR",
        {"position": "Engineer", "since": "2019"}
    )
    print(f"   Created relationships: KNOWS (ID: {knows_rel_id}), WORKS_FOR (ID: {works_rel_id})")
    print(f"   Current state: {db.node_count} nodes, {db.relationship_count} relationships\n")

    # Create nodes using Cypher
    print("4. Creating nodes using Cypher...")
    result = db.execute("CREATE (c:Person {name: 'Charlie', age: 35, city: 'New York'})")
    print("   Cypher CREATE executed successfully")
    print(f"   Current state: {db.node_count} nodes, {db.relationship_count} relationships\n")

    # Query nodes using the API
    print("5. Querying nodes using the API...")
    person_nodes = db.find_nodes(labels=["Person"])
    print(f"   Found {len(person_nodes)} Person nodes:")
    for node in person_nodes:
        print(f"     - {node['properties']['name']} (age: {node['properties']['age']})")
    print()

    # Query nodes using Cypher
    print("6. Querying nodes using Cypher...")
    try:
        result = db.execute("MATCH (p:Person) RETURN p")
        print("   Cypher MATCH executed successfully")
        print(f"   Found {len(result)} records")
        if len(result) > 0:
            print("   Result columns:", result.columns)
            print("   Sample record:", dict(result[0]) if result else "None")
    except Exception as e:
        print(f"   Cypher query failed: {e}")
    print()

    # Find relationships
    print("7. Querying relationships...")
    all_relationships = db.find_relationships()
    print(f"   Found {len(all_relationships)} relationships:")
    for rel in all_relationships:
        source_node = db.get_node(rel['source'])
        target_node = db.get_node(rel['target'])
        source_name = source_node['properties'].get('name', 'Unknown')
        target_name = target_node['properties'].get('name', 'Unknown')
        print(f"     - {source_name} -{rel['type']}-> {target_name}")
    print()

    # Demonstrate save / load functionality
    print("8. Demonstrating save / load functionality...")
    save_path = "example_graph.json"
    db.save(save_path)
    print(f"   Database saved to {save_path}")

    # Create a new database and load the data
    new_db = GraphDB()
    new_db.load(save_path)
    print(f"   Database loaded from {save_path}")
    print(f"   Loaded state: {new_db.node_count} nodes, {new_db.relationship_count} relationships")

    # Verify the loaded data
    loaded_persons = new_db.find_nodes(labels=["Person"])
    print(f"   Verified: {len(loaded_persons)} Person nodes loaded correctly")
    print()

    # Clean up
    import os
    if os.path.exists(save_path):
        os.remove(save_path)
        print(f"   Cleaned up: removed {save_path}")

    print("=== Example completed successfully! ===")

if __name__ == "__main__":
    main()
