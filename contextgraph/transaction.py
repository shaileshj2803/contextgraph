"""
Transaction support for the graph database.
"""

import copy
from typing import Any, Dict, List, Optional, Callable
from contextlib import contextmanager

from .exceptions import TransactionError

class Transaction:
    """
    Represents a database transaction.

    This class provides ACID transaction support by maintaining a log of
    operations and allowing rollback if needed.
    """

    def __init__(self, graph_db):
        """
        Initialize a new transaction.

        Args:
            graph_db: The GraphDB instance this transaction operates on
        """
        self.graph_db = graph_db
        self.operations = []
        self.is_active = False
        self.is_committed = False
        self.is_rolled_back = False

        # Store the initial state for rollback
        self._initial_state = None

    def begin(self):
        """Begin the transaction."""
        if self.is_active:
            raise TransactionError("Transaction is already active")

        if self.is_committed or self.is_rolled_back:
            raise TransactionError("Transaction has already been completed")

        # Store the current state for potential rollback
        self._initial_state = self._capture_state()
        self.is_active = True

    def commit(self):
        """Commit the transaction."""
        if not self.is_active:
            raise TransactionError("No active transaction to commit")

        try:
            # All operations have already been applied to the graph
            # Just mark as committed
            self.is_committed = True
            self.is_active = False

        except Exception as e:
            # If commit fails, try to rollback
            self._rollback_internal()
            raise TransactionError(f"Failed to commit transaction: {str(e)}")

    def rollback(self):
        """Rollback the transaction."""
        if not self.is_active:
            raise TransactionError("No active transaction to rollback")

        self._rollback_internal()

    def _rollback_internal(self):
        """Internal rollback implementation."""
        try:
            # Restore the initial state
            if self._initial_state is not None:
                self._restore_state(self._initial_state)

            self.is_rolled_back = True
            self.is_active = False

        except Exception as e:
            raise TransactionError(f"Failed to rollback transaction: {str(e)}")

    def _capture_state(self) -> Dict[str, Any]:
        """Capture the current state of the graph database."""
        state = {
            'node_id_counter': self.graph_db._node_id_counter,
            'relationship_id_counter': self.graph_db._relationship_id_counter,
            'nodes': [],
            'relationships': []
        }

        # Capture all nodes
        for vertex in self.graph_db._graph.vs:
            state['nodes'].append({
                'id': vertex['id'],
                'labels': copy.deepcopy(vertex['labels']),
                'properties': copy.deepcopy(vertex['properties'])
            })

        # Capture all relationships
        for edge in self.graph_db._graph.es:
            state['relationships'].append({
                'id': edge['id'],
                'type': edge['type'],
                'properties': copy.deepcopy(edge['properties']),
                'source': self.graph_db._graph.vs[edge.source]['id'],
                'target': self.graph_db._graph.vs[edge.target]['id']
            })

        return state

    def _restore_state(self, state: Dict[str, Any]):
        """Restore the graph database to a previous state."""
        # Clear the current graph
        self.graph_db.clear()

        # Restore counters
        self.graph_db._node_id_counter = state['node_id_counter']
        self.graph_db._relationship_id_counter = state['relationship_id_counter']

        # Restore nodes
        node_id_to_index = {}
        for node_data in state['nodes']:
            self.graph_db._graph.add_vertex()
            vertex_index = self.graph_db._graph.vcount() - 1

            self.graph_db._graph.vs[vertex_index]['id'] = node_data['id']
            self.graph_db._graph.vs[vertex_index]['labels'] = node_data['labels']
            self.graph_db._graph.vs[vertex_index]['properties'] = node_data['properties']

            node_id_to_index[node_data['id']] = vertex_index
            # Update the optimized lookup table
            self.graph_db._node_id_to_vertex_index[node_data['id']] = vertex_index

        # Restore relationships
        for rel_data in state['relationships']:
            source_index = node_id_to_index[rel_data['source']]
            target_index = node_id_to_index[rel_data['target']]

            self.graph_db._graph.add_edge(source_index, target_index)
            edge_index = self.graph_db._graph.ecount() - 1

            self.graph_db._graph.es[edge_index]['id'] = rel_data['id']
            self.graph_db._graph.es[edge_index]['type'] = rel_data['type']
            self.graph_db._graph.es[edge_index]['properties'] = rel_data['properties']

    def execute(self, operation: Callable, *args, **kwargs) -> Any:
        """
        Execute an operation within this transaction.

        Args:
            operation: The operation to execute
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            The result of the operation
        """
        if not self.is_active:
            raise TransactionError("No active transaction")

        try:
            _ = operation(*args, **kwargs)  # noqa: F841

            # Log the operation for potential rollback
            self.operations.append({
                'operation': operation,
                'args': args,
                'kwargs': kwargs,
                'result': result
            })

            return result

        except Exception as e:
            # If operation fails, rollback the transaction
            self._rollback_internal()
            raise TransactionError(f"Operation failed, transaction rolled back: {str(e)}")

class TransactionManager:
    """
    Manages transactions for the graph database.
    """

    def __init__(self, graph_db):
        """
        Initialize the transaction manager.

        Args:
            graph_db: The GraphDB instance to manage transactions for
        """
        self.graph_db = graph_db
        self.current_transaction = None

    def begin_transaction(self) -> Transaction:
        """
        Begin a new transaction.

        Returns:
            The new transaction instance

        Raises:
            TransactionError: If a transaction is already active
        """
        if self.current_transaction is not None and self.current_transaction.is_active:
            raise TransactionError("A transaction is already active")

        self.current_transaction = Transaction(self.graph_db)
        self.current_transaction.begin()
        return self.current_transaction

    def commit_transaction(self):
        """Commit the current transaction."""
        if self.current_transaction is None or not self.current_transaction.is_active:
            raise TransactionError("No active transaction to commit")

        self.current_transaction.commit()
        self.current_transaction = None

    def rollback_transaction(self):
        """Rollback the current transaction."""
        if self.current_transaction is None or not self.current_transaction.is_active:
            raise TransactionError("No active transaction to rollback")

        self.current_transaction.rollback()
        self.current_transaction = None

    @contextmanager
    def transaction(self):
        """
        Context manager for transactions.

        Usage:
            with db.transaction_manager.transaction():
                # Perform operations
                db.create_node(...)
                db.create_relationship(...)
                # Automatically commits on success, rolls back on exception
        """
        transaction = self.begin_transaction()
        try:
            yield transaction
            self.commit_transaction()
        except Exception:
            if transaction.is_active:
                self.rollback_transaction()
            raise

    @property
    def has_active_transaction(self) -> bool:
        """Check if there's an active transaction."""
        return (self.current_transaction is not None and
                self.current_transaction.is_active)
