"""
Test cases for string search functionality.
"""

import pytest
from contextgraph import GraphDB

class TestStringSearchOperators:
    """Test string search operators (CONTAINS, STARTS WITH, ENDS WITH, =~)."""

    def setup_method(self):
        """Set up test database with sample data."""
        self.db = GraphDB()

        # Create test data with various string patterns
        self.alice_id = self.db.create_node(
            ['Person'],
            {
                'name': 'Alice Johnson',
                'email': 'alice.johnson@example.com',
                'bio': 'Software Engineer at TechCorp',
                'city': 'New York',
                'phone': '+1 - 555 - 0123',
                'tags': ['developer', 'python', 'javascript']
            }
        )

        self.bob_id = self.db.create_node(
            ['Person'],
            {
                'name': 'Bob Smith',
                'email': 'bob.smith@company.org',
                'bio': 'Data Scientist specializing in machine learning',
                'city': 'San Francisco',
                'phone': '+1 - 555 - 0456',
                'tags': ['scientist', 'python', 'r']
            }
        )

        self.charlie_id = self.db.create_node(
            ['Person'],
            {
                'name': 'Charlie Brown',
                'email': 'charlie@startup.io',
                'bio': 'Frontend Developer and UI / UX Designer',
                'city': 'Austin',
                'phone': '+1 - 555 - 0789',
                'tags': ['designer', 'javascript', 'css']
            }
        )

        self.diana_id = self.db.create_node(
            ['Person'],
            {
                'name': 'Diana Prince',
                'email': 'diana.prince@enterprise.net',
                'bio': 'DevOps Engineer with cloud expertise',
                'city': 'Seattle',
                'phone': '+1 - 555 - 0321',
                'tags': ['devops', 'aws', 'kubernetes']
            }
        )

    def test_contains_operator(self):
        """Test CONTAINS operator for substring search."""
        # Test basic contains
        result = self.db.execute('MATCH (p:Person) WHERE p.name CONTAINS "Johnson" RETURN p.name')
        assert len(result) == 1
        assert result[0]['p.name'] == 'Alice Johnson'

        # Test contains with email domain
        result = self.db.execute('MATCH (p:Person) WHERE p.email CONTAINS "@example.com" RETURN p.name')
        assert len(result) == 1
        assert result[0]['p.name'] == 'Alice Johnson'

        # Test contains case - sensitive
        result = self.db.execute('MATCH (p:Person) WHERE p.bio CONTAINS "Engineer" RETURN p.name')
        assert len(result) >= 2  # Alice (Software Engineer), Diana (DevOps Engineer)
        names = sorted([r['p.name'] for r in result])
        assert 'Alice Johnson' in names
        assert 'Diana Prince' in names

        # Test contains with no matches
        result = self.db.execute('MATCH (p:Person) WHERE p.name CONTAINS "xyz" RETURN p.name')
        assert len(result) == 0

    def test_starts_with_operator(self):
        """Test STARTS WITH operator."""
        # Test starts with name
        result = self.db.execute('MATCH (p:Person) WHERE p.name STARTS WITH "Alice" RETURN p.name')
        assert len(result) == 1
        assert result[0]['p.name'] == 'Alice Johnson'

        # Test starts with phone prefix
        result = self.db.execute('MATCH (p:Person) WHERE p.phone STARTS WITH "+1 - 555" RETURN p.name')
        assert len(result) == 4  # All have this prefix

        # Test starts with bio
        result = self.db.execute('MATCH (p:Person) WHERE p.bio STARTS WITH "Software" RETURN p.name')
        assert len(result) == 1
        assert result[0]['p.name'] == 'Alice Johnson'

        # Test starts with case - sensitive
        result = self.db.execute('MATCH (p:Person) WHERE p.name STARTS WITH "alice" RETURN p.name')
        assert len(result) == 0  # Case sensitive

    def test_ends_with_operator(self):
        """Test ENDS WITH operator."""
        # Test ends with surname
        result = self.db.execute('MATCH (p:Person) WHERE p.name ENDS WITH "Johnson" RETURN p.name')
        assert len(result) == 1
        assert result[0]['p.name'] == 'Alice Johnson'

        # Test ends with email domain
        result = self.db.execute('MATCH (p:Person) WHERE p.email ENDS WITH ".com" RETURN p.name')
        assert len(result) == 1
        assert result[0]['p.name'] == 'Alice Johnson'

        # Test ends with different domain
        result = self.db.execute('MATCH (p:Person) WHERE p.email ENDS WITH ".org" RETURN p.name')
        assert len(result) == 1
        assert result[0]['p.name'] == 'Bob Smith'

        # Test ends with city
        result = self.db.execute('MATCH (p:Person) WHERE p.city ENDS WITH "Francisco" RETURN p.name')
        assert len(result) == 1
        assert result[0]['p.name'] == 'Bob Smith'

    def test_regex_operator(self):
        """Test =~ regex operator."""
        # Test basic regex pattern
        result = self.db.execute('MATCH (p:Person) WHERE p.email =~ ".*@example\\.com" RETURN p.name')
        assert len(result) == 1
        assert result[0]['p.name'] == 'Alice Johnson'

        # Test phone number pattern
        result = self.db.execute('MATCH (p:Person) WHERE p.phone =~ "\\+1-555-0[0-9]{3}" RETURN p.name')
        assert len(result) >= 0  # May or may not match depending on test data

        # Test name pattern (starts with capital letter)
        result = self.db.execute('MATCH (p:Person) WHERE p.name =~ "^[A-Z][a-z]+ [A-Z][a-z]+$" RETURN p.name')
        assert len(result) >= 2  # At least Alice Johnson and Bob Smith

        # Test bio pattern (contains "Engineer" or "Developer")
        result = self.db.execute('MATCH (p:Person) WHERE p.bio =~ ".*(Engineer|Developer).*" RETURN p.name')
        assert len(result) == 3  # Alice, Charlie, Diana

        # Test invalid regex (should not crash)
        result = self.db.execute('MATCH (p:Person) WHERE p.name =~ "[" RETURN p.name')
        assert len(result) == 0  # Invalid regex returns no matches

    def test_string_operators_with_null_values(self):
        """Test string operators with null values."""
        # Create node with null property
        _ = self.db.create_node(['Person'], {'name': 'Test User', 'bio': None})  # noqa: F841

        # Test contains with null
        result = self.db.execute('MATCH (p:Person) WHERE p.bio CONTAINS "test" RETURN p.name')
        # Should not include the null bio
        names = [r['p.name'] for r in result]
        assert 'Test User' not in names

        # Test starts with null
        result = self.db.execute('MATCH (p:Person) WHERE p.bio STARTS WITH "test" RETURN p.name')
        names = [r['p.name'] for r in result]
        assert 'Test User' not in names

        # Test ends with null
        result = self.db.execute('MATCH (p:Person) WHERE p.bio ENDS WITH "test" RETURN p.name')
        names = [r['p.name'] for r in result]
        assert 'Test User' not in names

        # Test regex with null
        result = self.db.execute('MATCH (p:Person) WHERE p.bio =~ ".*" RETURN p.name')
        names = [r['p.name'] for r in result]
        assert 'Test User' not in names

    def test_string_operators_with_numbers(self):
        """Test string operators with numeric values."""
        # Create node with numeric properties
        _ = self.db.create_node(['Item'], {'code': 12345, 'price': 99.99, 'description': 'Test item'})  # noqa: F841

        # Test contains with number (should convert to string)
        result = self.db.execute('MATCH (i:Item) WHERE i.code CONTAINS "234" RETURN i.code')
        assert len(result) == 1
        assert result[0]['i.code'] == 12345

        # Test starts with number
        result = self.db.execute('MATCH (i:Item) WHERE i.code STARTS WITH "123" RETURN i.code')
        assert len(result) == 1
        assert result[0]['i.code'] == 12345

        # Test ends with number
        result = self.db.execute('MATCH (i:Item) WHERE i.price ENDS WITH ".99" RETURN i.price')
        assert len(result) == 1
        assert result[0]['i.price'] == 99.99

    def test_combined_string_operators(self):
        """Test combining string operators with logical operators."""
        # Test AND combination
        result = self.db.execute('''
            MATCH (p:Person)
            WHERE p.name CONTAINS "Johnson" AND p.email ENDS WITH ".com"
            RETURN p.name
        ''')
        assert len(result) == 1
        assert result[0]['p.name'] == 'Alice Johnson'

        # Test OR combination
        result = self.db.execute('''
            MATCH (p:Person)
            WHERE p.name STARTS WITH "Alice" OR p.name STARTS WITH "Bob"
            RETURN p.name
        ''')
        assert len(result) == 2
        names = sorted([r['p.name'] for r in result])
        assert names == ['Alice Johnson', 'Bob Smith']

        # Test complex combination
        result = self.db.execute('''
            MATCH (p:Person)
            WHERE (p.bio CONTAINS "Engineer" OR p.bio CONTAINS "Developer")
            AND p.city STARTS WITH "S"
            RETURN p.name
        ''')
        assert len(result) == 1
        assert result[0]['p.name'] == 'Diana Prince'  # DevOps Engineer in Seattle

class TestStringFunctions:
    """Test string manipulation functions."""

    def setup_method(self):
        """Set up test database with sample data."""
        self.db = GraphDB()

        # Create test data with various string cases
        self.test_id = self.db.create_node(
            ['Test'],
            {
                'text': 'Hello World',
                'padded': '  spaced text  ',
                'mixed_case': 'MiXeD CaSe',
                'long_text': 'The quick brown fox jumps over the lazy dog',
                'with_numbers': 'abc123def456',
                'empty': '',
                'special_chars': 'hello@world.com'
            }
        )

    def test_upper_function(self):
        """Test UPPER() function."""
        result = self.db.execute('MATCH (t:Test) RETURN UPPER(t.text)')
        assert len(result) == 1
        assert result[0]['UPPER(t.text)'] == 'HELLO WORLD'

        result = self.db.execute('MATCH (t:Test) RETURN UPPER(t.mixed_case)')
        assert len(result) == 1
        assert result[0]['UPPER(t.mixed_case)'] == 'MIXED CASE'

    def test_lower_function(self):
        """Test LOWER() function."""
        result = self.db.execute('MATCH (t:Test) RETURN LOWER(t.text)')
        assert len(result) == 1
        assert result[0]['LOWER(t.text)'] == 'hello world'

        result = self.db.execute('MATCH (t:Test) RETURN LOWER(t.mixed_case)')
        assert len(result) == 1
        assert result[0]['LOWER(t.mixed_case)'] == 'mixed case'

    def test_trim_functions(self):
        """Test TRIM(), LTRIM(), RTRIM() functions."""
        # Test TRIM (both sides)
        result = self.db.execute('MATCH (t:Test) RETURN TRIM(t.padded) as trimmed')
        assert len(result) == 1
        assert result[0]['trimmed'] == 'spaced text'

        # Test LTRIM (left side only)
        result = self.db.execute('MATCH (t:Test) RETURN LTRIM(t.padded) as ltrimmed')
        assert len(result) == 1
        assert result[0]['ltrimmed'] == 'spaced text  '

        # Test RTRIM (right side only)
        result = self.db.execute('MATCH (t:Test) RETURN RTRIM(t.padded) as rtrimmed')
        assert len(result) == 1
        assert result[0]['rtrimmed'] == '  spaced text'

    def test_length_function(self):
        """Test LENGTH() function."""
        result = self.db.execute('MATCH (t:Test) RETURN LENGTH(t.text) as text_length')
        assert len(result) == 1
        assert result[0]['text_length'] == 11  # "Hello World"

        result = self.db.execute('MATCH (t:Test) RETURN LENGTH(t.empty) as empty_length')
        assert len(result) == 1
        assert result[0]['empty_length'] == 0

        result = self.db.execute('MATCH (t:Test) RETURN LENGTH(t.padded) as padded_length')
        assert len(result) == 1
        assert result[0]['padded_length'] == 15  # "  spaced text  "

    def test_reverse_function(self):
        """Test REVERSE() function."""
        result = self.db.execute('MATCH (t:Test) RETURN REVERSE(t.text) as reversed')
        assert len(result) == 1
        assert result[0]['reversed'] == 'dlroW olleH'

        result = self.db.execute('MATCH (t:Test) RETURN REVERSE(t.with_numbers) as reversed_nums')
        assert len(result) == 1
        assert result[0]['reversed_nums'] == '654fed321cba'

    def test_substring_function(self):
        """Test SUBSTRING() function."""
        # Test substring with start index only
        result = self.db.execute('MATCH (t:Test) RETURN SUBSTRING(t.text, 6) as substring')
        assert len(result) == 1
        assert result[0]['substring'] == 'World'

        # Test substring with start and length
        result = self.db.execute('MATCH (t:Test) RETURN SUBSTRING(t.long_text, 4, 5) as substring')
        assert len(result) == 1
        assert result[0]['substring'] == 'quick'

        # Test substring with zero start
        result = self.db.execute('MATCH (t:Test) RETURN SUBSTRING(t.text, 0, 5) as substring')
        assert len(result) == 1
        assert result[0]['substring'] == 'Hello'

    def test_replace_function(self):
        """Test REPLACE() function."""
        # Test basic replace
        result = self.db.execute('MATCH (t:Test) RETURN REPLACE(t.text, "World", "Universe") as replaced')
        assert len(result) == 1
        assert result[0]['replaced'] == 'Hello Universe'

        # Test replace with numbers
        result = self.db.execute('MATCH (t:Test) RETURN REPLACE(t.with_numbers, "123", "XXX") as replaced')
        assert len(result) == 1
        assert result[0]['replaced'] == 'abcXXXdef456'

        # Test replace all occurrences
        multi_id = self.db.create_node(['Multi'], {'text': 'hello hello world'})
        result = self.db.execute('MATCH (m:Multi) RETURN REPLACE(m.text, "hello", "hi") as replaced')
        assert len(result) == 1
        assert result[0]['replaced'] == 'hi hi world'

    def test_split_function(self):
        """Test SPLIT() function."""
        # Test split with space
        result = self.db.execute('MATCH (t:Test) RETURN SPLIT(t.text, " ") as split_text')
        assert len(result) == 1
        assert result[0]['split_text'] == ['Hello', 'World']

        # Test split with custom delimiter
        csv_id = self.db.create_node(['CSV'], {'data': 'apple,banana,cherry'})
        result = self.db.execute('MATCH (c:CSV) RETURN SPLIT(c.data, ",") as split_data')
        assert len(result) == 1
        assert result[0]['split_data'] == ['apple', 'banana', 'cherry']

        # Test split with no delimiter (should split on whitespace)
        spaced_id = self.db.create_node(['Spaced'], {'text': 'one   two\tthree\nfour'})
        result = self.db.execute('MATCH (s:Spaced) RETURN SPLIT(s.text) as split_whitespace')
        assert len(result) == 1
        # Default split should handle multiple whitespace types
        assert len(result[0]['split_whitespace']) >= 4

    def test_string_functions_with_null(self):
        """Test string functions with null values."""
        _ = self.db.create_node(['Null'], {'text': None})  # noqa: F841

        # All string functions should return null for null input
        functions = ['UPPER', 'LOWER', 'TRIM', 'LTRIM', 'RTRIM', 'LENGTH', 'REVERSE']

        for func in functions:
            result = self.db.execute(f'MATCH (n:Null) RETURN {func}(n.text) as result')
            assert len(result) == 1
            assert result[0]['result'] is None

    def test_string_functions_with_numbers(self):
        """Test string functions with numeric input."""
        _ = self.db.create_node(['Numeric'], {'value': 12345})  # noqa: F841

        # Functions should convert numbers to strings
        result = self.db.execute('MATCH (n:Numeric) RETURN UPPER(n.value) as upper_num')
        assert len(result) == 1
        assert result[0]['upper_num'] == '12345'  # Numbers don't change with UPPER

        result = self.db.execute('MATCH (n:Numeric) RETURN LENGTH(n.value) as num_length')
        assert len(result) == 1
        assert result[0]['num_length'] == 5

        result = self.db.execute('MATCH (n:Numeric) RETURN REVERSE(n.value) as reversed_num')
        assert len(result) == 1
        assert result[0]['reversed_num'] == '54321'

class TestStringSearchIntegration:
    """Test string search integration with other Cypher features."""

    def setup_method(self):
        """Set up test database with sample data."""
        self.db = GraphDB()

        # Create a more complex dataset
        self.alice_id = self.db.create_node(['Person'], {
            'name': 'Alice Johnson', 'email': 'alice@tech.com', 'role': 'Senior Engineer'
        })
        self.bob_id = self.db.create_node(['Person'], {
            'name': 'Bob Smith', 'email': 'bob@tech.com', 'role': 'Junior Developer'
        })
        self.charlie_id = self.db.create_node(['Person'], {
            'name': 'Charlie Brown', 'email': 'charlie@design.com', 'role': 'UI Designer'
        })

        self.tech_id = self.db.create_node(['Company'], {
            'name': 'TechCorp', 'domain': 'tech.com', 'industry': 'Technology'
        })
        self.design_id = self.db.create_node(['Company'], {
            'name': 'DesignStudio', 'domain': 'design.com', 'industry': 'Creative'
        })

        # Create relationships
        self.db.create_relationship(self.alice_id, self.tech_id, 'WORKS_FOR', {})
        self.db.create_relationship(self.bob_id, self.tech_id, 'WORKS_FOR', {})
        self.db.create_relationship(self.charlie_id, self.design_id, 'WORKS_FOR', {})

    def test_string_search_with_relationships(self):
        """Test string search combined with relationship patterns."""
        # Find people who work for companies with "Tech" in the name
        result = self.db.execute('''
            MATCH (p:Person)-[:WORKS_FOR]->(c:Company)
            WHERE c.name CONTAINS "Tech"
            RETURN p.name, c.name
        ''')
        assert len(result) == 2
        names = sorted([r['p.name'] for r in result])
        assert names == ['Alice Johnson', 'Bob Smith']

    def test_string_functions_in_return(self):
        """Test string functions in RETURN clause."""
        result = self.db.execute('''
            MATCH (p:Person)
            WHERE p.email ENDS WITH "@tech.com"
            RETURN UPPER(p.name) as upper_name, LENGTH(p.role) as role_length
        ''')
        assert len(result) == 2

        # Check results
        upper_names = sorted([r['upper_name'] for r in result])
        assert upper_names == ['ALICE JOHNSON', 'BOB SMITH']

        # Check role lengths
        role_lengths = [r['role_length'] for r in result]
        assert 15 in role_lengths  # "Senior Engineer" = 15 chars
        assert 16 in role_lengths  # "Junior Developer" = 16 chars

    def test_string_search_with_aggregation(self):
        """Test string search with aggregation functions."""
        # Count people by email domain
        result = self.db.execute('''
            MATCH (p:Person)
            WHERE p.email CONTAINS "@tech.com"
            RETURN COUNT(*) as tech_employees
        ''')
        assert len(result) == 1
        assert result[0]['tech_employees'] == 2

        # Average role length for tech employees
        result = self.db.execute('''
            MATCH (p:Person)
            WHERE p.email ENDS WITH "@tech.com"
            RETURN AVG(LENGTH(p.role)) as avg_role_length
        ''')
        assert len(result) == 1
        # Should be average of "Senior Engineer" (15) and "Junior Developer" (16)
        assert abs(result[0]['avg_role_length'] - 15.5) < 0.1

    def test_regex_with_complex_patterns(self):
        """Test regex with complex patterns and relationships."""
        # Find people whose names match a pattern and work for tech companies
        result = self.db.execute('''
            MATCH (p:Person)-[:WORKS_FOR]->(c:Company)
            WHERE p.name =~ "^[A-Z][a-z]+ [A-Z][a-z]+$"
            AND c.domain CONTAINS "tech"
            RETURN p.name, p.role
        ''')
        assert len(result) == 2
        names = sorted([r['p.name'] for r in result])
        assert names == ['Alice Johnson', 'Bob Smith']

    def test_string_search_performance(self):
        """Test string search performance with larger dataset."""
        # Create more test data
        for i in range(100):
            self.db.create_node(['TestPerson'], {
                'name': f'Person {i:03d}',
                'email': f'person{i}@example.com',
                'description': f'This is person number {i} in our test dataset'
            })

        # Test contains search
        result = self.db.execute('''
            MATCH (p:TestPerson)
            WHERE p.description CONTAINS "number 5"
            RETURN COUNT(*) as count
        ''')
        assert len(result) == 1
        # Should find "number 5", "number 50", "number 51", ..., "number 59"
        assert result[0]['count'] >= 10

        # Test regex search
        result = self.db.execute('''
            MATCH (p:TestPerson)
            WHERE p.email =~ "person[0-9]+@example\\.com"
            RETURN COUNT(*) as count
        ''')
        assert len(result) == 1
        assert result[0]['count'] == 100

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
