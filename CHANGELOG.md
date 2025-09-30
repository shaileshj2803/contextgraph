# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.1] - 2024-09-30

### Performance Improvements
- **MAJOR LOADING OPTIMIZATION**: Optimized `load_pickle()` and `load()` (JSON) with batch operations
- **Batch Vertex Creation**: Replace O(n) individual `add_vertex()` calls with single `add_vertices(n)` call
- **Batch Edge Creation**: Replace O(n) individual `add_edge()` calls with single `add_edges()` call  
- **Batch Attribute Assignment**: Optimized property setting with batch operations
- **Transaction Rollback**: Applied same batch optimizations to transaction restoration

### Performance Results
- JSON loading: 400,000+ nodes/second (massive improvement from batch operations)
- Pickle loading: 700,000+ nodes/second (1.8x faster than JSON)
- Total throughput: 1,173,000+ elements/second
- Transaction rollback: 980,000+ elements/second
- Large graphs (3,000 nodes) now load in 4 milliseconds instead of seconds

### Added
- Comprehensive loading performance test suite
- Loading performance demonstration example
- Regression prevention tests for loading scalability

## [0.3.0] - 2024-09-30

### Added
- **MAJOR PERFORMANCE IMPROVEMENTS**: Optimized `create_relationship` API with O(1) node lookup
- **NEW FEATURE**: Optional `nodeid` parameter in `create_node()` for custom node ID assignment
- **NEW API**: `create_relationships_batch()` for high-performance bulk relationship creation
- Performance benchmarks and comprehensive examples

### Changed
- **BREAKING PERFORMANCE**: `create_relationship` now uses O(1) hash map lookup instead of O(n) linear search
- Node lookup performance improved to 1,000,000+ lookups/second
- Batch relationship creation is 5-8x faster than individual creation
- Enhanced CSV import performance with optimized relationship creation

### Performance Results
- Node creation: 300,000+ nodes/second
- Individual relationships: 55,000+ relationships/second  
- Batch relationships: 480,000+ relationships/second (8.8x speedup)
- Node lookups: 1,000,000+ lookups/second (massive O(1) improvement)

## [0.2.0] - 2024-12-XX

### Changed
- **BREAKING**: License changed from Apache 2.0 to MIT License
- This is a minor version bump due to the significant license change

## [0.1.2] - 2024-12-XX

### Changed
- Updated to MIT License for better compatibility
- Fixed packaging and version management

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

