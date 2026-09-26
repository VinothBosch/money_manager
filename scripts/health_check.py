#!/usr/bin/env python3
"""
Quick Health Check Script
Run this before processing to ensure everything is ready
"""

import sys
import subprocess
from pathlib import Path

def quick_check():
    """Quick health check"""
    print("🔍 Quick Health Check\n")
    
    issues = []
    
    # Check Python
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    else:
        print(f"✗ Python {version.major}.{version.minor} (need 3.8+)")
        issues.append("Python version too old")
    
    # Check key dependencies
    deps = ['pandas', 'semantic_kernel', 'openpyxl', 'xlrd', 'xlwt', 'dotenv', 'openai']
    for dep in deps:
        try:
            __import__(dep if dep != 'dotenv' else 'dotenv')
            print(f"✓ {dep}")
        except ImportError:
            print(f"✗ {dep}")
            issues.append(f"Missing: {dep}")
    
    # Check files
    files = ['scripts/main.py', 'money_manager/config.py', 'money_manager/data_extractor.py',
             'money_manager/categorizer.py', 'money_manager/excel_exporter.py', '.env']
    for file in files:
        if Path(file).exists():
            print(f"✓ {file}")
        else:
            print(f"✗ {file}")
            if file == '.env':
                issues.append("Run: python scripts/setup.py")
            else:
                issues.append(f"Missing: {file}")
    
    # Check input files
    inputs = ['data/input/AccountStatement_edited.xlsx', 'data/input/01-01-25_31-12-25.xls']
    for inp in inputs:
        if Path(inp).exists():
            print(f"✓ {inp}")
        else:
            print(f"⚠ {inp} (needed for processing)")
    
    print()
    if issues:
        print("❌ Issues found:")
        for issue in issues:
            print(f"   - {issue}")
        print("\nFix with:")
        print("   pip install -r requirements.txt")
        print("   python setup.py")
        return False
    else:
        print("✅ All good! Ready to run:")
        print("   python scripts/main.py")
        return True

if __name__ == "__main__":
    success = quick_check()
    sys.exit(0 if success else 1)
