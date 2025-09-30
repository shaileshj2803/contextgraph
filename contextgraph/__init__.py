"""
ContextGraph: A powerful graph database with Cypher query support and advanced visualization capabilities.
"""

from .graphdb import GraphDB
from .cypher_parser import CypherParser
from .query_result import QueryResult, QueryRecord
from .transaction import Transaction, TransactionManager
from .csv_importer import CSVImporter
from .visualization import GraphVisualizer, install_dependencies
from .exceptions import (
    GraphDBError,
    CypherSyntaxError,
    NodeNotFoundError,
    RelationshipNotFoundError,
    TransactionError,
    PropertyError,
    SchemaError,
)

__version__ = "0.2.0"
__all__ = [
    "GraphDB",
    "CypherParser",
    "QueryResult",
    "QueryRecord",
    "Transaction",
    "TransactionManager",
    "CSVImporter",
    "GraphVisualizer",
    "install_dependencies",
    "GraphDBError",
    "CypherSyntaxError",
    "NodeNotFoundError",
    "RelationshipNotFoundError",
    "TransactionError",
    "PropertyError",
    "SchemaError",
]
