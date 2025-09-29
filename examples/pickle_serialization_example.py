"""
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import contextgraph
sys.path.insert(0, str(Path(__file__).parent.parent))
Example demonstrating pickle serialization for fast save / load operations.

This example shows the performance benefits of using pickle over JSON
for serializing graph databases, especially with large datasets.
"""

import time
import tempfile
from pathlib import Path
from contextgraph import GraphDB

def create_large_graph(db, num_people=1000, num_companies=50):
    """Create a large graph for performance testing."""
    print(f"Creating graph with {num_people} people and {num_companies} companies...")

    # Create people with various data types
    for i in range(num_people):
        # Use the API instead of Cypher for complex data
        db.create_node(['Person'], {
            'name': f'Person {i}',
            'id': i,
            'age': 25 + (i % 40),
            'active': i % 2 == 0,
            'scores': [i % 100, (i + 10) % 100, (i + 20) % 100],
            'metadata': {'level': i % 10, 'department': f'Dept{i % 5}'},
            'salary': 50000 + (i * 100)
        })

    # Create companies
    for i in range(num_companies):
        db.create_node(['Company'], {
            'name': f'Company {i}',
            'id': i + 10000,
            'industry': f'Industry{i % 5}',
            'founded': 2000 + (i % 23),
            'revenue': 1000000 + (i * 50000),
            'locations': [f'City{i % 10}', f'City{(i + 1) % 10}']
        })

    # Create employment relationships
    print("Creating employment relationships...")
    for i in range(num_people):
        company_id = i % num_companies

        # Find nodes
        person_nodes = db.find_nodes(properties={'name': f'Person {i}'})
        company_nodes = db.find_nodes(properties={'name': f'Company {company_id}'})

        if person_nodes and company_nodes:
            db.create_relationship(
                person_nodes[0]['id'],
                company_nodes[0]['id'],
                'WORKS_FOR',
                {
                    'position': f'Position{i % 10}',
                    'start_date': f'202{i % 4}-{(i % 12) + 1:02d}-01',
                    'salary_band': f'Band{(i % 5) + 1}',
                    'benefits': ['health', 'dental', 'vision'][:(i % 3) + 1]
                }
            )

    # Create some friendship relationships
    print("Creating friendship relationships...")
    for i in range(0, min(num_people, 500), 2):  # Create friendships for first 500 people
        if i + 1 < num_people:
            person1_nodes = db.find_nodes(properties={'name': f'Person {i}'})
            person2_nodes = db.find_nodes(properties={'name': f'Person {i + 1}'})

            if person1_nodes and person2_nodes:
                db.create_relationship(
                    person1_nodes[0]['id'],
                    person2_nodes[0]['id'],
                    'FRIENDS_WITH',
                    {
                        'since': f'201{i % 10}-{(i % 12) + 1:02d}-01',
                        'closeness': round((i % 100) / 100.0, 2),
                        'activities': ['coffee', 'movies', 'sports'][:(i % 3) + 1]
                    }
                )

    print(f"Graph created: {db.node_count} nodes, {db.relationship_count} relationships")

def benchmark_serialization(db, temp_dir):
    """Benchmark JSON vs Pickle serialization performance."""
    print("\n" + "="*60)
    print("SERIALIZATION PERFORMANCE BENCHMARK")
    print("="*60)

    json_file = temp_dir / "benchmark_graph.json"
    pickle_file = temp_dir / "benchmark_graph.pkl"

    # Benchmark JSON save
    print("\n📄 JSON Serialization:")
    start_time = time.time()
    db.save(json_file)
    json_save_time = time.time() - start_time
    json_size = json_file.stat().st_size

    print(f"   Save time: {json_save_time:.3f} seconds")
    print(f"   File size: {json_size:,} bytes ({json_size / 1024 / 1024:.2f} MB)")

    # Benchmark Pickle save
    print("\n🥒 Pickle Serialization:")
    start_time = time.time()
    db.save_pickle(pickle_file)
    pickle_save_time = time.time() - start_time
    pickle_size = pickle_file.stat().st_size

    print(f"   Save time: {pickle_save_time:.3f} seconds")
    print(f"   File size: {pickle_size:,} bytes ({pickle_size / 1024 / 1024:.2f} MB)")

    # Performance comparison
    save_speedup = json_save_time / pickle_save_time if pickle_save_time > 0 else float('inf')
    size_ratio = pickle_size / json_size if json_size > 0 else 0

    print("\n📊 Save Performance:")
    print(f"   Pickle is {save_speedup:.1f}x {'faster' if save_speedup > 1 else 'slower'} than JSON")
    print(f"   Pickle file is {size_ratio:.1f}x {'larger' if size_ratio > 1 else 'smaller'} than JSON")

    # Benchmark loading
    print("\n📥 Loading Performance:")

    # JSON load
    json_db = GraphDB()
    start_time = time.time()
    json_db.load(json_file)
    json_load_time = time.time() - start_time
    print(f"   JSON load time: {json_load_time:.3f} seconds")

    # Pickle load
    pickle_db = GraphDB()
    start_time = time.time()
    pickle_db.load_pickle(pickle_file)
    pickle_load_time = time.time() - start_time
    print(f"   Pickle load time: {pickle_load_time:.3f} seconds")

    # Load performance comparison
    load_speedup = json_load_time / pickle_load_time if pickle_load_time > 0 else float('inf')
    print(f"   Pickle is {load_speedup:.1f}x {'faster' if load_speedup > 1 else 'slower'} than JSON")

    # Verify data integrity
    print("\n✅ Data Integrity Check:")
    print(f"   Original: {db.node_count} nodes, {db.relationship_count} relationships")
    print(f"   JSON:     {json_db.node_count} nodes, {json_db.relationship_count} relationships")
    print(f"   Pickle:   {pickle_db.node_count} nodes, {pickle_db.relationship_count} relationships")

    # Verify data is identical
    assert json_db.node_count == db.node_count
    assert pickle_db.node_count == db.node_count
    assert json_db.relationship_count == db.relationship_count
    assert pickle_db.relationship_count == db.relationship_count

    print("   ✅ All data integrity checks passed!")

    return {
        'json_save_time': json_save_time,
        'pickle_save_time': pickle_save_time,
        'json_load_time': json_load_time,
        'pickle_load_time': pickle_load_time,
        'json_size': json_size,
        'pickle_size': pickle_size,
        'save_speedup': save_speedup,
        'load_speedup': load_speedup
    }

def demonstrate_type_preservation():
    """Demonstrate how pickle preserves Python types better than JSON."""
    print("\n" + "="*60)
    print("TYPE PRESERVATION DEMONSTRATION")
    print("="*60)

    db = GraphDB()

    # Create node with complex data types
    complex_data = {
        'string': 'Hello World',
        'integer': 42,
        'float': 3.14159,
        'boolean': True,
        'none_value': None,
        'list': [1, 2, 3, 'mixed', True, None],
        'dict': {'nested': {'deep': {'value': 'here'}}},
        'tuple': (1, 2, 3),  # Tuples are preserved in pickle but become lists in JSON
        'set': {1, 2, 3, 4, 5},  # Sets are preserved in pickle but become lists in JSON
    }

    db.create_node(['TypeTest'], complex_data)

    temp_dir = Path(tempfile.mkdtemp())
    json_file = temp_dir / "types_test.json"
    pickle_file = temp_dir / "types_test.pkl"

    # Save with both methods
    db.save(json_file)
    db.save_pickle(pickle_file)

    # Load with both methods
    json_db = GraphDB()
    json_db.load(json_file)

    pickle_db = GraphDB()
    pickle_db.load_pickle(pickle_file)

    # Compare type preservation
    json_node = json_db.find_nodes(labels=['TypeTest'])[0]['properties']
    pickle_node = pickle_db.find_nodes(labels=['TypeTest'])[0]['properties']

    print("\n📊 Type Preservation Comparison:")
    print(f"{'Property':<15} {'Original':<15} {'JSON':<15} {'Pickle':<15}")
    print("-" * 60)

    for key, original_value in complex_data.items():
        json_value = json_node.get(key)
        pickle_value = pickle_node.get(key)

        orig_type = type(original_value).__name__
        json_type = type(json_value).__name__
        pickle_type = type(pickle_value).__name__

        print(f"{key:<15} {orig_type:<15} {json_type:<15} {pickle_type:<15}")

        # Check if types match
        if isinstance(original_value, type(pickle_value)):
            print(f"   ✅ Pickle preserves {orig_type}")
        else:
            print(f"   ❌ Pickle changed {orig_type} to {pickle_type}")

        if not isinstance(original_value, type(json_value)):
            print(f"   ⚠️  JSON changed {orig_type} to {json_type}")

    # Clean up
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

def demonstrate_practical_usage():
    """Demonstrate practical usage scenarios for pickle serialization."""
    print("\n" + "="*60)
    print("PRACTICAL USAGE SCENARIOS")
    print("="*60)

    db = GraphDB()

    # Scenario 1: Data processing pipeline
    print("\n🔄 Scenario 1: Data Processing Pipeline")
    print("   Creating initial dataset...")

    # Create some data
    for i in range(100):
        db.execute(f'CREATE (item{i}:Item {{id: {i}, value: {i * 1.5}, processed: false}})')

    # Save checkpoint
    temp_dir = Path(tempfile.mkdtemp())
    checkpoint_file = temp_dir / "processing_checkpoint.pkl"

    print("   Saving processing checkpoint...")
    start_time = time.time()
    db.save_pickle(checkpoint_file)
    save_time = time.time() - start_time
    print(f"   Checkpoint saved in {save_time:.3f} seconds")

    # Simulate processing
    print("   Processing data...")
    for i in range(50):  # Process half the items
        items = db.find_nodes(properties={'id': i})
        if items:
            # Update processed status (in real scenario, you'd use SET clause)
            pass

    # Later, restore from checkpoint
    print("   Restoring from checkpoint...")
    restored_db = GraphDB()
    start_time = time.time()
    restored_db.load_pickle(checkpoint_file)
    load_time = time.time() - start_time
    print(f"   Checkpoint restored in {load_time:.3f} seconds")
    print(f"   Restored {restored_db.node_count} items")

    # Scenario 2: Model persistence
    print("\n🤖 Scenario 2: Machine Learning Model Persistence")
    print("   Creating graph - based model data...")

    model_db = GraphDB()

    # Create model structure (simplified neural network representation)
    for layer in range(3):
        for neuron in range(10):
            model_db.execute('''
                CREATE (n{layer}_{neuron}:Neuron {{
                    layer: {layer},
                    neuron_id: {neuron},
                    weights: [{neuron * 0.1 + i * 0.01 for i in range(5)}],
                    bias: {neuron * 0.05},
                    activation: "relu"
                }})
            ''')

    # Create connections between layers
    for layer in range(2):
        for src_neuron in range(10):
            for tgt_neuron in range(10):
                src_nodes = model_db.find_nodes(properties={'layer': layer, 'neuron_id': src_neuron})
                tgt_nodes = model_db.find_nodes(properties={'layer': layer + 1, 'neuron_id': tgt_neuron})

                if src_nodes and tgt_nodes:
                    model_db.create_relationship(
                        src_nodes[0]['id'],
                        tgt_nodes[0]['id'],
                        'CONNECTS_TO',
                        {'weight': (src_neuron + tgt_neuron) * 0.01}
                    )

    model_file = temp_dir / "neural_network_model.pkl"
    print("   Saving model...")
    model_db.save_pickle(model_file)
    print(f"   Model saved: {model_file.stat().st_size:,} bytes")

    # Load model for inference
    print("   Loading model for inference...")
    inference_db = GraphDB()
    inference_db.load_pickle(model_file)

    # Query model structure
    result = inference_db.execute('''
        MATCH (n:Neuron)
        RETURN n.layer, COUNT(*) as neuron_count
    ''')

    print("   Model structure:")
    for record in result:
        layer = record.get('n.layer')
        count = record.get('COUNT(*)')
        if layer is not None and count is not None:
            print(f"     Layer {layer}: {count} neurons")

    # Scenario 3: Backup and restore
    print("\n💾 Scenario 3: Backup and Restore")

    # Create production - like data
    prod_db = GraphDB()
    print("   Creating production data...")

    # Users
    for i in range(50):
        prod_db.execute(f'CREATE (u{i}:User {{id: {i}, name: "User{i}", created: "2024 - 01-{(i % 28) + 1:02d}"}})')

    # Orders
    for i in range(200):
        user_id = i % 50
        user_nodes = prod_db.find_nodes(properties={'id': user_id})
        if user_nodes:
            order_id = prod_db.create_node(
                ['Order'],
                {'id': i, 'amount': (i + 1) * 10.0, 'status': 'completed'}
            )
            prod_db.create_relationship(user_nodes[0]['id'], order_id, 'PLACED', {})

    # Create backup
    backup_file = temp_dir / "production_backup.pkl"
    print("   Creating backup...")
    start_time = time.time()
    prod_db.save_pickle(backup_file)
    backup_time = time.time() - start_time

    backup_size = backup_file.stat().st_size
    print(f"   Backup completed in {backup_time:.3f} seconds")
    print(f"   Backup size: {backup_size:,} bytes ({backup_size / 1024:.1f} KB)")

    # Simulate data loss and restore
    print("   Simulating data loss...")
    prod_db.clear()  # Simulate data loss
    print(f"   Data lost! Nodes: {prod_db.node_count}, Relationships: {prod_db.relationship_count}")

    print("   Restoring from backup...")
    start_time = time.time()
    prod_db.load_pickle(backup_file)
    restore_time = time.time() - start_time

    print(f"   Restore completed in {restore_time:.3f} seconds")
    print(f"   Data restored! Nodes: {prod_db.node_count}, Relationships: {prod_db.relationship_count}")

    # Verify data integrity
    result = prod_db.execute('MATCH (u:User)-[:PLACED]->(o:Order) RETURN COUNT(*) as order_count')
    order_count = result[0]['COUNT(*)'] if result else 0
    print(f"   Verified: {order_count} orders restored")

    # Clean up
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    """Main demonstration function."""
    print("🥒 PICKLE SERIALIZATION DEMONSTRATION")
    print("=" * 60)
    print("This example demonstrates the pickle serialization capabilities")
    print("of igraph - cypher - db for fast and efficient graph persistence.")

    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create and populate database
        db = GraphDB()
        create_large_graph(db, num_people=500, num_companies=25)

        # Benchmark performance
        benchmark_results = benchmark_serialization(db, temp_dir)

        # Demonstrate type preservation
        demonstrate_type_preservation()

        # Demonstrate practical usage
        demonstrate_practical_usage()

        # Final summary
        print("\n" + "="*60)
        print("📊 PERFORMANCE SUMMARY")
        print("="*60)
        print(f"Save Performance: Pickle is {benchmark_results['save_speedup']:.1f}x faster than JSON")
        print(f"Load Performance: Pickle is {benchmark_results['load_speedup']:.1f}x faster than JSON")
        print(f"File Size: Pickle is {benchmark_results['pickle_size'] / benchmark_results['json_size']:.1f}x the size of JSON")

        print("\n🎯 RECOMMENDATIONS:")
        print("✅ Use pickle for:")
        print("   • Fast backup / restore operations")
        print("   • Data processing checkpoints")
        print("   • Model persistence")
        print("   • Internal data storage")
        print("   • Large graph serialization")

        print("\n⚠️  Use JSON for:")
        print("   • Cross - platform compatibility")
        print("   • Human - readable exports")
        print("   • API data exchange")
        print("   • Configuration files")

        print("\n🎉 Pickle serialization implementation complete!")

    finally:
        # Clean up
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    main()
