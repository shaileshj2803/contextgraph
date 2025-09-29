# Release Guide for ContextGraph

This guide walks you through the complete process of releasing ContextGraph to GitHub and PyPI.

## 📋 Prerequisites

### 1. Update Personal Information

Before releasing, update the following files with your information:

**setup.py**:
```python
author="Your Name",  # Replace with your name
author_email="your.email@example.com",  # Replace with your email
url="https://github.com/yourusername/contextgraph",  # Replace with your GitHub URL
```

**pyproject.toml**:
```toml
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
```

**LICENSE**:
```
Copyright (c) 2024 Your Name
```

**All GitHub URLs** in README.md, setup.py, pyproject.toml should point to your repository.

### 2. Required Accounts

- **GitHub Account**: For hosting the repository
- **PyPI Account**: For publishing packages (https://pypi.org/account/register/)
- **Test PyPI Account**: For testing releases (https://test.pypi.org/account/register/)

### 3. Install Required Tools

```bash
pip install build twine
```

## 🚀 Step-by-Step Release Process

### Step 1: Prepare Your GitHub Repository

1. **Create a new private repository** on GitHub:
   ```
   Repository name: contextgraph
   Description: A powerful graph database with Cypher query support and advanced visualization capabilities
   Private: ✅ (initially)
   ```

2. **Initialize and push your code**:
   ```bash
   cd /Users/sjannu/igraph_cypher_db
   git init
   git add .
   git commit -m "Initial commit: contextgraph v0.1.0"
   git branch -M main
   git remote add origin https://github.com/yourusername/contextgraph.git
   git push -u origin main
   ```

### Step 2: Set Up PyPI API Tokens

1. **Create PyPI API Token**:
   - Go to https://pypi.org/manage/account/token/
   - Create a new API token with scope "Entire account"
   - Copy the token (starts with `pypi-`)

2. **Create Test PyPI API Token**:
   - Go to https://test.pypi.org/manage/account/token/
   - Create a new API token
   - Copy the token

3. **Add tokens to GitHub Secrets**:
   - Go to your GitHub repository
   - Settings → Secrets and variables → Actions
   - Add new repository secrets:
     - `PYPI_API_TOKEN`: Your PyPI token
     - `TEST_PYPI_API_TOKEN`: Your Test PyPI token

### Step 3: Test the Package Locally

```bash
# Run tests
python -m pytest tests/ --cov=igraph_cypher_db

# Check code quality
flake8 igraph_cypher_db tests
mypy igraph_cypher_db --ignore-missing-imports

# Build package
python -m build

# Check package
twine check dist/*
```

### Step 4: Test Release to Test PyPI

```bash
# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Test installation from Test PyPI
pip install --index-url https://test.pypi.org/simple/ contextgraph

# Test the installed package
python -c "from igraph_cypher_db import GraphDB; print('✅ Package works!')"
```

### Step 5: Release to PyPI

#### Option A: Using the Release Script
```bash
# Test release
python scripts/release.py --test

# Production release
python scripts/release.py
```

#### Option B: Manual Release
```bash
# Clean and build
rm -rf build/ dist/ *.egg-info/
python -m build
twine check dist/*

# Upload to PyPI
twine upload dist/*
```

### Step 6: Create GitHub Release

1. **Go to your GitHub repository**
2. **Click "Releases" → "Create a new release"**
3. **Fill in the release information**:
   ```
   Tag version: v0.1.0
   Release title: contextgraph v0.1.0
   Description: [Copy from CHANGELOG.md]
   ```
4. **Attach the built distributions** (optional):
   - Upload `dist/*.tar.gz` and `dist/*.whl` files

### Step 7: Make Repository Public

1. **Go to repository Settings**
2. **Scroll to "Danger Zone"**
3. **Click "Change repository visibility"**
4. **Select "Make public"**

## 🔧 Configuration Files Created

Here's what we've set up for you:

### Package Configuration
- ✅ `setup.py` - Package setup script
- ✅ `pyproject.toml` - Modern Python packaging configuration
- ✅ `requirements.txt` - Core dependencies
- ✅ `requirements-dev.txt` - Development dependencies
- ✅ `MANIFEST.in` - Package file inclusion rules

### Documentation
- ✅ `README.md` - Comprehensive project documentation
- ✅ `CHANGELOG.md` - Version history
- ✅ `CONTRIBUTING.md` - Contributor guidelines
- ✅ `LICENSE` - MIT license

### GitHub Configuration
- ✅ `.github/workflows/tests.yml` - CI/CD for testing
- ✅ `.github/workflows/publish.yml` - Automatic PyPI publishing
- ✅ `.gitignore` - Git ignore rules

### Development Tools
- ✅ `scripts/release.py` - Automated release script
- ✅ `igraph_cypher_db/py.typed` - Type checking support

## 📦 Package Features

Your package will be installable with:

```bash
# Basic installation
pip install contextgraph

# With visualization support
pip install contextgraph[visualization]

# With all optional features
pip install contextgraph[all]

# Development installation
pip install contextgraph[dev]
```

## 🔄 Updating After Release

### For Bug Fixes (Patch Version: 0.1.0 → 0.1.1)
1. Fix the bug
2. Update version in `igraph_cypher_db/__init__.py`
3. Update `CHANGELOG.md`
4. Commit and push
5. Create new release

### For New Features (Minor Version: 0.1.0 → 0.2.0)
1. Develop feature
2. Add tests and documentation
3. Update version numbers
4. Update `CHANGELOG.md`
5. Create new release

### For Breaking Changes (Major Version: 0.1.0 → 1.0.0)
1. Implement changes
2. Update documentation thoroughly
3. Update version numbers
4. Update `CHANGELOG.md` with migration guide
5. Create new release

## 🎯 Post-Release Checklist

After successful release:

- [ ] Verify package is available on PyPI
- [ ] Test installation: `pip install contextgraph`
- [ ] Update any external documentation
- [ ] Announce the release (social media, forums, etc.)
- [ ] Monitor for issues and feedback

## 🆘 Troubleshooting

### Common Issues

**Build Fails**:
```bash
# Clean everything and retry
rm -rf build/ dist/ *.egg-info/
pip install --upgrade build setuptools wheel
python -m build
```

**Upload Fails**:
```bash
# Check credentials
twine check dist/*
# Verify API token is correct
```

**Tests Fail on GitHub Actions**:
- Check that all dependencies are properly specified
- Ensure tests don't depend on local files
- Verify cross-platform compatibility

### Getting Help

- **GitHub Issues**: Create an issue in your repository
- **PyPI Help**: https://pypi.org/help/
- **Python Packaging**: https://packaging.python.org/

## 🎉 Congratulations!

Once you complete these steps, you'll have:

- ✅ A professional open-source Python package
- ✅ Automated testing and deployment
- ✅ Comprehensive documentation
- ✅ A package available on PyPI
- ✅ A public GitHub repository

Your contextgraph package will be ready for the community to discover and use! 🚀
