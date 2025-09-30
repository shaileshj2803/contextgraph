"""
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import contextgraph
sys.path.insert(0, str(Path(__file__).parent.parent))

This example shows how to import large datasets from CSV files
into the graph database efficiently.
"""

import os
import csv
import time
from pathlib import Path
from contextgraph import GraphDB

def create_sample_data():
    """Create sample CSV files for demonstration."""

    # Create sample directory
    sample_dir = Path("sample_data")
    sample_dir.mkdir(exist_ok=True)

    # Create nodes CSV (people)
    people_file = sample_dir / "people.csv"
    with open(people_file, 'w', newline='', encoding='utf - 8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'name', 'age', 'city', 'department', 'salary', 'labels'])

        # Generate sample people data
        departments = ['Engineering', 'Marketing', 'Sales', 'HR', 'Finance']
        cities = ['NYC', 'SF', 'LA', 'Chicago', 'Boston', 'Seattle']

        for i in range(1000):
            writer.writerow([
                f'person_{i}',
                f'Person {i}',
                25 + (i % 40),  # Age 25 - 64
                cities[i % len(cities)],
                departments[i % len(departments)],
                50000 + (i * 100),  # Salary 50k - 150k
                'Person;Employee'
            ])

    # Create companies CSV
    companies_file = sample_dir / "companies.csv"
    with open(companies_file, 'w', newline='', encoding='utf - 8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'name', 'industry', 'size', 'founded', 'revenue'])

        industries = ['Technology', 'Finance', 'Healthcare', 'Retail', 'Manufacturing']
        sizes = ['Small', 'Medium', 'Large']

        for i in range(100):
            writer.writerow([
                f'company_{i}',
                f'Company {i} Inc',
                industries[i % len(industries)],
                sizes[i % len(sizes)],
                2000 + (i % 23),  # Founded 2000 - 2022
                1000000 + (i * 50000)  # Revenue 1M - 6M
            ])

    # Create relationships CSV (employment)
    employment_file = sample_dir / "employment.csv"
    with open(employment_file, 'w', newline='', encoding='utf - 8') as f:
        writer = csv.writer(f)
        writer.writerow(['source', 'target', 'type', 'position', 'start_date', 'salary_band'])

        positions = ['Engineer', 'Manager', 'Director', 'Analyst', 'Coordinator']

        # Each person works for a company
        for i in range(1000):
            company_id = f'company_{i % 100}'  # Distribute across companies
            writer.writerow([
                f'person_{i}',
                company_id,
                'WORKS_FOR',
                positions[i % len(positions)],
                f'2020-{(i % 12) + 1:02d}-01',
                f'Band_{(i % 5) + 1}'
            ])

    # Create friendships CSV
    friendships_file = sample_dir / "friendships.csv"
    with open(friendships_file, 'w', newline='', encoding='utf - 8') as f:
        writer = csv.writer(f)
        writer.writerow(['person1', 'person2', 'since', 'closeness'])

        # Create some friendships (about 2000 relationships)
        import random
        random.seed(42)  # For reproducible results

        friendships = set()
        for _ in range(2000):
            p1 = random.randint(0, 999)
            p2 = random.randint(0, 999)
            if p1 != p2:
                # Ensure no duplicates
                pair = tuple(sorted([p1, p2]))
                if pair not in friendships:
                    friendships.add(pair)
                    writer.writerow([
                        f'person_{p1}',
                        f'person_{p2}',
                        f'201{random.randint(5, 9)}-{random.randint(1, 12):02d}-01',
                        random.choice(['close', 'casual', 'professional'])
                    ])

    return {
        'people': people_file,
        'companies': companies_file,
        'employment': employment_file,
        'friendships': friendships_file
    }

def progress_callback(current, total):
    percentage = (current / total) * 100
    print(f"\rProgress: {current}/{total} ({percentage:.1f}%)", end='', flush=True)

def main():
    """Main demonstration function."""
    print("🚀 CSV Import Performance Demonstration")
    print("=" * 50)

    # Create sample data
    print("\n📊 Creating sample CSV files...")
    files = create_sample_data()
    print("✅ Sample data created:")
    for name, path in files.items():
        size = os.path.getsize(path) / 1024  # KB
        print(f"   • {name}: {path} ({size:.1f} KB)")

    # Initialize database
    print("\n🗄️  Initializing graph database...")
    db = GraphDB()

    # Import nodes (people)
    print(f"\n👥 Importing people from {files['people']}...")
    _ = time.time()  # noqa: F841

    people_stats = db.import_nodes_from_csv(
        files['people'],
        id_column='id',
        label_column='labels',  # Will parse "Person;Employee"
        progress_callback=progress_callback
    )

    print("\n✅ People import completed!")
    print(f"   • Imported: {people_stats['imported_nodes']} nodes")
    print(f"   • Time: {people_stats['processing_time']:.2f} seconds")
    print(f"   • Speed: {people_stats['nodes_per_second']:.0f} nodes / second")

    # Import nodes (companies)
    print(f"\n🏢 Importing companies from {files['companies']}...")

    companies_stats = db.import_nodes_from_csv(
        files['companies'],
        id_column='id',
        labels=['Company'],  # Fixed label for all companies
        progress_callback=progress_callback
    )

    print("\n✅ Companies import completed!")
    print(f"   • Imported: {companies_stats['imported_nodes']} nodes")
    print(f"   • Time: {companies_stats['processing_time']:.2f} seconds")
    print(f"   • Speed: {companies_stats['nodes_per_second']:.0f} nodes / second")

    # Import employment relationships
    print(f"\n💼 Importing employment relationships from {files['employment']}...")

    employment_stats = db.import_relationships_from_csv(
        files['employment'],
        source_column='source',
        target_column='target',
        type_column='type',
        progress_callback=progress_callback
    )

    print("\n✅ Employment relationships import completed!")
    print(f"   • Imported: {employment_stats['imported_relationships']} relationships")
    print(f"   • Time: {employment_stats['processing_time']:.2f} seconds")
    print(f"   • Speed: {employment_stats['relationships_per_second']:.0f} relationships / second")

    # Import friendship relationships
    print(f"\n👫 Importing friendships from {files['friendships']}...")

    friendship_stats = db.import_relationships_from_csv(
        files['friendships'],
        source_column='person1',
        target_column='person2',
        relationship_type='FRIENDS_WITH',
        progress_callback=progress_callback
    )

    print("\n✅ Friendships import completed!")
    print(f"   • Imported: {friendship_stats['imported_relationships']} relationships")
    print(f"   • Time: {friendship_stats['processing_time']:.2f} seconds")
    print(f"   • Speed: {friendship_stats['relationships_per_second']:.0f} relationships / second")

    # Display final statistics
    print("\n📈 Final Database Statistics:")
    print(f"   • Total nodes: {db.node_count}")
    print(f"   • Total relationships: {db.relationship_count}")

    total_time = (
        people_stats['processing_time'] +
        companies_stats['processing_time'] +
        employment_stats['processing_time'] +
        friendship_stats['processing_time']
    )
    print(f"   • Total import time: {total_time:.2f} seconds")

    # Test some queries on the imported data

    # Query 1: Count people by department
    result = db.execute('''
        MATCH (p:Person)-[:WORKS_FOR]->(c:Company)
        WHERE p.department = "Engineering"
        RETURN COUNT(*)
    ''')
    print(f"   • Engineers: {result[0]['COUNT(*)']}")

    # Query 2: Find high earners
    result = db.execute('''
        MATCH (p:Person)
        WHERE p.salary > 100000
        RETURN COUNT(*)
    ''')
    print(f"   • High earners (>100k): {result[0]['COUNT(*)']}")

    # Query 3: Average age by city
    result = db.execute('''
        MATCH (p:Person)
        RETURN p.city, AVG(p.age) as avg_age
    ''')
    print("   • Cities with average age:")
    for record in result[:3]:  # Show first 3
        if record.get('p.city') and record.get('avg_age'):
            print(f"     - {record['p.city']}: {record['avg_age']:.1f} years")

    # Query 4: Company with most employees
    result = db.execute('''
        MATCH (p:Person)-[:WORKS_FOR]->(c:Company)
        RETURN c.name, COUNT(*) as employee_count
    ''')
    if result:
        max_employees = max(result, key=lambda x: x.get('COUNT(*)', 0))
        print(f"   • Largest employer: {max_employees.get('c.name', 'N / A')} ({max_employees.get('COUNT(*)', 0)} employees)")

    # Demonstrate optimized batch relationship creation
    print("\n🚀 Demonstrating optimized batch relationship creation...")
    
    # Create some additional relationships using the new batch API
    print("Creating additional relationships using batch API...")
    
    # Get some random people for demonstration
    all_people = db.find_nodes(labels=['Person'])
    
    if len(all_people) >= 10:
        # Prepare batch relationship data
        batch_relationships = []
        for i in range(0, min(10, len(all_people) - 1)):
            batch_relationships.append({
                'source_id': all_people[i]['id'],
                'target_id': all_people[i + 1]['id'],
                'rel_type': 'COLLABORATES_WITH',
                'properties': {
                    'project': f'Project_{i}',
                    'start_date': '2024-01-01',
                    'intensity': i % 5 + 1
                }
            })
        
        # Time the batch creation
        start_time = time.time()
        batch_rel_ids = db.create_relationships_batch(batch_relationships)
        batch_time = time.time() - start_time
        
        print(f"   • Created {len(batch_rel_ids)} relationships in {batch_time:.4f} seconds")
        print(f"   • Batch creation rate: {len(batch_rel_ids)/batch_time:.0f} relationships/second")
        print(f"   • New total relationships: {db.relationship_count}")
    
    print("\n🎉 CSV Import demonstration completed successfully!")

if __name__ == "__main__":
    main()
