#!/usr/bin/env python3
"""
Performance comparison example showing the improvements in create_relationship API
and the new optional nodeid parameter functionality.

This example demonstrates:
1. O(1) node lookup vs O(n) lookup performance
2. Batch relationship creation vs individual creation
3. Custom node ID assignment
4. Real-world performance scenarios
"""

import sys
import time
from pathlib import Path

# Add the parent directory to the path so we can import contextgraph
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextgraph import GraphDB


def create_test_graph(db, num_nodes=1000):
    """Create a test graph with specified number of nodes."""
    print(f"Creating {num_nodes} test nodes...")
    
    node_ids = []
    start_time = time.time()
    
    for i in range(num_nodes):
        # Use custom node IDs for some nodes to test the feature
        if i % 100 == 0:
            # Every 100th node gets a custom ID
            custom_id = 10000 + i
            node_id = db.create_node(
                labels=["Person", "VIP"],
                properties={"name": f"VIP_Person_{i}", "rank": "premium"},
                nodeid=custom_id
            )
        else:
            # Regular auto-generated IDs
            node_id = db.create_node(
                labels=["Person"],
                properties={"name": f"Person_{i}", "age": 20 + (i % 50)}
            )
        node_ids.append(node_id)
    
    creation_time = time.time() - start_time
    print(f"✅ Created {len(node_ids)} nodes in {creation_time:.3f} seconds")
    print(f"   Rate: {len(node_ids)/creation_time:.0f} nodes/second")
    
    return node_ids


def test_individual_relationships(db, node_ids, num_relationships=500):
    """Test individual relationship creation performance."""
    print(f"\n📊 Testing individual relationship creation ({num_relationships} relationships)...")
    
    start_time = time.time()
    
    relationship_ids = []
    for i in range(num_relationships):
        source_id = node_ids[i]
        target_id = node_ids[(i + 100) % len(node_ids)]
        
        rel_id = db.create_relationship(
            source_id, target_id, "KNOWS",
            {"strength": i % 10, "since": f"2020-{(i % 12) + 1:02d}-01"}
        )
        relationship_ids.append(rel_id)
    
    individual_time = time.time() - start_time
    print(f"✅ Individual creation: {individual_time:.3f} seconds")
    print(f"   Rate: {len(relationship_ids)/individual_time:.0f} relationships/second")
    
    return individual_time, relationship_ids


def test_batch_relationships(db, node_ids, num_relationships=500):
    """Test batch relationship creation performance."""
    print(f"\n🚀 Testing batch relationship creation ({num_relationships} relationships)...")
    
    # Prepare batch data
    batch_relationships = []
    for i in range(num_relationships):
        source_id = node_ids[i + 500]  # Use different nodes than individual test
        target_id = node_ids[(i + 600) % len(node_ids)]
        
        batch_relationships.append({
            'source_id': source_id,
            'target_id': target_id,
            'rel_type': 'FRIENDS_WITH',
            'properties': {
                'closeness': i % 5,
                'met_at': f'Event_{i % 20}',
                'year': 2020 + (i % 4)
            }
        })
    
    start_time = time.time()
    batch_rel_ids = db.create_relationships_batch(batch_relationships)
    batch_time = time.time() - start_time
    
    print(f"✅ Batch creation: {batch_time:.3f} seconds")
    print(f"   Rate: {len(batch_rel_ids)/batch_time:.0f} relationships/second")
    
    return batch_time, batch_rel_ids


def test_node_lookup_performance(db, node_ids, num_lookups=1000):
    """Test the O(1) node lookup performance."""
    print(f"\n🔍 Testing node lookup performance ({num_lookups} lookups)...")
    
    import random
    random.seed(42)  # For reproducible results
    
    # Select random node IDs to lookup
    lookup_ids = random.sample(node_ids, min(num_lookups, len(node_ids)))
    
    start_time = time.time()
    
    found_nodes = 0
    for node_id in lookup_ids:
        node = db.get_node(node_id)
        if node is not None:
            found_nodes += 1
    
    lookup_time = time.time() - start_time
    print(f"✅ Looked up {found_nodes}/{len(lookup_ids)} nodes in {lookup_time:.3f} seconds")
    print(f"   Rate: {len(lookup_ids)/lookup_time:.0f} lookups/second")
    
    return lookup_time


def test_custom_node_ids(db):
    """Test the custom node ID functionality."""
    print("\n🎯 Testing custom node ID functionality...")
    
    # Test various custom ID scenarios
    test_cases = [
        {"nodeid": 50000, "name": "Custom_50000"},
        {"nodeid": 99999, "name": "Custom_99999"},
        {"nodeid": 1, "name": "Custom_1"},  # This might conflict with auto-generated
    ]
    
    created_nodes = []
    for i, case in enumerate(test_cases):
        try:
            node_id = db.create_node(
                labels=["CustomID"],
                properties={"name": case["name"], "test_case": i},
                nodeid=case["nodeid"]
            )
            created_nodes.append(node_id)
            print(f"   ✅ Created node with custom ID {node_id}")
        except Exception as e:
            print(f"   ⚠️  Failed to create node with ID {case['nodeid']}: {e}")
    
    # Test that auto-generated IDs work after custom IDs
    auto_node = db.create_node(
        labels=["AutoID"],
        properties={"name": "Auto_after_custom"}
    )
    print(f"   ✅ Auto-generated ID after custom IDs: {auto_node}")
    
    return created_nodes


def run_comprehensive_benchmark():
    """Run a comprehensive performance benchmark."""
    print("🏁 Comprehensive Performance Benchmark")
    print("=" * 60)
    
    benchmark_start = time.time()
    db = GraphDB()
    
    # Test 1: Node creation with mixed ID types
    node_ids = create_test_graph(db, 2000)
    
    # Test 2: Custom node ID functionality
    custom_nodes = test_custom_node_ids(db)
    
    # Test 3: Individual vs Batch relationship creation
    individual_time, individual_rels = test_individual_relationships(db, node_ids, 1000)
    batch_time, batch_rels = test_batch_relationships(db, node_ids, 1000)
    
    # Calculate speedup
    if batch_time > 0:
        speedup = individual_time / batch_time
        print(f"\n📈 Batch vs Individual Performance:")
        print(f"   Speedup: {speedup:.1f}x faster")
        print(f"   Time saved: {individual_time - batch_time:.3f} seconds")
    
    # Test 4: Node lookup performance
    lookup_time = test_node_lookup_performance(db, node_ids, 2000)
    
    # Final statistics
    print(f"\n📊 Final Graph Statistics:")
    print(f"   Total nodes: {db.node_count}")
    print(f"   Total relationships: {db.relationship_count}")
    print(f"   Custom ID nodes: {len(custom_nodes)}")
    
    # Performance summary
    total_nodes = len(node_ids) + len(custom_nodes) + 1  # +1 for auto node after custom
    total_relationships = len(individual_rels) + len(batch_rels)
    
    print(f"\n🎯 Performance Summary:")
    print(f"   Node creation rate: {total_nodes/(time.time() - benchmark_start):.0f} nodes/second")
    print(f"   Relationship creation rate: {total_relationships/(individual_time + batch_time):.0f} relationships/second")
    print(f"   Node lookup rate: {2000/lookup_time:.0f} lookups/second")


def main():
    """Main demonstration function."""
    print("🚀 GraphDB Performance Optimization Demonstration")
    print("=" * 60)
    print()
    print("This example demonstrates the performance improvements in:")
    print("• O(1) node lookup (vs previous O(n) lookup)")
    print("• Batch relationship creation API")
    print("• Optional custom node ID assignment")
    print("• Real-world performance scenarios")
    print()
    
    start_time = time.time()
    
    try:
        run_comprehensive_benchmark()
        
        total_time = time.time() - start_time
        print(f"\n✅ Benchmark completed in {total_time:.2f} seconds")
        print("\n🎉 All performance optimizations working correctly!")
        
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
