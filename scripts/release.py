#!/usr/bin/env python3
"""
Release script for ContextGraph

This script helps automate the release process:
1. Run tests
2. Build package
3. Check package
4. Upload to PyPI (test or production)
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_command(cmd, check=True):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        print(f"Command failed: {cmd}")
        print(f"Error: {result.stderr}")
        sys.exit(1)
    
    return result


def run_tests():
    """Run the test suite."""
    print("🧪 Running tests...")
    run_command("python -m pytest tests/ --cov=contextgraph")
    print("✅ Tests passed!")


def check_code_quality():
    """Run code quality checks."""
    print("🔍 Checking code quality...")
    
    # Linting
    run_command("flake8 contextgraph tests --count --select=E9,F63,F7,F82 --show-source --statistics")
    
    # Type checking
    run_command("mypy contextgraph --ignore-missing-imports")
    
    print("✅ Code quality checks passed!")


def clean_build():
    """Clean previous build artifacts."""
    print("🧹 Cleaning build artifacts...")
    run_command("rm -rf build/ dist/ *.egg-info/", check=False)
    print("✅ Build artifacts cleaned!")


def build_package():
    """Build the package."""
    print("📦 Building package...")
    run_command("python -m build")
    print("✅ Package built!")


def check_package():
    """Check the built package."""
    print("🔍 Checking package...")
    run_command("twine check dist/*")
    print("✅ Package check passed!")


def upload_to_test_pypi():
    """Upload to Test PyPI."""
    print("🚀 Uploading to Test PyPI...")
    run_command("twine upload --repository testpypi dist/*")
    print("✅ Uploaded to Test PyPI!")


def upload_to_pypi():
    """Upload to PyPI."""
    print("🚀 Uploading to PyPI...")
    run_command("twine upload dist/*")
    print("✅ Uploaded to PyPI!")


def main():
    parser = argparse.ArgumentParser(description="Release script for ContextGraph")
    parser.add_argument("--test", action="store_true", help="Upload to Test PyPI instead of PyPI")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")
    parser.add_argument("--skip-quality", action="store_true", help="Skip code quality checks")
    parser.add_argument("--build-only", action="store_true", help="Only build, don't upload")
    
    args = parser.parse_args()
    
    print("🚀 Starting release process for ContextGraph")
    
    # Change to project directory
    project_dir = Path(__file__).parent.parent
    import os
    os.chdir(project_dir)
    
    try:
        # Run tests
        if not args.skip_tests:
            run_tests()
        
        # Check code quality
        if not args.skip_quality:
            check_code_quality()
        
        # Clean and build
        clean_build()
        build_package()
        check_package()
        
        if not args.build_only:
            # Upload
            if args.test:
                upload_to_test_pypi()
                print("🎉 Successfully released to Test PyPI!")
                print("Install with: pip install --index-url https://test.pypi.org/simple/ contextgraph")
            else:
                # Confirm before uploading to production PyPI
                confirm = input("Are you sure you want to upload to PyPI? (yes/no): ")
                if confirm.lower() == 'yes':
                    upload_to_pypi()
                    print("🎉 Successfully released to PyPI!")
                    print("Install with: pip install contextgraph")
                else:
                    print("❌ Upload cancelled")
        else:
            print("📦 Package built successfully!")
            print("To upload manually:")
            print("  Test PyPI: twine upload --repository testpypi dist/*")
            print("  PyPI: twine upload dist/*")
    
    except KeyboardInterrupt:
        print("\n❌ Release process interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Release process failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
