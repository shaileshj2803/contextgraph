#!/usr/bin/env python3
"""
Setup script for ContextGraph
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

# Read the requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="contextgraph",
    version="0.3.0",
    author="Shailesh Jannu",  # Replace with your name
    author_email="shaileshj@gmail.com",  # Replace with your email
    description="A powerful graph database with Cypher query support and advanced visualization capabilities",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/shaileshj2803/contextgraph",
    license="MIT",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Database",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "visualization": [
            "matplotlib>=3.5.0",
            "networkx>=2.6.0",
            "plotly>=5.0.0",
        ],
        "graphviz": [
            "graphviz>=0.19.0",
        ],
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.10.0",
            "flake8>=3.8.0",
            "black>=21.0.0",
            "mypy>=0.800",
        ],
        "all": [
            "matplotlib>=3.5.0",
            "networkx>=2.6.0",
            "plotly>=5.0.0",
            "graphviz>=0.19.0",
        ],
    },
    entry_points={
        "console_scripts": [
            # Add any command-line tools here if needed
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="graph database cypher context visualization networkx",
    project_urls={
        "Bug Reports": "https://github.com/shaileshj2803/contextgraph/issues",
        "Source": "https://github.com/shaileshj2803/contextgraph",
        "Documentation": "https://github.com/shaileshj2803/contextgraph#readme",
    },
)