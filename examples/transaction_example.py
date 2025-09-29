#!/usr / bin / env python3
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import contextgraph
sys.path.insert(0, str(Path(__file__).parent.parent))
"""
Transaction Example for igraph - cypher - db.

This example demonstrates the transaction functionality including:
- Basic transaction operations (begin, commit, rollback)
- Context manager usage
- Error handling and rollback scenarios
"""

from contextgraph import GraphDB
from contextgraph.exceptions import TransactionError

def demonstrate_basic_transactions():
    """Demonstrate basic transaction operations."""
    print("=== Basic Transaction Operations ===\n")

    db = GraphDB()

    # Create some initial data
    print("1. Creating initial data...")
    alice_id = db.create_node(labels=["Person"], properties={"name": "Alice", "age": 30})
    bob_id = db.create_node(labels=["Person"], properties={"name": "Bob", "age": 25})
    print(f"   Created initial nodes: Alice (ID: {alice_id}), Bob (ID: {bob_id})")
    print(f"   Initial state: {db.node_count} nodes, {db.relationship_count} relationships\n")

    # Demonstrate successful transaction
    print("2. Demonstrating successful transaction...")
    transaction = db.transaction_manager.begin_transaction()
    print("   Transaction started")

    # Perform operations within transaction
    charlie_id = db.create_node(labels=["Person"], properties={"name": "Charlie", "age": 35})
    rel1_id = db.create_relationship(alice_id, charlie_id, "KNOWS", {"since": "2020"})
    _ = db.create_relationship(bob_id, charlie_id, "KNOWS", {"since": "2021"})  # noqa: F841

    print(f"   Added Charlie (ID: {charlie_id}) and relationships")
    print(f"   Transaction state: {db.node_count} nodes, {db.relationship_count} relationships")

    # Commit transaction
    db.transaction_manager.commit_transaction()
    print("   Transaction committed")
    print(f"   Final state: {db.node_count} nodes, {db.relationship_count} relationships\n")

    # Demonstrate rollback transaction
    print("3. Demonstrating transaction rollback...")
    transaction = db.transaction_manager.begin_transaction()
    print("   Transaction started")

    # Perform operations within transaction
    diana_id = db.create_node(labels=["Person"], properties={"name": "Diana", "age": 28})
    eve_id = db.create_node(labels=["Person"], properties={"name": "Eve", "age": 32})
    rel3_id = db.create_relationship(diana_id, eve_id, "KNOWS")

    print(f"   Added Diana (ID: {diana_id}), Eve (ID: {eve_id}) and relationship")
    print(f"   Transaction state: {db.node_count} nodes, {db.relationship_count} relationships")

    # Rollback transaction
    db.transaction_manager.rollback_transaction()
    print("   Transaction rolled back")
    print(f"   Final state: {db.node_count} nodes, {db.relationship_count} relationships")

    # Verify rollback worked
    assert db.get_node(diana_id) is None
    assert db.get_node(eve_id) is None
    assert db.get_relationship(rel3_id) is None
    print("   Rollback verified: Diana, Eve, and their relationship are gone\n")

def demonstrate_context_manager():
    """Demonstrate transaction context manager."""
    print("=== Transaction Context Manager ===\n")

    db = GraphDB()

    # Create initial data
    alice_id = db.create_node(labels=["Person"], properties={"name": "Alice"})
    print(f"Initial state: {db.node_count} nodes, {db.relationship_count} relationships")

    # Successful transaction using context manager
    print("\n1. Successful transaction with context manager...")
    try:
        with db.transaction_manager.transaction():
            bob_id = db.create_node(labels=["Person"], properties={"name": "Bob"})
            charlie_id = db.create_node(labels=["Company"], properties={"name": "ACME Corp"})
            _ = db.create_relationship(alice_id, bob_id, "KNOWS")  # noqa: F841

            print(f"   Within transaction: {db.node_count} nodes, {db.relationship_count} relationships")
            # Transaction automatically commits here

        print(f"   After commit: {db.node_count} nodes, {db.relationship_count} relationships")
        print("   Transaction committed successfully\n")

    except Exception as e:
        print(f"   Transaction failed: {e}")

    # Failed transaction using context manager
    print("2. Failed transaction with context manager (automatic rollback)...")
    initial_node_count = db.node_count
    initial_rel_count = db.relationship_count

    try:
        with db.transaction_manager.transaction():
            # Add some data
            diana_id = db.create_node(labels=["Person"], properties={"name": "Diana"})
            eve_id = db.create_node(labels=["Person"], properties={"name": "Eve"})
            _ = db.create_relationship(diana_id, eve_id, "KNOWS")  # noqa: F841

            print(f"   Within transaction: {db.node_count} nodes, {db.relationship_count} relationships")

            # Simulate an error
            raise ValueError("Simulated error to trigger rollback")

    except ValueError as e:
        print(f"   Exception caught: {e}")
        print(f"   After rollback: {db.node_count} nodes, {db.relationship_count} relationships")

        # Verify rollback
        assert db.node_count == initial_node_count
        assert db.relationship_count == initial_rel_count
        print("   Automatic rollback verified\n")

def demonstrate_complex_scenario():
    """Demonstrate a complex transaction scenario."""
    print("=== Complex Transaction Scenario ===\n")

    db = GraphDB()

    # Create a company structure
    print("1. Setting up initial company structure...")

    # Create employees
    alice_id = db.create_node(labels=["Person", "Employee"],
                             properties={"name": "Alice", "role": "Engineer", "salary": 80000})
    bob_id = db.create_node(labels=["Person", "Employee"],
                           properties={"name": "Bob", "role": "Designer", "salary": 75000})
    charlie_id = db.create_node(labels=["Person", "Manager"],
                               properties={"name": "Charlie", "role": "Manager", "salary": 100000})

    # Create company
    company_id = db.create_node(labels=["Company"],
                               properties={"name": "TechCorp", "industry": "Software"})

    # Create relationships
    db.create_relationship(alice_id, company_id, "WORKS_FOR", {"department": "Engineering"})
    db.create_relationship(bob_id, company_id, "WORKS_FOR", {"department": "Design"})
    db.create_relationship(charlie_id, company_id, "WORKS_FOR", {"department": "Management"})
    db.create_relationship(charlie_id, alice_id, "MANAGES")
    db.create_relationship(charlie_id, bob_id, "MANAGES")

    print(f"   Initial setup: {db.node_count} nodes, {db.relationship_count} relationships")

    # Simulate a complex business operation: promoting Alice to manager
    print("\n2. Simulating Alice's promotion to manager (complex transaction)...")

    try:
        with db.transaction_manager.transaction():
            print("   Starting promotion transaction...")

            # Update Alice's properties
            alice_node = db.get_node(alice_id)
            if alice_node:
                # In a real implementation, we'd have an update_node method
                # For now, we'll simulate by deleting and recreating
                db.delete_node(alice_id)
                new_alice_id = db.create_node(
                    labels=["Person", "Manager"],
                    properties={"name": "Alice", "role": "Senior Manager", "salary": 95000}
                )

                # Update relationships
                db.create_relationship(new_alice_id, company_id, "WORKS_FOR",
                                     {"department": "Engineering"})

                # Alice now manages Bob instead of being managed by Charlie
                db.create_relationship(new_alice_id, bob_id, "MANAGES")

                # Create a new junior engineer to replace Alice's old role
                junior_id = db.create_node(
                    labels=["Person", "Employee"],
                    properties={"name": "David", "role": "Junior Engineer", "salary": 60000}
                )
                db.create_relationship(junior_id, company_id, "WORKS_FOR",
                                     {"department": "Engineering"})
                db.create_relationship(new_alice_id, junior_id, "MANAGES")

                print("   Transaction operations completed")
                print(f"   Current state: {db.node_count} nodes, {db.relationship_count} relationships")

                # Simulate validation - check if budget allows the changes
                total_salary = 95000 + 75000 + 100000 + 60000  # Alice + Bob + Charlie + David
                budget_limit = 350000

                if total_salary > budget_limit:
                    raise ValueError(f"Salary budget exceeded: {total_salary} > {budget_limit}")

                print("   Budget validation passed")

            # Transaction commits automatically here

        print("   Promotion transaction completed successfully!")
        print(f"   Final state: {db.node_count} nodes, {db.relationship_count} relationships")

        # Verify the changes
        managers = db.find_nodes(labels=["Manager"])
        print(f"   Managers in system: {len(managers)}")
        for manager in managers:
            print(f"     - {manager['properties']['name']} ({manager['properties']['role']})")

    except Exception as e:
        print(f"   Promotion transaction failed: {e}")
        print(f"   State after rollback: {db.node_count} nodes, {db.relationship_count} relationships")
        print("   All changes have been rolled back")

def demonstrate_error_handling():
    """Demonstrate error handling in transactions."""
    print("=== Transaction Error Handling ===\n")

    db = GraphDB()

    # Try to commit without starting a transaction
    print("1. Testing commit without active transaction...")
    try:
        db.transaction_manager.commit_transaction()
    except TransactionError as e:
        print(f"   Expected error caught: {e}")

    # Try to rollback without starting a transaction
    print("\n2. Testing rollback without active transaction...")
    try:
        db.transaction_manager.rollback_transaction()
    except TransactionError as e:
        print(f"   Expected error caught: {e}")

    # Try to start nested transactions
    print("\n3. Testing nested transactions...")
    try:
        transaction1 = db.transaction_manager.begin_transaction()
        print("   First transaction started")

        try:
            transaction2 = db.transaction_manager.begin_transaction()
        except TransactionError as e:
            print(f"   Expected error caught: {e}")

        # Clean up
        db.transaction_manager.rollback_transaction()
        print("   First transaction rolled back")

    except Exception as e:
        print(f"   Unexpected error: {e}")

def main():
    """Main function to run all transaction examples."""
    print("=== igraph - cypher - db Transaction Examples ===\n")

    demonstrate_basic_transactions()
    demonstrate_context_manager()
    demonstrate_complex_scenario()
    demonstrate_error_handling()

    print("\n=== All transaction examples completed! ===")
    print("\nKey takeaways:")
    print("- Transactions provide ACID guarantees for graph operations")
    print("- Use context managers for automatic commit / rollback")
    print("- Failed operations automatically trigger rollback")
    print("- Complex business logic can be safely wrapped in transactions")

if __name__ == "__main__":
    main()
