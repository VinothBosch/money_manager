"""
Setup Validation Script
Validates all dependencies, files, and configuration before running
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"  ✗ Python {version.major}.{version.minor} detected")
        print(f"  ✓ Required: Python 3.8 or higher")
        return False
    print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Check if all required packages are installed"""
    print("\nChecking dependencies...")
    required_packages = {
        'pandas': 'pandas',
        'openpyxl': 'openpyxl',
        'xlrd': 'xlrd',
        'xlwt': 'xlwt',
        'semantic_kernel': 'semantic-kernel',
        'dotenv': 'python-dotenv',
        'openai': 'openai'
    }
    
    all_installed = True
    for module_name, package_name in required_packages.items():
        try:
            __import__(module_name)
            print(f"  ✓ {package_name}")
        except ImportError:
            print(f"  ✗ {package_name} - NOT INSTALLED")
            all_installed = False
    
    if not all_installed:
        print("\nInstall missing packages with:")
        print("  pip install -r requirements.txt")
    
    return all_installed

def check_files():
    """Check if all required files exist"""
    print("\nChecking required files...")
    required_files = [
        'scripts/main.py',
        'money_manager/config.py',
        'money_manager/data_extractor.py',
        'money_manager/categorizer.py',
        'money_manager/excel_exporter.py',
        'requirements.txt',
        '.env.example'
    ]
    
    all_exist = True
    for filename in required_files:
        if Path(filename).exists():
            print(f"  ✓ {filename}")
        else:
            print(f"  ✗ {filename} - MISSING")
            all_exist = False
    
    return all_exist

def check_input_files():
    """Check if input data files exist"""
    print("\nChecking input data files...")
    input_files = [
        'data/input/AccountStatement_edited.xlsx',
        'data/input/01-01-25_31-12-25.xls'
    ]
    
    all_exist = True
    for filename in input_files:
        if Path(filename).exists():
            print(f"  ✓ {filename}")
        else:
            print(f"  ✗ {filename} - MISSING")
            all_exist = False
    
    if not all_exist:
        print("\n  Note: Input files are required to run the processor")
        print("  Make sure you have:")
        print("    - AccountStatement_edited.xlsx (your bank statement)")
        print("    - 01-01-25_31-12-25.xls (reference file with categories)")
    
    return all_exist

def check_env_config():
    """Check if .env file is configured"""
    print("\nChecking configuration...")
    env_file = Path(".env")
    
    if not env_file.exists():
        print("  ✗ .env file not found")
        print("\n  Setup required:")
        print("    1. Copy .env.example to .env")
        print("    2. Add your OpenAI or Azure OpenAI API key")
        print("    OR run: python setup.py")
        return False
    
    print("  ✓ .env file exists")
    
    # Check if API key is configured
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        openai_key = os.getenv("OPENAI_API_KEY")
        azure_key = os.getenv("AZURE_OPENAI_API_KEY")
        
        if openai_key and openai_key != "sk-your-api-key-here":
            print("  ✓ OpenAI API key configured")
            return True
        elif azure_key and azure_key != "your-api-key-here":
            print("  ✓ Azure OpenAI API key configured")
            return True
        else:
            print("  ✗ No valid API key found in .env")
            print("    Please add your OPENAI_API_KEY or AZURE_OPENAI_API_KEY")
            return False
    except Exception as e:
        print(f"  ⚠ Could not validate .env: {e}")
        return False

def check_write_permissions():
    """Check if we can write output files"""
    print("\nChecking write permissions...")
    try:
        test_file = Path("test_write_permission.tmp")
        test_file.write_text("test")
        test_file.unlink()
        print("  ✓ Can write output files")
        return True
    except Exception as e:
        print(f"  ✗ Cannot write files: {e}")
        return False

def main():
    """Run all validation checks"""
    print("="*60)
    print("Bank Statement Processor - Setup Validation")
    print("="*60)
    
    checks = [
        ("Python Version", check_python_version()),
        ("Dependencies", check_dependencies()),
        ("Code Files", check_files()),
        ("Input Files", check_input_files()),
        ("Configuration", check_env_config()),
        ("Write Permissions", check_write_permissions())
    ]
    
    print("\n" + "="*60)
    print("Validation Summary")
    print("="*60)
    
    all_passed = True
    for check_name, passed in checks:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:10} - {check_name}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n✓ All checks passed! You're ready to run:")
        print("  python tests/test_components.py  (test individual components)")
        print("  python scripts/main.py           (run full pipeline)")
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Set up API key: python scripts/setup.py")
        print("  3. Ensure input files are in the correct location")
    
    print()
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
