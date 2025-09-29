# Contributing to ContextGraph

Thank you for your interest in contributing to ContextGraph! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/contextgraph.git
   cd contextgraph
   ```

2. **Set up development environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .[dev]
   ```

3. **Install pre-commit hooks** (optional but recommended)
   ```bash
   pre-commit install
   ```

### Development Dependencies

The development environment includes:
- **Testing**: pytest, pytest-cov
- **Code Quality**: flake8, black, mypy
- **Visualization**: matplotlib, networkx, plotly, graphviz
- **Documentation**: sphinx, sphinx-rtd-theme
- **Build Tools**: build, twine

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=igraph_cypher_db --cov-report=html

# Run specific test categories
pytest -m "not slow"  # Skip slow tests
pytest tests/test_cypher.py  # Specific test file
pytest -k "test_visualization"  # Tests matching pattern
```

### Writing Tests

- Place tests in the `tests/` directory
- Use descriptive test names: `test_cypher_query_with_where_clause`
- Include both positive and negative test cases
- Test edge cases and error conditions
- Add integration tests for complex features

Example test structure:
```python
class TestNewFeature:
    def setup_method(self):
        """Set up test fixtures."""
        self.db = GraphDB()
        # ... setup code
    
    def test_basic_functionality(self):
        """Test basic feature functionality."""
        # Arrange
        # Act
        # Assert
        
    def test_error_handling(self):
        """Test error conditions."""
        with pytest.raises(ExpectedError):
            # Test error condition
```

## 🎨 Code Style

### Formatting

We use [Black](https://black.readthedocs.io/) for code formatting:
```bash
black igraph_cypher_db tests examples
```

### Linting

We use [flake8](https://flake8.pycqa.org/) for linting:
```bash
flake8 igraph_cypher_db tests examples
```

### Type Checking

We use [mypy](https://mypy.readthedocs.io/) for type checking:
```bash
mypy igraph_cypher_db
```

### Code Style Guidelines

- **Line Length**: 88 characters (Black default)
- **Imports**: Use absolute imports, group by standard/third-party/local
- **Docstrings**: Use Google-style docstrings
- **Type Hints**: Include type hints for all public APIs
- **Variable Names**: Use descriptive names, avoid abbreviations

## 📝 Documentation

### Docstring Format

Use Google-style docstrings:
```python
def create_node(self, labels: List[str], properties: Dict[str, Any]) -> int:
    """Create a new node in the graph.
    
    Args:
        labels: List of labels to assign to the node
        properties: Dictionary of properties for the node
        
    Returns:
        The ID of the created node
        
    Raises:
        GraphDBError: If node creation fails
        
    Example:
        >>> db = GraphDB()
        >>> node_id = db.create_node(['Person'], {'name': 'Alice'})
    """
```

### README Updates

When adding new features:
1. Update the feature list in README.md
2. Add usage examples
3. Update the roadmap if applicable

## 🐛 Bug Reports

### Before Submitting

1. **Search existing issues** to avoid duplicates
2. **Test with the latest version**
3. **Create a minimal reproduction case**

### Bug Report Template

```markdown
**Bug Description**
A clear description of the bug.

**Reproduction Steps**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**
- OS: [e.g., Ubuntu 20.04]
- Python version: [e.g., 3.9.7]
- contextgraph version: [e.g., 0.1.0]
- Dependencies: [relevant package versions]

**Additional Context**
Any other relevant information.
```

## ✨ Feature Requests

### Before Submitting

1. **Check the roadmap** in README.md
2. **Search existing issues** for similar requests
3. **Consider the scope** - does it fit the project goals?

### Feature Request Template

```markdown
**Feature Description**
A clear description of the proposed feature.

**Use Case**
Describe the problem this feature would solve.

**Proposed Solution**
Your ideas for how this could be implemented.

**Alternatives Considered**
Other approaches you've considered.

**Additional Context**
Any other relevant information.
```

## 🔄 Pull Requests

### Before Submitting

1. **Create an issue** to discuss major changes
2. **Fork the repository** and create a feature branch
3. **Write tests** for new functionality
4. **Update documentation** as needed
5. **Run the full test suite**

### PR Guidelines

- **Branch naming**: `feature/description` or `fix/description`
- **Commit messages**: Use clear, descriptive messages
- **Small PRs**: Keep changes focused and reviewable
- **Tests required**: All new code must have tests
- **Documentation**: Update docs for user-facing changes

### PR Template

```markdown
**Description**
Brief description of changes.

**Type of Change**
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

**Testing**
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Manual testing performed

**Checklist**
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
```

## 🏗️ Architecture Guidelines

### Code Organization

```
igraph_cypher_db/
├── __init__.py          # Public API exports
├── graphdb.py           # Main GraphDB class
├── cypher_parser.py     # Cypher query parsing
├── query_result.py      # Query result handling
├── transaction.py       # Transaction management
├── csv_importer.py      # CSV import functionality
├── visualization.py     # Graph visualization
└── exceptions.py        # Custom exceptions
```

### Design Principles

1. **Separation of Concerns**: Each module has a clear responsibility
2. **Dependency Injection**: Avoid tight coupling between components
3. **Error Handling**: Comprehensive error handling with custom exceptions
4. **Performance**: Optimize for common use cases
5. **Extensibility**: Design for future enhancements

### Adding New Features

1. **Core Features**: Add to appropriate existing modules
2. **New Modules**: Create new modules for distinct functionality
3. **Public API**: Export new public APIs in `__init__.py`
4. **Backward Compatibility**: Maintain API compatibility when possible

## 🔧 Development Workflow

### Typical Workflow

1. **Create Issue**: Discuss the change
2. **Fork & Branch**: Create a feature branch
3. **Develop**: Write code and tests
4. **Test**: Run full test suite
5. **Document**: Update documentation
6. **Submit PR**: Create pull request
7. **Review**: Address feedback
8. **Merge**: Maintainer merges PR

### Release Process

1. **Version Bump**: Update version in `__init__.py` and `setup.py`
2. **Changelog**: Update CHANGELOG.md
3. **Tag Release**: Create GitHub release
4. **PyPI**: Automatic publication via GitHub Actions

## 🤝 Community

### Code of Conduct

Be respectful, inclusive, and constructive in all interactions.

### Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check README and code documentation

### Recognition

Contributors are recognized in:
- GitHub contributors list
- Release notes for significant contributions
- Special thanks in documentation

## 📚 Resources

- **Python Packaging**: [Python Packaging Guide](https://packaging.python.org/)
- **Testing**: [pytest documentation](https://docs.pytest.org/)
- **Type Hints**: [mypy documentation](https://mypy.readthedocs.io/)
- **igraph**: [igraph documentation](https://igraph.org/python/)
- **Cypher**: [Cypher Query Language](https://neo4j.com/developer/cypher/)

Thank you for contributing to contextgraph! 🚀
