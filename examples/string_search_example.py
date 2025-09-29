"""
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import contextgraph
sys.path.insert(0, str(Path(__file__).parent.parent))
Example demonstrating comprehensive string search capabilities.

This example shows how to use string search operators and functions
for powerful text - based queries in the graph database.
"""

from contextgraph import GraphDB

def create_sample_data(db):
    """Create sample data for string search demonstrations."""
    print("📊 Creating sample data...")

    # Create people with various text patterns
    people_data = [
        {
            'name': 'Alice Johnson',
            'email': 'alice.johnson@techcorp.com',
            'bio': 'Senior Software Engineer specializing in Python and JavaScript',
            'city': 'New York',
            'phone': '+1 - 555 - 0123',
            'skills': 'Python, JavaScript, React, Node.js',
            'company': 'TechCorp'
        },
        {
            'name': 'Bob Smith',
            'email': 'bob.smith@datatech.org',
            'bio': 'Data Scientist with expertise in machine learning and AI',
            'city': 'San Francisco',
            'phone': '+1 - 555 - 0456',
            'skills': 'Python, R, TensorFlow, Pandas',
            'company': 'DataTech'
        },
        {
            'name': 'Charlie Brown',
            'email': 'charlie@designstudio.io',
            'bio': 'Creative Frontend Developer and UI / UX Designer',
            'city': 'Austin',
            'phone': '+1 - 555 - 0789',
            'skills': 'JavaScript, CSS, HTML, Figma',
            'company': 'DesignStudio'
        },
        {
            'name': 'Diana Prince',
            'email': 'diana.prince@cloudops.net',
            'bio': 'DevOps Engineer with cloud infrastructure expertise',
            'city': 'Seattle',
            'phone': '+1 - 555 - 0321',
            'skills': 'AWS, Kubernetes, Docker, Terraform',
            'company': 'CloudOps'
        },
        {
            'name': 'Eve Wilson',
            'email': 'eve@securityfirst.com',
            'bio': 'Cybersecurity Specialist focusing on network security',
            'city': 'Boston',
            'phone': '+1 - 555 - 0654',
            'skills': 'Network Security, Penetration Testing, CISSP',
            'company': 'SecurityFirst'
        }
    ]

    for person in people_data:
        db.create_node(['Person'], person)

    print(f"✅ Created {len(people_data)} people with rich text data")

def demonstrate_string_operators(db):
    """Demonstrate string search operators."""
    print("\n" + "="*60)
    print("🔍 STRING SEARCH OPERATORS")
    print("="*60)

    # CONTAINS operator
    print("\n📌 CONTAINS Operator:")
    print("   Finding people with 'Engineer' in their bio...")
    result = db.execute('''
        MATCH (p:Person)
        WHERE p.bio CONTAINS "Engineer"
        RETURN p.name, p.bio
    ''')

    for record in result:
        print(f"   • {record['p.name']}: {record['p.bio']}")

    # STARTS WITH operator
    print("\n📌 STARTS WITH Operator:")
    print("   Finding people whose names start with 'A'...")
    result = db.execute('''
        MATCH (p:Person)
        WHERE p.name STARTS WITH "A"
        RETURN p.name, p.city
    ''')

    for record in result:
        print(f"   • {record['p.name']} from {record['p.city']}")

    # ENDS WITH operator
    print("\n📌 ENDS WITH Operator:")
    print("   Finding people with .com email addresses...")
    result = db.execute('''
        MATCH (p:Person)
        WHERE p.email ENDS WITH ".com"
        RETURN p.name, p.email
    ''')

    for record in result:
        print(f"   • {record['p.name']}: {record['p.email']}")

    # REGEX operator
    print("\n📌 REGEX Operator (=~):")
    print("   Finding people with phone numbers matching pattern...")
    result = db.execute('''
        MATCH (p:Person)
        WHERE p.phone =~ "\\+1 - 555 - 0[0 - 9]{3}"
        RETURN p.name, p.phone
    ''')

    for record in result:
        print(f"   • {record['p.name']}: {record['p.phone']}")

    print("\n📌 Complex REGEX:")
    print("   Finding emails with specific domain patterns...")
    result = db.execute('''
        MATCH (p:Person)
        WHERE p.email =~ ".*@(tech|data).*\\.(com|org)"
        RETURN p.name, p.email, p.company
    ''')

    for record in result:
        print(f"   • {record['p.name']} ({record['p.company']}): {record['p.email']}")

def demonstrate_string_functions(db):
    """Demonstrate string manipulation functions."""
    print("\n" + "="*60)
    print("🔧 STRING MANIPULATION FUNCTIONS")
    print("="*60)

    # Case conversion functions
    print("\n📌 Case Conversion:")
    result = db.execute('''
        MATCH (p:Person)
        WHERE p.name STARTS WITH "Alice"
        RETURN p.name, UPPER(p.name), LOWER(p.name)
    ''')

    for record in result:
        print(f"   Original: {record['p.name']}")
        print(f"   UPPER:    {record['UPPER(p.name)']}")
        print(f"   LOWER:    {record['LOWER(p.name)']}")

    # Length function
    print("\n📌 String Length:")
    result = db.execute('''
        MATCH (p:Person)
        RETURN p.name, LENGTH(p.name), LENGTH(p.skills)
    ''')

    print("   Name lengths and skill string lengths:")
    for record in result:
        print(f"   • {record['p.name']}: {record['LENGTH(p.name)']} chars, Skills: {record['LENGTH(p.skills)']} chars")

    # Trim functions
    print("\n📌 String Trimming:")
    # Create a test node with padded text
    test_id = db.create_node(['Test'], {
        'padded_text': '   Hello World   ',
        'left_padded': '   Left Padded',
        'right_padded': 'Right Padded   '
    })

    result = db.execute('''
        MATCH (t:Test)
        RETURN t.padded_text, TRIM(t.padded_text),
               LTRIM(t.left_padded), RTRIM(t.right_padded)
    ''')

    for record in result:
        print(f"   Original padded: '{record['t.padded_text']}'")
        print(f"   TRIM result:     '{record['TRIM(t.padded_text)']}'")
        print(f"   LTRIM result:    '{record['LTRIM(t.left_padded)']}'")
        print(f"   RTRIM result:    '{record['RTRIM(t.right_padded)']}'")

    # Reverse function
    print("\n📌 String Reversal:")
    result = db.execute('''
        MATCH (p:Person)
        WHERE p.name CONTAINS "Alice"
        RETURN p.name, REVERSE(p.name)
    ''')

    for record in result:
        print(f"   {record['p.name']} reversed: {record['REVERSE(p.name)']}")

def demonstrate_advanced_operations(db):
    """Demonstrate advanced string search combinations."""
    print("\n" + "="*60)
    print("🚀 ADVANCED STRING OPERATIONS")
    print("="*60)

    # Combining multiple string operators
    print("\n📌 Combined String Operators:")
    print("   Finding engineers in tech companies with .com emails...")
    result = db.execute('''
        MATCH (p:Person)
        WHERE p.bio CONTAINS "Engineer"
        AND p.email ENDS WITH ".com"
        AND p.company CONTAINS "Tech"
        RETURN p.name, p.bio, p.company
    ''')

    for record in result:
        print(f"   • {record['p.name']} at {record['p.company']}")
        print(f"     Bio: {record['p.bio']}")

    # String functions with filtering
    print("\n📌 String Functions with Filtering:")
    print("   People with long names (>10 characters) in uppercase...")
    result = db.execute('''
        MATCH (p:Person)
        WHERE LENGTH(p.name) > 10
        RETURN UPPER(p.name), LENGTH(p.name), p.city
    ''')

    for record in result:
        print(f"   • {record['UPPER(p.name)']} ({record['LENGTH(p.name)']} chars) from {record['p.city']}")

    # Pattern matching with skills
    print("\n📌 Skill - based Pattern Matching:")
    print("   Finding Python developers using regex...")
    result = db.execute('''
        MATCH (p:Person)
        WHERE p.skills =~ ".*Python.*"
        RETURN p.name, p.skills, p.bio
    ''')

    for record in result:
        print(f"   • {record['p.name']}")
        print(f"     Skills: {record['p.skills']}")
        print(f"     Role: {record['p.bio']}")

    # Case - insensitive search simulation
    print("\n📌 Case - Insensitive Search (using LOWER):")
    print("   Finding people with 'JAVASCRIPT' skills (case - insensitive)...")
    result = db.execute('''
        MATCH (p:Person)
        WHERE LOWER(p.skills) CONTAINS "javascript"
        RETURN p.name, p.skills
    ''')

    for record in result:
        print(f"   • {record['p.name']}: {record['p.skills']}")

def demonstrate_performance_features(db):
    """Demonstrate performance - oriented string search features."""
    print("\n" + "="*60)
    print("⚡ PERFORMANCE & PRACTICAL EXAMPLES")
    print("="*60)

    # Efficient email domain extraction
    print("\n📌 Email Domain Analysis:")
    result = db.execute('''
        MATCH (p:Person)
        RETURN p.name, p.email
    ''')

    print("   Email domains found:")
    domains = set()
    for record in result:
        email = record['p.email']
        if '@' in email:
            domain = email.split('@')[1]
            domains.add(domain)
            print(f"   • {record['p.name']}: {domain}")

    print(f"\n   Unique domains: {', '.join(sorted(domains))}")

    # Phone number validation
    print("\n📌 Phone Number Validation:")
    result = db.execute('''
        MATCH (p:Person)
        WHERE p.phone =~ "\\+1 - 555-[0 - 9]{4}"
        RETURN p.name, p.phone
    ''')

    print("   Valid phone numbers:")
    for record in result:
        print(f"   • {record['p.name']}: {record['p.phone']}")

    # Skill counting
    print("\n📌 Skill Analysis:")
    result = db.execute('''
        MATCH (p:Person)
        RETURN p.name, p.skills, LENGTH(p.skills)
    ''')

    print("   Skill string lengths (proxy for skill count):")
    for record in result:
        skill_count = record['p.skills'].count(',') + 1 if record['p.skills'] else 0
        print(f"   • {record['p.name']}: ~{skill_count} skills ({record['LENGTH(p.skills)']} chars)")

def main():
    """Main demonstration function."""
    print("🔍 STRING SEARCH CAPABILITIES DEMONSTRATION")
    print("=" * 60)
    print("This example demonstrates the comprehensive string search")
    print("and manipulation capabilities of igraph - cypher - db.")

    # Initialize database
    db = GraphDB()

    # Create sample data
    create_sample_data(db)

    # Demonstrate different aspects
    demonstrate_string_operators(db)
    demonstrate_string_functions(db)
    demonstrate_advanced_operations(db)
    demonstrate_performance_features(db)

    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY OF STRING SEARCH FEATURES")
    print("="*60)
    print("✅ String Search Operators:")
    print("   • CONTAINS - substring search")
    print("   • STARTS WITH - prefix matching")
    print("   • ENDS WITH - suffix matching")
    print("   • =~ - regex pattern matching")

    print("\n✅ String Functions:")
    print("   • UPPER() / LOWER() - case conversion")
    print("   • TRIM() / LTRIM() / RTRIM() - whitespace removal")
    print("   • LENGTH() - string length")
    print("   • REVERSE() - string reversal")
    print("   • SUBSTRING() - extract substrings")
    print("   • REPLACE() - string replacement")
    print("   • SPLIT() - string splitting")

    print("\n✅ Advanced Features:")
    print("   • Complex regex patterns")
    print("   • Combined string operations")
    print("   • Case - insensitive search patterns")
    print("   • Integration with WHERE clauses")
    print("   • Performance - optimized operations")

    print("\n🎉 String search implementation complete!")
    print("   The igraph - cypher - db now supports comprehensive")
    print("   text search and manipulation capabilities!")

if __name__ == "__main__":
    main()
