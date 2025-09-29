"""
Custom exceptions for the igraph - cypher - db library.
"""

class GraphDBError(Exception):
    """Base exception for all graph database errors."""
    pass

class CypherSyntaxError(GraphDBError):
    """Raised when there's a syntax error in a Cypher query."""
    pass

class NodeNotFoundError(GraphDBError):
    """Raised when a requested node is not found."""
    pass

class RelationshipNotFoundError(GraphDBError):
    """Raised when a requested relationship is not found."""
    pass

class TransactionError(GraphDBError):
    """Raised when there's an error during transaction processing."""
    pass

class PropertyError(GraphDBError):
    """Raised when there's an error with node or relationship properties."""
    pass

class SchemaError(GraphDBError):
    """Raised when there's an error with the graph schema."""
    pass
