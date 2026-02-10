#!/usr/bin/env python3
"""
Quick diagnostic script to check if the web app is properly configured.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_imports():
    """Check if required modules can be imported."""
    print("Checking Python imports...")
    try:
        import flask
        print("  ✓ Flask")
    except ImportError as e:
        print(f"  ✗ Flask: {e}")
        return False
    
    try:
        import pandas
        print("  ✓ Pandas")
    except ImportError as e:
        print(f"  ✗ Pandas: {e}")
        return False
    
    try:
        import psycopg2
        print("  ✓ psycopg2")
    except ImportError as e:
        print(f"  ✗ psycopg2: {e}")
        return False
    
    return True

def check_config():
    """Check if configuration is set up."""
    print("\nChecking configuration...")
    try:
        from config import DB_CONFIG
        print(f"  ✓ Config loaded")
        print(f"    Database: {DB_CONFIG.get('database', 'N/A')}")
        print(f"    Host: {DB_CONFIG.get('host', 'N/A')}")
        print(f"    User: {DB_CONFIG.get('user', 'N/A')}")
        return True
    except Exception as e:
        print(f"  ✗ Config error: {e}")
        return False

def check_database():
    """Check database connection."""
    print("\nChecking database connection...")
    try:
        from database.db_manager import DatabaseManager
        from config import DB_CONFIG
        
        db = DatabaseManager(DB_CONFIG)
        # Test query
        result = db.execute_query("SELECT 1 as test", None, fetch=True)
        print("  ✓ Database connection successful")
        db.close_all_connections()
        return True
    except Exception as e:
        print(f"  ✗ Database connection failed: {e}")
        print("    Check your database configuration in config.py")
        return False

def check_web_modules():
    """Check if web modules can be imported."""
    print("\nChecking web modules...")
    try:
        from web.nl_to_sql import NLToSQLConverter
        print("  ✓ NL to SQL converter")
    except Exception as e:
        print(f"  ✗ NL to SQL converter: {e}")
        return False
    
    try:
        from web.sql_validator import SQLValidator
        print("  ✓ SQL validator")
    except Exception as e:
        print(f"  ✗ SQL validator: {e}")
        return False
    
    try:
        from web.code_generator import CodeGenerator
        print("  ✓ Code generator")
    except Exception as e:
        print(f"  ✗ Code generator: {e}")
        return False
    
    return True

def main():
    print("=" * 50)
    print("Web App Setup Diagnostic")
    print("=" * 50)
    
    results = []
    results.append(("Imports", check_imports()))
    results.append(("Configuration", check_config()))
    results.append(("Database", check_database()))
    results.append(("Web Modules", check_web_modules()))
    
    print("\n" + "=" * 50)
    print("Summary:")
    print("=" * 50)
    
    all_ok = True
    for name, status in results:
        status_symbol = "✓" if status else "✗"
        print(f"{status_symbol} {name}")
        if not status:
            all_ok = False
    
    print("\n" + "=" * 50)
    if all_ok:
        print("✓ All checks passed! You can start the server with:")
        print("  python -m web.app")
        print("  or")
        print("  ./run_web_app.sh")
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Check database configuration in config.py")
        print("  3. Ensure PostgreSQL is running")
    print("=" * 50)
    
    return 0 if all_ok else 1

if __name__ == '__main__':
    sys.exit(main())


