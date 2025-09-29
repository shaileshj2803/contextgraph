# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2024-12-XX

### Added
- Initial release of ContextGraph
- Core graph database functionality with igraph backend
- Comprehensive Cypher query language support
- Advanced visualization capabilities with multiple backends
- Variable-length path queries with depth limits
- String search and manipulation functions
- High-performance CSV import/export
- ACID-compliant transaction support
- Multiple serialization formats (JSON, Pickle)
- Comprehensive test suite with 187+ tests
- Full documentation and examples

### Features
#### Core Database
- Node and relationship creation with labels and properties
- Cypher query parser and executor using pyparsing
- Pattern matching with complex WHERE clauses
- Aggregate functions (COUNT, SUM, AVG, MIN, MAX)
- Query result iteration and indexing
- Transaction management with rollback support

#### Cypher Language Support
- **Query Clauses**: MATCH, CREATE, WHERE, RETURN, ORDER BY, LIMIT, WITH
- **Pattern Matching**: Node patterns, relationship patterns, variable-length paths
- **String Functions**: UPPER, LOWER, TRIM, LTRIM, RTRIM, LENGTH, SUBSTRING, REPLACE, SPLIT, REVERSE
- **String Operators**: CONTAINS, STARTS WITH, ENDS WITH, =~ (regex)
- **Variable-Length Paths**: Support for *n, *min..max, and * syntax
- **Comparison Operators**: =, <>, <, >, <=, >=

#### Visualization
- **Multiple Backends**: matplotlib (static), plotly (interactive), graphviz (vector)
- **Layout Algorithms**: spring, circular, random, shell, kamada_kawai, hierarchical
- **Property-Based Styling**: Node size, color, and edge width based on data properties
- **Interactive Features**: Hover details, pan, zoom, drag nodes
- **Export Formats**: PNG, SVG, HTML, and more
- **Query Result Visualization**: Visualize subgraphs from Cypher queries
- **Path Visualization**: Highlight paths between specific nodes

#### Data Import/Export
- **CSV Import**: High-performance bulk import with batch processing
- **JSON Serialization**: Human-readable graph export/import
- **Pickle Serialization**: Fast binary serialization with full Python object support
- **Streaming Operations**: Memory-efficient handling of large datasets

#### Performance & Quality
- **High Performance**: 50,000+ nodes/sec, 25,000+ relationships/sec
- **Memory Efficient**: Optimized for large graphs
- **Comprehensive Testing**: 187+ tests covering all functionality
- **Type Safety**: Full type hints throughout codebase
- **Error Handling**: Robust exception handling and validation

### Dependencies
- **Core**: igraph>=0.10.0, pyparsing>=3.0.0
- **Visualization** (optional): matplotlib>=3.5.0, networkx>=2.6.0, plotly>=5.0.0
- **Graphviz** (optional): graphviz>=0.19.0
- **Development**: pytest, flake8, black, mypy

### Documentation
- Comprehensive README with examples
- Full API documentation
- Multiple example scripts demonstrating features
- Installation and development guides
- Performance benchmarks and roadmap

### Notes
- First stable release of ContextGraph ready for production use
- MIT licensed for maximum compatibility
- Python 3.8+ support
- Cross-platform compatibility (Windows, macOS, Linux)

