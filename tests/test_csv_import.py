"""
Test cases for CSV import functionality.
"""

import pytest
import csv
import tempfile
import time
from pathlib import Path
from contextgraph import GraphDB, CSVImporter
from contextgraph.csv_importer import import_nodes_csv, import_relationships_csv
from contextgraph.exceptions import GraphDBError

class TestCSVImporter:
    """Test CSV import functionality."""

    def setup_method(self):
        """Set up test database and temporary files."""
        self.db = GraphDB()
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_sample_nodes_csv(self, filename="nodes.csv", num_rows=100):
        """Create a sample nodes CSV file."""
        csv_file = self.temp_dir / filename

        with open(csv_file, 'w', newline='', encoding='utf - 8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'age', 'city', 'active', 'labels'])

            for i in range(num_rows):
                writer.writerow([
                    f'node_{i}',
                    f'Person {i}',
                    25 + (i % 50),
                    ['NYC', 'SF', 'LA'][i % 3],
                    'true' if i % 2 == 0 else 'false',
                    'Person;User'
                ])

        return csv_file

    def create_sample_relationships_csv(self, filename="relationships.csv", num_rows=50):
        """Create a sample relationships CSV file."""
        csv_file = self.temp_dir / filename

        with open(csv_file, 'w', newline='', encoding='utf - 8') as f:
            writer = csv.writer(f)
            writer.writerow(['source', 'target', 'type', 'weight', 'since'])

            for i in range(num_rows):
                writer.writerow([
                    f'node_{i}',
                    f'node_{(i + 1) % num_rows}',
                    'KNOWS',
                    i * 0.1,
                    f'2020-{(i % 12) + 1:02d}-01'
                ])

        return csv_file

        """Test basic node import functionality."""
        csv_file = self.create_sample_nodes_csv(num_rows=10)

        stats = self.db.import_nodes_from_csv(csv_file, label_column='labels')

        assert stats['imported_nodes'] == 10
        assert stats['errors'] == 0
        assert stats['processing_time'] > 0
        assert stats['nodes_per_second'] > 0

        # Verify nodes were created
        assert self.db.node_count == 10

        # Check a specific node
        nodes = self.db.find_nodes(properties={'name': 'Person 0'})
        assert len(nodes) == 1
        assert nodes[0]['properties']['age'] == 25
        assert nodes[0]['properties']['city'] == 'NYC'
        assert nodes[0]['properties']['active'] is True
        assert 'Person' in nodes[0]['labels']
        assert 'User' in nodes[0]['labels']

        csv_file = self.create_sample_nodes_csv(num_rows=5)

        stats = self.db.import_nodes_from_csv(
            csv_file,
            id_column='id',
            labels=['TestNode'],
            property_columns=['name', 'age']  # Only import specific columns
        )

        assert stats['imported_nodes'] == 5

        # Check that only specified properties were imported
        nodes = self.db.find_nodes(labels=['TestNode'])
        assert len(nodes) == 5

        node = nodes[0]
        assert 'name' in node['properties']
        assert 'age' in node['properties']
        assert 'city' not in node['properties']  # Should be excluded
        assert 'active' not in node['properties']  # Should be excluded

        """Test skipping duplicate nodes."""
        # Create CSV with duplicate IDs
        csv_file = self.temp_dir / "duplicates.csv"
        with open(csv_file, 'w', newline='', encoding='utf - 8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name'])
            writer.writerow(['1', 'Alice'])
            writer.writerow(['2', 'Bob'])
            writer.writerow(['1', 'Alice Duplicate'])  # Duplicate ID
            writer.writerow(['3', 'Charlie'])

        assert stats['imported_nodes'] == 3  # Should skip the duplicate
        assert stats['skipped_duplicates'] == 1
        assert self.db.node_count == 3

        """Test basic relationship import functionality."""
        # First import nodes
        nodes_csv = self.create_sample_nodes_csv(num_rows=5)
        self.db.import_nodes_from_csv(nodes_csv, label_column='labels')

        # Then import relationships
        rels_csv = self.create_sample_relationships_csv(num_rows=4)

        assert stats['imported_relationships'] == 4
        assert stats['errors'] == 0
        assert stats['skipped_missing_nodes'] == 0

        # Verify relationships were created
        assert self.db.relationship_count == 4

        # Test a query
        result = self.db.execute('MATCH (a)-[:KNOWS]->(b) RETURN COUNT(*)')
        assert result[0]['COUNT(*)'] == 4

        """Test relationship import with missing nodes."""
        # Create relationships CSV without importing nodes first
        rels_csv = self.create_sample_relationships_csv(num_rows=3)

        # All relationships should be skipped due to missing nodes
        assert stats['imported_relationships'] == 0
        assert stats['skipped_missing_nodes'] == 3
        assert self.db.relationship_count == 0

        # Create CSV with type column
        csv_file = self.temp_dir / "typed_rels.csv"
        with open(csv_file, 'w', newline='', encoding='utf - 8') as f:
            writer = csv.writer(f)
            writer.writerow(['from_id', 'to_id', 'rel_type', 'strength'])
            writer.writerow(['node_0', 'node_1', 'FRIENDS', '0.8'])
            writer.writerow(['node_1', 'node_2', 'COLLEAGUES', '0.6'])

        # Import nodes first
        nodes_csv = self.create_sample_nodes_csv(num_rows=3)
        self.db.import_nodes_from_csv(nodes_csv)

        # Import relationships
        stats = self.db.import_relationships_from_csv(
            csv_file,
            source_column='from_id',
            target_column='to_id',
            type_column='rel_type'
        )

        assert stats['imported_relationships'] == 2

        # Verify different relationship types
        friends = self.db.execute('MATCH (a)-[:FRIENDS]->(b) RETURN COUNT(*)')
        colleagues = self.db.execute('MATCH (a)-[:COLLEAGUES]->(b) RETURN COUNT(*)')

        assert friends[0]['COUNT(*)'] == 1
        assert colleagues[0]['COUNT(*)'] == 1

    def test_batch_processing(self):
        """Test batch processing with small batch size."""
        csv_file = self.create_sample_nodes_csv(num_rows=25)

        # Use small batch size to test batching
        stats = self.db.import_nodes_from_csv(csv_file, batch_size=5)
        assert stats['imported_nodes'] == 25
        assert self.db.node_count == 25

    def test_progress_callback(self):
        """Test progress callback functionality."""
        csv_file = self.create_sample_nodes_csv(num_rows=20)

        progress_calls = []

        def progress_callback(current, total):
            progress_calls.append((current, total))

        stats = self.db.import_nodes_from_csv(csv_file, progress_callback=progress_callback)
        assert stats['imported_nodes'] == 20
        assert len(progress_calls) > 0

        # Check that final call has current == total
        final_call = progress_calls[-1]
        assert final_call[0] == final_call[1] == 20

    def test_type_conversion(self):
        """Test automatic type conversion."""
        csv_file = self.temp_dir / "types.csv"
        with open(csv_file, 'w', newline='', encoding='utf - 8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'age', 'salary', 'active', 'tags', 'metadata'])
            writer.writerow([
                'test_1',
                'Test Person',
                '30',  # Should become int
                '75000.50',  # Should become float
                'true',  # Should become bool
                '["tag1", "tag2"]',  # Should become list
                '{"key": "value"}'  # Should become dict
            ])

        stats = self.db.import_nodes_from_csv(csv_file)
        assert stats['imported_nodes'] == 1

        nodes = self.db.find_nodes(properties={'name': 'Test Person'})
        assert len(nodes) == 1

        props = nodes[0]['properties']
        assert props['age'] == 30  # int
        assert props['salary'] == 75000.50  # float
        assert props['active'] is True  # bool
        assert props['tags'] == ['tag1', 'tag2']  # list
        assert props['metadata'] == {'key': 'value'}  # dict

    def test_error_handling(self):
        """Test error handling for invalid files."""
        # Test non - existent file
        with pytest.raises(GraphDBError):
            self.db.import_nodes_from_csv("nonexistent.csv")

        # Test CSV with missing required column
        csv_file = self.temp_dir / "invalid.csv"
        with open(csv_file, 'w', newline='', encoding='utf - 8') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'age'])  # Missing 'id' column
            writer.writerow(['Alice', '30'])

        with pytest.raises(GraphDBError):
            self.db.import_nodes_from_csv(csv_file)

    def test_large_dataset_performance(self):
        """Test performance with larger dataset."""
        # Create larger CSV (1000 nodes)
        csv_file = self.create_sample_nodes_csv(num_rows=1000)

        start_time = time.time()
        stats = self.db.import_nodes_from_csv(csv_file)
        end_time = time.time()

        assert stats['imported_nodes'] == 1000
        assert stats['errors'] == 0

        # Should complete in reasonable time (less than 5 seconds)
        processing_time = end_time - start_time
        assert processing_time < 5.0

        # Should achieve reasonable throughput (>100 nodes / second)
        assert stats['nodes_per_second'] > 100

    def test_convenience_functions(self):
        csv_file = self.create_sample_nodes_csv(num_rows=5)

        # Test convenience function
        stats = import_nodes_csv(self.db, csv_file)

        assert stats['imported_nodes'] == 5
        assert self.db.node_count == 5

        # Test relationships convenience function
        rels_csv = self.create_sample_relationships_csv(num_rows=3)
        rel_stats = import_relationships_csv(self.db, rels_csv)

        assert rel_stats['imported_relationships'] == 3
        assert self.db.relationship_count == 3

class TestCSVImportIntegration:

    def setup_method(self):
        """Set up test database."""
        self.db = GraphDB()
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

        # Create and import nodes
        nodes_csv = self.temp_dir / "people.csv"
        with open(nodes_csv, 'w', newline='', encoding='utf - 8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'age', 'department'])
            writer.writerow(['emp_1', 'Alice', '30', 'Engineering'])
            writer.writerow(['emp_2', 'Bob', '25', 'Marketing'])
            writer.writerow(['emp_3', 'Charlie', '35', 'Engineering'])

        # Create and import relationships
        rels_csv = self.temp_dir / "reports_to.csv"
        with open(rels_csv, 'w', newline='', encoding='utf - 8') as f:
            writer = csv.writer(f)
            writer.writerow(['subordinate', 'manager', 'since'])
            writer.writerow(['emp_2', 'emp_1', '2021 - 01 - 01'])
            writer.writerow(['emp_3', 'emp_1', '2020 - 06 - 01'])

        self.db.import_relationships_from_csv(
            rels_csv,
            source_column='subordinate',
            target_column='manager',
            relationship_type='REPORTS_TO'
        )

        # Test complex Cypher queries
        # Find all managers
        result = self.db.execute('''
            MATCH (subordinate)-[:REPORTS_TO]->(manager)
            RETURN DISTINCT manager.name
        ''')

        assert len(result) == 1
        assert result[0]['manager.name'] == 'Alice'

        # Find engineers who are managers (simplified test)
        result = self.db.execute('''
            MATCH (subordinate)-[:REPORTS_TO]->(manager)
            WHERE manager.department = "Engineering"
            RETURN manager.name
        ''')

        assert len(result) == 2  # Two subordinates report to Alice
        # All results should have Alice as the manager
        for record in result:
            assert record['manager.name'] == 'Alice'

        nodes_csv = self.temp_dir / "transactional_nodes.csv"
        with open(nodes_csv, 'w', newline='', encoding='utf - 8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name'])
            writer.writerow(['1', 'Alice'])
            writer.writerow(['2', 'Bob'])

        # Test successful transaction
        with self.db.transaction_manager.transaction():
            stats = self.db.import_nodes_from_csv(nodes_csv)
            assert stats['imported_nodes'] == 2

        # Verify nodes were committed
        assert self.db.node_count == 2

        # Test rollback (simulate by raising exception)
        initial_count = self.db.node_count

        try:
            with self.db.transaction_manager.transaction():
                # Import more nodes
                more_nodes_csv = self.temp_dir / "more_nodes.csv"
                with open(more_nodes_csv, 'w', newline='', encoding='utf - 8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['id', 'name'])
                    writer.writerow(['3', 'Charlie'])

                # Simulate error
                raise Exception("Simulated error")
        except Exception:
            pass

        # Node count should be unchanged due to rollback
        assert self.db.node_count == initial_count

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
