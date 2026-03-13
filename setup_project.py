#!/usr/bin/env python3
"""
Project setup script for CreatePay Test Automation Framework.
Creates the necessary directory structure.
"""
import os
import sys


def create_directory_structure():
    """Create the project directory structure."""
    
    # Define directory structure
    directories = [
        "config/env",
        "config/keys",
        "utils",
        "middlewares",
        "api",
        "testcases/generated",
        "testcases/manual",
        "templates",
        "testdata/parsed",
        "testdata/fixtures",
        "reports/allure-results",
        "logs",
        "storage",
    ]
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("Creating directory structure...")
    for directory in directories:
        dir_path = os.path.join(base_dir, directory)
        os.makedirs(dir_path, exist_ok=True)
        print(f"  ✓ Created: {directory}")
    
    print("\n✅ Project structure created successfully!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Configure environment: Edit config/config.yaml")
    print("3. Generate RSA keys: Place keys in config/keys/")
    print("4. Run tests: python run.py")


if __name__ == "__main__":
    try:
        create_directory_structure()
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
