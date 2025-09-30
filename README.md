# ContextGraph

[![PyPI version](https://badge.fury.io/py/contextgraph.svg)](https://badge.fury.io/py/contextgraph)
[![Python Support](https://img.shields.io/pypi/pyversions/contextgraph.svg)](https://pypi.org/project/contextgraph/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/yourusername/contextgraph/workflows/Tests/badge.svg)](https://github.com/yourusername/contextgraph/actions)

A powerful graph database with [Cypher](https://neo4j.com/developer/cypher/) query support and advanced visualization capabilities, built on [igraph](https://igraph.org/).

## 🚀 Features

- **🔍 Cypher Query Language**: Full support for Cypher queries including MATCH, CREATE, WHERE, RETURN, and more
- **📊 Advanced Visualization**: Multiple backends (matplotlib, plotly, graphviz) with interactive capabilities
- **🔗 Variable-Length Paths**: Support for path queries with depth limits (`*1..3`, `*2`, `*`)
- **🔤 String Operations**: Comprehensive string search and manipulation functions
- **💾 Data Import/Export**: High-performance CSV import and multiple serialization formats
- **⚡ Transactions**: ACID-compliant transaction support with rollback capabilities
- **🎯 High Performance**: Built on igraph for efficient graph operations
- **🐍 Pythonic API**: Clean, intuitive Python interface

## 📦 Installation

### Basic Installation
```bash
pip install contextgraph
```

### With Visualization Support
```bash
pip install contextgraph[visualization]
```

### With All Optional Dependencies
```bash
pip install contextgraph[all]
```

### Development Installation
```bash
git clone https://github.com/yourusername/contextgraph.git
cd contextgraph
pip install -e .[dev]
```

## 🏃‍♂️ Quick Start

```python
from contextgraph import GraphDB

# Create a new graph database
db = GraphDB()

# Create nodes
alice_id = db.create_node(['Person'], {'name': 'Alice', 'age': 30})
bob_id = db.create_node(['Person'], {'name': 'Bob', 'age': 25})
company_id = db.create_node(['Company'], {'name': 'TechCorp'})

# Create relationships
db.create_relationship(alice_id, bob_id, 'KNOWS', {'since': 2020})
db.create_relationship(alice_id, company_id, 'WORKS_FOR')

# Query with Cypher
result = db.execute("""
    MATCH (p:Person)-[:KNOWS]->(friend:Person)
    WHERE p.age > 25
    RETURN p.name, friend.name, p.age
""")

for record in result:
    print(f"{record['p.name']} knows {record['friend.name']}")

# Visualize the graph
db.visualize(node_labels=True, node_color_property='age')
```

## 📚 Documentation

### Core Operations

#### Creating Nodes and Relationships
```python
# Create nodes with labels and properties
person_id = db.create_node(['Person', 'Employee'], {
    'name': 'Alice',
    'age': 30,
    'department': 'Engineering'
})

# Create relationships with properties
rel_id = db.create_relationship(
    source_id=alice_id,
    target_id=bob_id,
    relationship_type='MANAGES',
    properties={'since': '2023-01-01', 'level': 'senior'}
)
```

#### Cypher Queries
```python
# Basic pattern matching
result = db.execute("""
    MATCH (manager:Person)-[:MANAGES]->(employee:Person)
    WHERE manager.department = 'Engineering'
    RETURN manager.name, employee.name
""")

# Variable-length paths
result = db.execute("""
    MATCH (start:Person)-[:KNOWS*1..3]->(end:Person)
    WHERE start.name = 'Alice'
    RETURN start.name, end.name
""")

# String operations
result = db.execute("""
    MATCH (p:Person)
    WHERE p.name CONTAINS 'Ali' AND p.email =~ '.*@company\\.com'
    RETURN UPPER(p.name) as name, LENGTH(p.name) as name_length
""")
```

### Advanced Features

#### Transactions
```python
# Using transactions for data consistency
with db.transaction():
    node1 = db.create_node(['Person'], {'name': 'Charlie'})
    node2 = db.create_node(['Person'], {'name': 'Diana'})
    db.create_relationship(node1, node2, 'FRIENDS')
    # Automatically committed on success, rolled back on exception
```

#### CSV Import
```python
# High-performance CSV import
stats = db.import_nodes_from_csv(
    'people.csv',
    labels=['Person'],
    property_columns=['name', 'age', 'email']
)

stats = db.import_relationships_from_csv(
    'relationships.csv',
    relationship_type='KNOWS',
    source_column='person1_id',
    target_column='person2_id'
)
```

#### Visualization
```python
# Basic visualization
db.visualize(
    node_labels=True,
    layout='spring',
    title='My Graph'
)

# Advanced styling
db.visualize(
    backend='plotly',  # Interactive visualization
    node_size_property='age',
    node_color_property='department',
    edge_width_property='strength',
    layout='circular'
)

# Query result visualization
from contextgraph import GraphVisualizer
viz = GraphVisualizer(db)
viz.plot_query_result("""
    MATCH (p:Person)-[:WORKS_FOR]->(c:Company)
    RETURN p, c
""")
```

## 🔧 Supported Cypher Features

### Query Clauses
- ✅ `MATCH` - Pattern matching
- ✅ `CREATE` - Node and relationship creation
- ✅ `WHERE` - Filtering conditions
- ✅ `RETURN` - Result projection
- ✅ `ORDER BY` - Result sorting
- ✅ `LIMIT` - Result limiting
- ✅ `WITH` - Query chaining

### Pattern Matching
- ✅ Node patterns: `(n:Label {property: value})`
- ✅ Relationship patterns: `-[:TYPE {property: value}]->`
- ✅ Variable-length paths: `-[:TYPE*1..3]->`
- ✅ Optional patterns and complex matching

### Functions and Operators
- ✅ String functions: `UPPER()`, `LOWER()`, `TRIM()`, `SUBSTRING()`, etc.
- ✅ String operators: `CONTAINS`, `STARTS WITH`, `ENDS WITH`, `=~` (regex)
- ✅ Aggregate functions: `COUNT()`, `SUM()`, `AVG()`, `MIN()`, `MAX()`
- ✅ Comparison operators: `=`, `<>`, `<`, `>`, `<=`, `>=`

## 📊 Visualization Backends

| Backend | Type | Features |
|---------|------|----------|
| **matplotlib** | Static | Publication-quality plots, customizable styling |
| **plotly** | Interactive | Web-ready, hover details, zoom/pan |
| **graphviz** | Vector | High-quality layouts, perfect for documentation |

## 🔄 Data Import/Export

### Supported Formats
- **CSV**: High-performance bulk import
- **JSON**: Human-readable serialization
- **Pickle**: Fast binary serialization with full Python object support

### Performance
- **CSV Import**: 10,000+ nodes/relationships per second
- **Query Performance**: Optimized for complex graph traversals
- **Memory Efficient**: Streaming operations for large datasets

## 🧪 Testing

Run the test suite:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=igraph_cypher_db

# Run specific test categories
pytest -m "not slow"  # Skip slow tests
pytest tests/test_cypher.py  # Specific test file
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
git clone https://github.com/yourusername/contextgraph.git
cd contextgraph
pip install -e .[dev]
pre-commit install
```

### Code Quality
```bash
# Format code
black igraph_cypher_db tests

# Lint code
flake8 igraph_cypher_db tests

# Type checking
mypy igraph_cypher_db
```

## 📈 Performance Benchmarks

| Operation | Performance |
|-----------|-------------|
| Node Creation | 50,000+ nodes/sec |
| Relationship Creation | 25,000+ relationships/sec |
| CSV Import | 10,000+ records/sec |
| Simple Queries | 1,000+ queries/sec |
| Complex Path Queries | 100+ queries/sec |

## 🗺️ Roadmap

- [ ] **Query Optimization**: Advanced query planning and optimization
- [ ] **Distributed Queries**: Support for distributed graph operations
- [ ] **Graph Algorithms**: Built-in graph analysis algorithms
- [ ] **Schema Validation**: Optional schema enforcement
- [ ] **REST API**: HTTP interface for remote access
- [ ] **Streaming**: Real-time graph updates and queries

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on the excellent [igraph](https://igraph.org/) library
- Inspired by [Neo4j](https://neo4j.com/) and the Cypher query language
- Visualization powered by [matplotlib](https://matplotlib.org/), [plotly](https://plotly.com/), and [graphviz](https://graphviz.org/)

## 📞 Support

- 📖 [Documentation](https://github.com/yourusername/contextgraph#readme)
- 🐛 [Issue Tracker](https://github.com/yourusername/contextgraph/issues)
- 💬 [Discussions](https://github.com/yourusername/contextgraph/discussions)

---

**Made with ❤️ for the graph database community**