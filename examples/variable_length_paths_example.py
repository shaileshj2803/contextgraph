#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import contextgraph
sys.path.insert(0, str(Path(__file__).parent.parent))
"""
Variable-Length Path Example for igraph-cypher-db

This example demonstrates the new variable-length path functionality,
which allows you to find paths of varying lengths between nodes using
Cypher syntax like *1..3, *2, and *.

Features demonstrated:
- Exact hop counts (*n)
- Range hop counts (*min..max)
- Unlimited hops (*)
- Path finding in social networks
- Cycle detection and handling
- Performance with larger graphs
"""

from contextgraph import GraphDB
import time


def create_social_network(db):
    """Create a sample social network for demonstration."""
    print("Creating social network...")
    
    # Create people
    people = [
        ('Alice', 'Engineer', 'TechCorp'),
        ('Bob', 'Designer', 'TechCorp'),
        ('Charlie', 'Manager', 'TechCorp'),
        ('Diana', 'Developer', 'StartupInc'),
        ('Eve', 'Analyst', 'StartupInc'),
        ('Frank', 'CEO', 'StartupInc'),
        ('Grace', 'Consultant', 'Freelance'),
        ('Henry', 'Researcher', 'University')
    ]
    
    person_ids = {}
    for name, role, company in people:
        person_id = db.create_node(['Person'], {
            'name': name,
            'role': role,
            'company': company
        })
        person_ids[name] = person_id
    
    # Create companies
    companies = ['TechCorp', 'StartupInc', 'Freelance', 'University']
    company_ids = {}
    for company in companies:
        company_id = db.create_node(['Company'], {'name': company})
        company_ids[company] = company_id
    
    # Create relationships - social connections
    connections = [
        ('Alice', 'Bob', 'KNOWS'),
        ('Bob', 'Charlie', 'KNOWS'),
        ('Charlie', 'Diana', 'KNOWS'),
        ('Diana', 'Eve', 'KNOWS'),
        ('Eve', 'Frank', 'KNOWS'),
        ('Alice', 'Grace', 'KNOWS'),
        ('Grace', 'Henry', 'KNOWS'),
        ('Frank', 'Henry', 'KNOWS'),  # Creates a longer path
        ('Charlie', 'Frank', 'MANAGES'),  # Cross-company connection
        ('Alice', 'Alice', 'MENTORS'),  # Self-loop for demonstration
    ]
    
    for person1, person2, rel_type in connections:
        db.create_relationship(person_ids[person1], person_ids[person2], rel_type)
    
    # Create employment relationships
    for name, role, company in people:
        db.create_relationship(person_ids[name], company_ids[company], 'WORKS_FOR')
    
    print(f"Created {db.node_count} nodes and {db.relationship_count} relationships")
    return person_ids, company_ids


def demonstrate_exact_hops(db):
    """Demonstrate exact hop count queries (*n)."""
    print("\n" + "="*60)
    print("EXACT HOP COUNT QUERIES (*n)")
    print("="*60)
    
    # Find people exactly 1 hop away via KNOWS relationships
    print("\n1. People exactly 1 hop away (direct connections):")
    result = db.execute('MATCH (a:Person)-[:KNOWS*1]->(b:Person) RETURN a.name, b.name')
    print(f"Found {len(result)} direct connections:")
    for r in result:
        print(f"  {r['a.name']} -> {r['b.name']}")
    
    # Find people exactly 2 hops away
    print("\n2. People exactly 2 hops away (friends of friends):")
    result = db.execute('MATCH (a:Person)-[:KNOWS*2]->(b:Person) RETURN a.name, b.name')
    print(f"Found {len(result)} 2-hop connections:")
    for r in result:
        print(f"  {r['a.name']} -> {r['b.name']}")
    
    # Find people exactly 3 hops away
    print("\n3. People exactly 3 hops away:")
    result = db.execute('MATCH (a:Person)-[:KNOWS*3]->(b:Person) RETURN a.name, b.name')
    print(f"Found {len(result)} 3-hop connections:")
    for r in result:
        print(f"  {r['a.name']} -> {r['b.name']}")


def demonstrate_range_hops(db):
    """Demonstrate range hop count queries (*min..max)."""
    print("\n" + "="*60)
    print("RANGE HOP COUNT QUERIES (*min..max)")
    print("="*60)
    
    # Find all people within 1-2 hops
    print("\n1. People within 1-2 hops of Alice:")
    result = db.execute(
        'MATCH (a:Person)-[:KNOWS*1..2]->(b:Person) '
        'WHERE a.name = "Alice" '
        'RETURN a.name, b.name'
    )
    print(f"Found {len(result)} people within 1-2 hops of Alice:")
    for r in result:
        print(f"  {r['a.name']} -> {r['b.name']}")
    
    # Find all people within 1-3 hops
    print("\n2. People within 1-3 hops of Alice:")
    result = db.execute(
        'MATCH (a:Person)-[:KNOWS*1..3]->(b:Person) '
        'WHERE a.name = "Alice" '
        'RETURN a.name, b.name'
    )
    print(f"Found {len(result)} people within 1-3 hops of Alice:")
    for r in result:
        print(f"  {r['a.name']} -> {r['b.name']}")
    
    # Find people in a specific range (2-4 hops)
    print("\n3. People exactly 2-4 hops from Alice:")
    result = db.execute(
        'MATCH (a:Person)-[:KNOWS*2..4]->(b:Person) '
        'WHERE a.name = "Alice" '
        'RETURN a.name, b.name'
    )
    print(f"Found {len(result)} people 2-4 hops from Alice:")
    for r in result:
        print(f"  {r['a.name']} -> {r['b.name']}")


def demonstrate_unlimited_hops(db):
    """Demonstrate unlimited hop queries (*)."""
    print("\n" + "="*60)
    print("UNLIMITED HOP QUERIES (*)")
    print("="*60)
    
    # Find all people reachable from Alice
    print("\n1. All people reachable from Alice via KNOWS relationships:")
    result = db.execute(
        'MATCH (a:Person)-[:KNOWS*]->(b:Person) '
        'WHERE a.name = "Alice" '
        'RETURN a.name, b.name'
    )
    print(f"Found {len(result)} people reachable from Alice:")
    for r in result:
        print(f"  {r['a.name']} -> {r['b.name']}")
    
    # Find all reachable pairs
    print("\n2. All reachable pairs in the network:")
    result = db.execute('MATCH (a:Person)-[:KNOWS*]->(b:Person) RETURN a.name, b.name')
    print(f"Found {len(result)} total reachable pairs:")
    
    # Group by source for better readability
    from collections import defaultdict
    by_source = defaultdict(list)
    for r in result:
        by_source[r['a.name']].append(r['b.name'])
    
    for source, targets in sorted(by_source.items()):
        print(f"  {source} can reach: {', '.join(sorted(targets))}")


def demonstrate_mixed_relationship_types(db):
    """Demonstrate variable-length paths with different relationship types."""
    print("\n" + "="*60)
    print("MIXED RELATIONSHIP TYPES")
    print("="*60)
    
    # Find people connected via KNOWS relationships
    print("\n1. Connections via KNOWS relationships:")
    result = db.execute('MATCH (a:Person)-[:KNOWS*1..3]->(b:Person) RETURN a.name, b.name')
    print(f"Found {len(result)} KNOWS connections:")
    for r in result[:10]:  # Show first 10
        print(f"  {r['a.name']} -> {r['b.name']}")
    if len(result) > 10:
        print(f"  ... and {len(result) - 10} more")
    
    # Find people connected via MANAGES relationships
    print("\n2. Connections via MANAGES relationships:")
    result = db.execute('MATCH (a:Person)-[:MANAGES*1..2]->(b:Person) RETURN a.name, b.name')
    print(f"Found {len(result)} MANAGES connections:")
    for r in result:
        print(f"  {r['a.name']} -> {r['b.name']}")
    
    # Find employment chains (people -> companies)
    print("\n3. Employment relationships (1-2 hops to companies):")
    result = db.execute('MATCH (a:Person)-[:WORKS_FOR*1..2]->(b) RETURN a.name, b.name')
    print(f"Found {len(result)} employment connections:")
    for r in result:
        print(f"  {r['a.name']} -> {r['b.name']}")


def demonstrate_self_loops(db):
    """Demonstrate handling of self-loops."""
    print("\n" + "="*60)
    print("SELF-LOOPS AND CYCLES")
    print("="*60)
    
    # Find self-referential relationships
    print("\n1. Self-referential relationships:")
    result = db.execute('MATCH (a:Person)-[:MENTORS*1]->(b:Person) RETURN a.name, b.name')
    print(f"Found {len(result)} MENTORS relationships:")
    for r in result:
        print(f"  {r['a.name']} -> {r['b.name']}")
    
    # Find paths that include self-loops
    print("\n2. Multi-hop paths including self-loops:")
    result = db.execute('MATCH (a:Person)-[:MENTORS*1..3]->(b:Person) RETURN a.name, b.name')
    print(f"Found {len(result)} paths including self-loops:")
    for r in result:
        print(f"  {r['a.name']} -> {r['b.name']}")


def demonstrate_performance(db):
    """Demonstrate performance characteristics."""
    print("\n" + "="*60)
    print("PERFORMANCE DEMONSTRATION")
    print("="*60)
    
    # Test performance with different hop ranges
    test_cases = [
        ('*1', 'Direct connections'),
        ('*1..2', '1-2 hops'),
        ('*1..3', '1-3 hops'),
        ('*1..4', '1-4 hops'),
        ('*', 'Unlimited (up to default limit)')
    ]
    
    for pattern, description in test_cases:
        start_time = time.time()
        result = db.execute(f'MATCH (a:Person)-[:KNOWS{pattern}]->(b:Person) RETURN a.name, b.name')
        end_time = time.time()
        
        print(f"{description:25} | {len(result):3} results | {(end_time - start_time)*1000:6.2f}ms")


def demonstrate_practical_use_cases(db):
    """Demonstrate practical use cases for variable-length paths."""
    print("\n" + "="*60)
    print("PRACTICAL USE CASES")
    print("="*60)
    
    # Use case 1: Find mutual connections
    print("\n1. Find people who can introduce Alice to Frank:")
    result = db.execute('''
        MATCH (alice:Person)-[:KNOWS*1..2]->(intermediary:Person)-[:KNOWS*1..2]->(frank:Person)
        WHERE alice.name = "Alice" AND frank.name = "Frank"
        RETURN alice.name, intermediary.name, frank.name
    ''')
    print(f"Found {len(result)} potential introducers:")
    for r in result:
        print(f"  {r['alice.name']} -> {r['intermediary.name']} -> {r['frank.name']}")
    
    # Use case 2: Find shortest paths (within reasonable limits)
    print("\n2. Find people within 2 degrees of separation from Alice:")
    result = db.execute('''
        MATCH (alice:Person)-[:KNOWS*1..2]->(person:Person)
        WHERE alice.name = "Alice"
        RETURN alice.name, person.name, person.company
    ''')
    print(f"Found {len(result)} people within 2 degrees:")
    for r in result:
        print(f"  {r['alice.name']} -> {r['person.name']} ({r['person.company']})")
    
    # Use case 3: Find cross-company connections
    print("\n3. Find cross-company connections (people from different companies):")
    result = db.execute('''
        MATCH (a:Person)-[:KNOWS*1..3]->(b:Person)
        WHERE a.company <> b.company
        RETURN a.name, a.company, b.name, b.company
    ''')
    print(f"Found {len(result)} cross-company connections:")
    for r in result[:8]:  # Show first 8
        print(f"  {r['a.name']} ({r['a.company']}) -> {r['b.name']} ({r['b.company']})")
    if len(result) > 8:
        print(f"  ... and {len(result) - 8} more")


def main():
    """Main demonstration function."""
    print("Variable-Length Path Demonstration")
    print("=" * 60)
    print("This example demonstrates the new variable-length path functionality")
    print("in igraph-cypher-db, which supports Cypher syntax like:")
    print("  - *n (exact n hops)")
    print("  - *min..max (range of hops)")
    print("  - * (unlimited hops, with reasonable default limit)")
    
    # Create database and sample data
    db = GraphDB()
    person_ids, company_ids = create_social_network(db)
    
    # Run demonstrations
    demonstrate_exact_hops(db)
    demonstrate_range_hops(db)
    demonstrate_unlimited_hops(db)
    demonstrate_mixed_relationship_types(db)
    demonstrate_self_loops(db)
    demonstrate_performance(db)
    demonstrate_practical_use_cases(db)
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("Variable-length path functionality provides powerful graph traversal")
    print("capabilities for finding connections, analyzing networks, and")
    print("discovering relationships at various degrees of separation.")
    print()
    print("Key features:")
    print("✓ Exact hop counts (*2, *3, etc.)")
    print("✓ Range hop counts (*1..3, *2..5, etc.)")
    print("✓ Unlimited hops (*) with cycle detection")
    print("✓ Support for different relationship types")
    print("✓ Self-loop handling")
    print("✓ Performance optimization for large graphs")
    print("✓ Integration with WHERE clauses and property filtering")


if __name__ == '__main__':
    main()
