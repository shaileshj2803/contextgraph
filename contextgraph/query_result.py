"""
Query result handling for Cypher queries.
"""

from typing import Any, Dict, List, Optional, Iterator
from collections.abc import Mapping

class QueryResult:
    """
    Represents the result of a Cypher query execution.

    This class provides an interface to access query results in a structured
    way, supporting both record - based iteration and column - based access.
    """

    def __init__(self, columns: List[str], records: List[List[Any]],
                 summary: Optional[Dict[str, Any]] = None):
        """
        Initialize a QueryResult.

        Args:
            columns: List of column names in the result
            records: List of records, where each record is a list of values
            summary: Optional summary information about the query execution
        """
        self._columns = columns
        self._records = records
        self._summary = summary or {}
        self._current_index = 0

    @property
    def columns(self) -> List[str]:
        """Get the column names of the result."""
        return self._columns.copy()

    @property
    def records(self) -> List[List[Any]]:
        """Get all records as a list of lists."""
        return [record.copy() for record in self._records]

    @property
    def summary(self) -> Dict[str, Any]:
        """Get summary information about the query execution."""
        return self._summary.copy()

    def __len__(self) -> int:
        """Return the number of records in the result."""
        return len(self._records)

    def __iter__(self) -> Iterator['QueryRecord']:
        """Iterate over records as QueryRecord objects."""
        for record in self._records:
            yield QueryRecord(self._columns, record)

    def __getitem__(self, key):
        """Get a specific record by index or slice."""
        if isinstance(key, slice):
            # Handle slice
            records = self._records[key]
            return [QueryRecord(self._columns, record) for record in records]
        elif isinstance(key, int):
            # Handle single index
            if key < 0 or key >= len(self._records):
                raise IndexError(f"Record index {key} out of range")
            return QueryRecord(self._columns, self._records[key])
        else:
            raise TypeError(f"Invalid key type: {type(key)}")

    def __bool__(self) -> bool:
        """Return True if the result contains any records."""
        return len(self._records) > 0

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """
        Convert the result to a list of dictionaries.

        Returns:
            List of dictionaries where each dict represents a record
        """
        return [dict(zip(self._columns, record)) for record in self._records]

    def to_table(self) -> str:
        """
        Convert the result to a formatted table string.

        Returns:
            String representation of the result as a table
        """
        if not self._records:
            return "No records found."

        # Calculate column widths
        col_widths = [len(col) for col in self._columns]
        for record in self._records:
            for i, value in enumerate(record):
                col_widths[i] = max(col_widths[i], len(str(value)))

        # Build table
        lines = []

        # Header
        header = " | ".join(col.ljust(width)
                           for col, width in zip(self._columns, col_widths))
        lines.append(header)
        lines.append("-" * len(header))

        # Records
        for record in self._records:
            row = " | ".join(str(value).ljust(width)
                           for value, width in zip(record, col_widths))
            lines.append(row)

        return "\n".join(lines)

    def single(self) -> Optional['QueryRecord']:
        """
        Get a single record from the result.

        Returns:
            The single record if exactly one exists, None if empty

        Raises:
            ValueError: If more than one record exists
        """
        if len(self._records) == 0:
            return None
        elif len(self._records) == 1:
            return QueryRecord(self._columns, self._records[0])
        else:
            raise ValueError("Expected single record, got "
                           f"{len(self._records)}")

    def value(self, column: Optional[str] = None) -> Any:
        """
        Get a single value from the result.

        Args:
            column: Column name to get value from (uses first column if None)

        Returns:
            The single value

        Raises:
            ValueError: If not exactly one record or column not found
        """
        record = self.single()
        if record is None:
            raise ValueError("No records found")

        if column is None:
            if len(self._columns) != 1:
                raise ValueError("Expected single column, got "
                               f"{len(self._columns)}")
            return record[self._columns[0]]
        else:
            return record[column]

class QueryRecord(Mapping):
    """
    Represents a single record from a query result.

    This class provides dictionary - like access to the values in a record,
    using column names as keys.
    """

    def __init__(self, columns: List[str], values: List[Any]):
        """
        Initialize a QueryRecord.

        Args:
            columns: List of column names
            values: List of values corresponding to the columns
        """
        if len(columns) != len(values):
            raise ValueError(f"Column count ({len(columns)}) doesn't match "
                           f"value count ({len(values)})")

        self._columns = columns
        self._values = values
        self._data = dict(zip(columns, values))

    def __getitem__(self, key: str) -> Any:
        """Get a value by column name."""
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        """Iterate over column names."""
        return iter(self._columns)

    def __len__(self) -> int:
        """Return the number of columns."""
        return len(self._columns)

    def __contains__(self, key: str) -> bool:
        """Check if a column exists."""
        return key in self._data

    def __repr__(self) -> str:
        """Return string representation of the record."""
        items = [f"{k}={repr(v)}" for k, v in self._data.items()]
        return f"QueryRecord({', '.join(items)})"

    def keys(self):
        """Get column names."""
        return self._data.keys()

    def values(self):
        """Get column values."""
        return self._data.values()

    def items(self):
        """Get column name - value pairs."""
        return self._data.items()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value by column name with optional default."""
        return self._data.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the record to a dictionary."""
        return self._data.copy()
