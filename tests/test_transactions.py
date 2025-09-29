"""
Tests for transaction functionality.
"""

import pytest

from contextgraph import GraphDB
from contextgraph.exceptions import TransactionError

class TestTransactions:
    """Test cases for transaction functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.db = GraphDB()

    def test_transaction_manager_initialization(self):
        """Test that transaction manager is properly initialized."""
        assert self.db.transaction_manager is not None
        assert not self.db.transaction_manager.has_active_transaction

    def test_begin_commit_transaction(self):
        """Test basic transaction begin and commit."""
        # Begin transaction
        transaction = self.db.transaction_manager.begin_transaction()
        assert transaction is not None
        assert transaction.is_active
        assert self.db.transaction_manager.has_active_transaction

        # Perform operations
        node_id = self.db.create_node(labels=["Person"], properties={"name": "Alice"})
        assert self.db.node_count == 1

        # Commit transaction
        self.db.transaction_manager.commit_transaction()
        assert not transaction.is_active
        assert transaction.is_committed
        assert not self.db.transaction_manager.has_active_transaction

        # Verify data persists after commit
        assert self.db.node_count == 1
        node = self.db.get_node(node_id)
        assert node is not None
        assert node["properties"]["name"] == "Alice"

    def test_begin_rollback_transaction(self):
        """Test transaction rollback."""
        # Create initial data
        initial_node_id = self.db.create_node(labels=["Person"], properties={"name": "Bob"})
        assert self.db.node_count == 1

        # Begin transaction
        transaction = self.db.transaction_manager.begin_transaction()
        assert transaction.is_active

        # Perform operations in transaction
        new_node_id = self.db.create_node(labels=["Person"], properties={"name": "Alice"})
        rel_id = self.db.create_relationship(initial_node_id, new_node_id, "KNOWS")

        # Verify operations were applied
        assert self.db.node_count == 2
        assert self.db.relationship_count == 1

        # Rollback transaction
        self.db.transaction_manager.rollback_transaction()
        assert not transaction.is_active
        assert transaction.is_rolled_back
        assert not self.db.transaction_manager.has_active_transaction

        # Verify data was rolled back
        assert self.db.node_count == 1
        assert self.db.relationship_count == 0

        # Original data should still exist
        node = self.db.get_node(initial_node_id)
        assert node is not None
        assert node["properties"]["name"] == "Bob"

        # New data should be gone
        assert self.db.get_node(new_node_id) is None
        assert self.db.get_relationship(rel_id) is None

    def test_transaction_context_manager_success(self):
        """Test transaction context manager with successful operations."""
        initial_count = self.db.node_count

        with self.db.transaction_manager.transaction():
            node1_id = self.db.create_node(labels=["Person"], properties={"name": "Alice"})
            node2_id = self.db.create_node(labels=["Person"], properties={"name": "Bob"})
            _ = self.db.create_relationship(node1_id, node2_id, "KNOWS")  # noqa: F841

            # Operations should be visible within transaction
            assert self.db.node_count == initial_count + 2
            assert self.db.relationship_count == 1

        # After successful completion, changes should be committed
        assert self.db.node_count == initial_count + 2
        assert self.db.relationship_count == 1
        assert not self.db.transaction_manager.has_active_transaction

    def test_transaction_context_manager_exception(self):
        """Test transaction context manager with exception (rollback)."""
        # Create initial data
        initial_node_id = self.db.create_node(labels=["Person"], properties={"name": "Initial"})
        initial_count = self.db.node_count

        with pytest.raises(ValueError, match="Test exception"):
            with self.db.transaction_manager.transaction():
                # Perform operations
                self.db.create_node(labels=["Person"], properties={"name": "Alice"})
                self.db.create_node(labels=["Person"], properties={"name": "Bob"})

                # Operations should be visible within transaction
                assert self.db.node_count == initial_count + 2

                # Raise an exception to trigger rollback
                raise ValueError("Test exception")

        # After exception, changes should be rolled back
        assert self.db.node_count == initial_count
        assert self.db.relationship_count == 0
        assert not self.db.transaction_manager.has_active_transaction

        # Initial data should still exist
        node = self.db.get_node(initial_node_id)
        assert node is not None
        assert node["properties"]["name"] == "Initial"

    def test_nested_transaction_error(self):
        """Test that nested transactions are not allowed."""
        transaction1 = self.db.transaction_manager.begin_transaction()
        assert transaction1.is_active

        with pytest.raises(TransactionError, match="A transaction is already active"):
            self.db.transaction_manager.begin_transaction()

        # Clean up
        self.db.transaction_manager.rollback_transaction()

    def test_commit_without_active_transaction(self):
        """Test committing without an active transaction."""
        with pytest.raises(TransactionError, match="No active transaction to commit"):
            self.db.transaction_manager.commit_transaction()

    def test_rollback_without_active_transaction(self):
        """Test rolling back without an active transaction."""
        with pytest.raises(TransactionError, match="No active transaction to rollback"):
            self.db.transaction_manager.rollback_transaction()

    def test_transaction_double_begin(self):
        """Test that beginning a transaction twice fails."""
        transaction = self.db.transaction_manager.begin_transaction()

        with pytest.raises(TransactionError, match="Transaction is already active"):
            transaction.begin()

        # Clean up
        self.db.transaction_manager.rollback_transaction()

    def test_transaction_double_commit(self):
        """Test that committing a transaction twice fails."""
        transaction = self.db.transaction_manager.begin_transaction()
        self.db.transaction_manager.commit_transaction()

        with pytest.raises(TransactionError, match="Transaction has already been completed"):
            transaction.begin()

    def test_transaction_operations_after_commit(self):
        """Test that operations after commit don't affect the transaction."""
        # Begin and commit transaction
        transaction = self.db.transaction_manager.begin_transaction()
        node_id = self.db.create_node(labels=["Person"], properties={"name": "Alice"})
        self.db.transaction_manager.commit_transaction()

        # Operations after commit should work normally
        node2_id = self.db.create_node(labels=["Person"], properties={"name": "Bob"})

        assert self.db.node_count == 2
        assert self.db.get_node(node_id) is not None
        assert self.db.get_node(node2_id) is not None

    def test_complex_transaction_rollback(self):
        """Test rollback of complex operations."""
        # Create initial state
        person1_id = self.db.create_node(labels=["Person"], properties={"name": "Alice"})
        person2_id = self.db.create_node(labels=["Person"], properties={"name": "Bob"})
        initial_rel_id = self.db.create_relationship(person1_id, person2_id, "KNOWS")

        initial_node_count = self.db.node_count
        initial_rel_count = self.db.relationship_count

        # Begin transaction and perform complex operations
        transaction = self.db.transaction_manager.begin_transaction()

        # Add new nodes
        person3_id = self.db.create_node(labels=["Person"], properties={"name": "Charlie"})
        company_id = self.db.create_node(labels=["Company"], properties={"name": "ACME"})

        # Add new relationships
        rel1_id = self.db.create_relationship(person1_id, company_id, "WORKS_FOR")
        rel2_id = self.db.create_relationship(person3_id, company_id, "WORKS_FOR")
        rel3_id = self.db.create_relationship(person1_id, person3_id, "KNOWS")

        # Modify existing data (delete a relationship)
        self.db.delete_relationship(initial_rel_id)

        # Verify intermediate state
        assert self.db.node_count == initial_node_count + 2
        assert self.db.relationship_count == initial_rel_count + 2  # Added 3, deleted 1

        # Rollback
        self.db.transaction_manager.rollback_transaction()

        # Verify rollback
        assert self.db.node_count == initial_node_count
        assert self.db.relationship_count == initial_rel_count

        # Original data should be restored
        assert self.db.get_node(person1_id) is not None
        assert self.db.get_node(person2_id) is not None
        assert self.db.get_relationship(initial_rel_id) is not None

        # New data should be gone
        assert self.db.get_node(person3_id) is None
        assert self.db.get_node(company_id) is None
        assert self.db.get_relationship(rel1_id) is None
        assert self.db.get_relationship(rel2_id) is None
        assert self.db.get_relationship(rel3_id) is None
