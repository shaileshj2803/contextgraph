"""
High - performance CSV importer for nodes and relationships.

into the graph database efficiently.
"""

import csv
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from typing import Any, Dict, List, Optional, Union, Callable

from .exceptions import GraphDBError

class CSVImporter:
    """
    High - performance CSV importer for nodes and relationships.

    Features:
    - Batch processing for optimal performance
    - Parallel processing for large files
    - Automatic type inference and conversion
    - Progress tracking and reporting
    - Error handling and validation
    - Memory - efficient streaming for large files
    """

    def __init__(self, graph_db, batch_size: int = 1000, max_workers: int = 4):
        """
        Initialize the CSV importer.

        Args:
            graph_db: The GraphDB instance to import data into
            batch_size: Number of records to process in each batch
            max_workers: Maximum number of worker threads for parallel processing
        """
        self.graph_db = graph_db
        self.batch_size = batch_size
        self.max_workers = max_workers
        self._node_id_mapping = {}  # Maps CSV node IDs to internal node IDs

    def import_nodes_from_csv(
        self,
        csv_file: Union[str, Path],
        id_column: str = 'id',
        label_column: Optional[str] = None,
        labels: Optional[List[str]] = None,
        property_columns: Optional[List[str]] = None,
        skip_duplicates: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        batch_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Import nodes from a CSV file with high performance.

        Args:
            csv_file: Path to the CSV file
            id_column: Column name containing unique node identifiers
            label_column: Column name containing node labels (optional)
            labels: Fixed labels to apply to all nodes (optional)
            skip_duplicates: Whether to skip nodes with duplicate IDs
            progress_callback: Callback function for progress updates (current, total)

        Returns:
            Dictionary with import statistics
        """
        start_time = time.time()
        csv_file = Path(csv_file)

        if not csv_file.exists():
            raise GraphDBError(f"CSV file not found: {csv_file}")

        # Use provided batch_size or fall back to instance default
        effective_batch_size = batch_size if batch_size is not None else self.batch_size

        # First pass: count total rows for progress tracking
        total_rows = self._count_csv_rows(csv_file)

        stats = {
            'total_rows': total_rows,
            'imported_nodes': 0,
            'skipped_duplicates': 0,
            'errors': 0,
            'processing_time': 0,
            'nodes_per_second': 0
        }

        processed_rows = 0
        node_batches = []
        seen_ids = set() if skip_duplicates else None

        try:
            with open(csv_file, 'r', encoding='utf - 8') as f:
                reader = csv.DictReader(f)

                # Validate required columns
                if id_column not in reader.fieldnames:
                    raise GraphDBError(f"ID column '{id_column}' not found in CSV")

                if label_column and label_column not in reader.fieldnames:
                    raise GraphDBError(f"Label column '{label_column}' not found in CSV")

                # Determine property columns
                if property_columns is None:
                    property_columns = [col for col in reader.fieldnames
                                      if col not in [id_column, label_column]]

                current_batch = []

                for row in reader:
                    processed_rows += 1

                    # Extract node data
                    node_id = row[id_column]

                    # Skip duplicates if requested
                    if skip_duplicates:
                        if node_id in seen_ids:
                            stats['skipped_duplicates'] += 1
                            continue
                        seen_ids.add(node_id)

                    # Determine labels
                    node_labels = []
                    if labels:
                        node_labels.extend(labels)
                    if label_column and row[label_column]:
                        # Support multiple labels separated by semicolon
                        additional_labels = [lbl.strip() for lbl in row[label_column].split(';')]
                        node_labels.extend(additional_labels)

                    # Extract properties
                    properties = {}
                    for col in property_columns:
                        if col in row and row[col]:
                            properties[col] = self._convert_value(row[col])

                    # Add original CSV ID as property for reference
                    properties['_csv_id'] = node_id

                    current_batch.append({
                        'csv_id': node_id,
                        'labels': node_labels,
                        'properties': properties
                    })

                    # Process batch when full
                    if len(current_batch) >= effective_batch_size:
                        node_batches.append(current_batch)
                        current_batch = []

                    # Progress callback
                    if progress_callback and processed_rows % 100 == 0:
                        progress_callback(processed_rows, total_rows)

                # Process remaining nodes
                if current_batch:
                    node_batches.append(current_batch)

            # Process all batches
            if len(node_batches) <= 1 or self.max_workers == 1:
                # Single - threaded processing
                for batch in node_batches:
                    batch_stats = self._process_node_batch(batch)
                    stats['imported_nodes'] += batch_stats['imported']
                    stats['errors'] += batch_stats['errors']
            else:
                # Multi - threaded processing
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    future_to_batch = {
                        executor.submit(self._process_node_batch, batch): batch
                        for batch in node_batches
                    }

                    for future in as_completed(future_to_batch):
                        batch_stats = future.result()
                        stats['imported_nodes'] += batch_stats['imported']
                        stats['errors'] += batch_stats['errors']

            # Final progress update
            if progress_callback:
                progress_callback(total_rows, total_rows)

        except Exception as e:
            raise GraphDBError(f"Error importing nodes from CSV: {str(e)}")

        # Calculate final statistics
        stats['processing_time'] = time.time() - start_time
        if stats['processing_time'] > 0:
            stats['nodes_per_second'] = stats['imported_nodes'] / stats['processing_time']

        return stats

    def import_relationships_from_csv(
        self,
        csv_file: Union[str, Path],
        source_column: str = 'source',
        target_column: str = 'target',
        type_column: Optional[str] = None,
        relationship_type: str = 'RELATED',
        property_columns: Optional[List[str]] = None,
        use_csv_ids: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        batch_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Import relationships from a CSV file with high performance.

        Args:
            csv_file: Path to the CSV file
            source_column: Column name containing source node identifiers
            target_column: Column name containing target node identifiers
            type_column: Column name containing relationship types (optional)
            relationship_type: Default relationship type if type_column not specified
            use_csv_ids: Whether to use CSV IDs (True) or internal node IDs (False)
            progress_callback: Callback function for progress updates (current, total)

        Returns:
            Dictionary with import statistics
        """
        start_time = time.time()
        csv_file = Path(csv_file)

        if not csv_file.exists():
            raise GraphDBError(f"CSV file not found: {csv_file}")

        # Use provided batch_size or fall back to instance default
        effective_batch_size = batch_size if batch_size is not None else self.batch_size

        # Count total rows
        total_rows = self._count_csv_rows(csv_file)

        stats = {
            'total_rows': total_rows,
            'imported_relationships': 0,
            'skipped_missing_nodes': 0,
            'errors': 0,
            'processing_time': 0,
            'relationships_per_second': 0
        }

        # Build node lookup if using CSV IDs
        node_lookup = {}
        if use_csv_ids:
            node_lookup = self._build_csv_id_lookup()

        processed_rows = 0
        relationship_batches = []

        try:
            with open(csv_file, 'r', encoding='utf - 8') as f:
                reader = csv.DictReader(f)

                # Validate required columns
                if source_column not in reader.fieldnames:
                    raise GraphDBError(f"Source column '{source_column}' not found in CSV")

                if target_column not in reader.fieldnames:
                    raise GraphDBError(f"Target column '{target_column}' not found in CSV")

                if type_column and type_column not in reader.fieldnames:
                    raise GraphDBError(f"Type column '{type_column}' not found in CSV")

                # Determine property columns
                if property_columns is None:
                    excluded_cols = [source_column, target_column]
                    if type_column:
                        excluded_cols.append(type_column)
                    property_columns = [col for col in reader.fieldnames
                                      if col not in excluded_cols]

                current_batch = []

                for row in reader:
                    processed_rows += 1

                    # Extract relationship data
                    source_id = row[source_column]
                    target_id = row[target_column]

                    # Determine relationship type
                    rel_type = relationship_type
                    if type_column and row[type_column]:
                        rel_type = row[type_column]

                    # Extract properties
                    properties = {}
                    for col in property_columns:
                        if col in row and row[col]:
                            properties[col] = self._convert_value(row[col])

                    current_batch.append({
                        'source_id': source_id,
                        'target_id': target_id,
                        'type': rel_type,
                        'properties': properties
                    })

                    # Process batch when full
                    if len(current_batch) >= effective_batch_size:
                        relationship_batches.append(current_batch)
                        current_batch = []

                    # Progress callback
                    if progress_callback and processed_rows % 100 == 0:
                        progress_callback(processed_rows, total_rows)

                # Process remaining relationships
                if current_batch:
                    relationship_batches.append(current_batch)

            # Process all batches
            if len(relationship_batches) <= 1 or self.max_workers == 1:
                # Single - threaded processing
                for batch in relationship_batches:
                    batch_stats = self._process_relationship_batch(batch, node_lookup, use_csv_ids)
                    stats['imported_relationships'] += batch_stats['imported']
                    stats['skipped_missing_nodes'] += batch_stats['skipped']
                    stats['errors'] += batch_stats['errors']
            else:
                # Multi - threaded processing
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    future_to_batch = {
                        executor.submit(self._process_relationship_batch, batch, node_lookup, use_csv_ids): batch
                        for batch in relationship_batches
                    }

                    for future in as_completed(future_to_batch):
                        batch_stats = future.result()
                        stats['imported_relationships'] += batch_stats['imported']
                        stats['skipped_missing_nodes'] += batch_stats['skipped']
                        stats['errors'] += batch_stats['errors']

            # Final progress update
            if progress_callback:
                progress_callback(total_rows, total_rows)

        except Exception as e:
            raise GraphDBError(f"Error importing relationships from CSV: {str(e)}")

        # Calculate final statistics
        stats['processing_time'] = time.time() - start_time
        if stats['processing_time'] > 0:
            stats['relationships_per_second'] = stats['imported_relationships'] / stats['processing_time']

        return stats

    def _process_node_batch(self, batch: List[Dict]) -> Dict[str, int]:
        """Process a batch of nodes."""
        stats = {'imported': 0, 'errors': 0}

        for node_data in batch:
            try:
                # Create node in database
                internal_id = self.graph_db.create_node(
                    labels=node_data['labels'],
                    properties=node_data['properties']
                )

                # Store mapping from CSV ID to internal ID
                self._node_id_mapping[node_data['csv_id']] = internal_id
                stats['imported'] += 1

            except Exception as e:
                stats['errors'] += 1
                # Log error but continue processing
                print(f"Error creating node {node_data['csv_id']}: {e}")

        return stats

    def _process_relationship_batch(
        self,
        batch: List[Dict],
        node_lookup: Dict[str, int],
        use_csv_ids: bool
    ) -> Dict[str, int]:
        """Process a batch of relationships."""
        stats = {'imported': 0, 'skipped': 0, 'errors': 0}

        for rel_data in batch:
            try:
                # Resolve node IDs
                if use_csv_ids:
                    source_internal_id = node_lookup.get(rel_data['source_id'])
                    target_internal_id = node_lookup.get(rel_data['target_id'])

                    if source_internal_id is None or target_internal_id is None:
                        stats['skipped'] += 1
                        continue
                else:
                    # Use IDs directly as internal IDs
                    source_internal_id = int(rel_data['source_id'])
                    target_internal_id = int(rel_data['target_id'])

                # Create relationship
                self.graph_db.create_relationship(
                    source_id=source_internal_id,
                    target_id=target_internal_id,
                    rel_type=rel_data['type'],
                    properties=rel_data['properties']
                )

                stats['imported'] += 1

            except Exception as e:
                stats['errors'] += 1
                print(f"Error creating relationship {rel_data['source_id']} -> {rel_data['target_id']}: {e}")

        return stats

    def _build_csv_id_lookup(self) -> Dict[str, int]:
        """Build a lookup table from CSV IDs to internal node IDs."""
        lookup = {}

        # Find all nodes with _csv_id property
        all_nodes = self.graph_db.find_nodes()
        for node in all_nodes:
            csv_id = node.get('properties', {}).get('_csv_id')
            if csv_id:
                lookup[str(csv_id)] = node['id']

        return lookup

    def _count_csv_rows(self, csv_file: Path) -> int:
        """Count the number of rows in a CSV file (excluding header)."""
        with open(csv_file, 'r', encoding='utf - 8') as f:
            # Skip header
            next(f)
            return sum(1 for _ in f)

    def _convert_value(self, value: str) -> Any:
        """Convert a string value to appropriate Python type."""
        if not value or value.lower() in ('null', 'none', ''):
            return None

        # Try boolean
        if value.lower() in ('true', 'yes', '1'):
            return True
        elif value.lower() in ('false', 'no', '0'):
            return False

        # Try integer
        try:
            if '.' not in value and 'e' not in value.lower():
                return int(value)
        except ValueError:
            pass

        # Try float
        try:
            return float(value)
        except ValueError:
            pass

        # Try JSON (for lists, objects)
        if value.startswith(('[', '{')):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass

        # Return as string
        return value

    def clear_node_mapping(self):
        """Clear the internal node ID mapping."""
        self._node_id_mapping.clear()

    def get_node_mapping(self) -> Dict[str, int]:
        """Get the current CSV ID to internal ID mapping."""
        return self._node_id_mapping.copy()

def import_nodes_csv(
    graph_db,
    csv_file: Union[str, Path],
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to import nodes from CSV.

    Args:
        graph_db: GraphDB instance
        csv_file: Path to CSV file

    Returns:
        Import statistics
    """
    importer = CSVImporter(graph_db)
    return importer.import_nodes_from_csv(csv_file, **kwargs)

def import_relationships_csv(
    graph_db,
    csv_file: Union[str, Path],
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to import relationships from CSV.

    Args:
        graph_db: GraphDB instance
        csv_file: Path to CSV file

    Returns:
        Import statistics
    """
    importer = CSVImporter(graph_db)
    return importer.import_relationships_from_csv(csv_file, **kwargs)
