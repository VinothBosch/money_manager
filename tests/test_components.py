"""
Quick Test Script
Tests individual components before running the full pipeline
"""

import sys
from pathlib import Path

# Allow running this script directly from the tests/ folder
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from money_manager.data_extractor import DataExtractor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_data_extraction():
    """Test data extraction component"""
    print("\n" + "="*60)
    print("Testing Data Extraction")
    print("="*60)
    
    extractor = DataExtractor(
        statement_file="data/input/AccountStatement_edited.xlsx",
        reference_file="data/input/01-01-25_31-12-25.xls"
    )
    
    # Load reference data
    print("\n1. Loading reference data...")
    extractor.load_reference_data()
    mappings = extractor.get_category_mappings()
    print("\n" + "="*60)
    print(f"[OK] Found {len(mappings)} categories")
    print(f"   Categories: {list(mappings.keys())[:5]}...")
    
    # Extract transactions
    print("\n2. Extracting transactions...")
    transactions = extractor.extract_transactions()
    print(f"   [OK] Extracted {len(transactions)} transactions")
    
    # Show sample transactions
    print("\n3. Sample transactions:")
    for i, txn in enumerate(transactions[:3]):
        print(f"\n   Transaction {i+1}:")
        print(f"   - Date: {txn['date'].strftime('%d/%m/%Y')}")
        print(f"   - Details: {txn['details'][:80]}...")
        print(f"   - Amount: Rs. {txn['amount']}")
        print(f"   - Type: {txn['transaction_type']}")
    
    # Test text cleaning
    print("\n4. Testing text cleaning...")
    test_texts = [
        "UPI/DR/123/Grace Pa/YESB/frui ",
        "WDL TFR groceri store",
        "Payment to restauran "
    ]
    for text in test_texts:
        cleaned = extractor._clean_details(text)
        print(f"   '{text}' → '{cleaned}'")
    
    print("\n" + "="*60)
    print("[OK] Data Extraction Test Complete!")
    print("="*60)
    
    return extractor, transactions

def test_excel_structure():
    """Test Excel file structure"""
    print("\n" + "="*60)
    print("Testing Excel Files Structure")
    print("="*60)
    
    # Check input statement
    print("\n1. AccountStatement_edited.xlsx:")
    df_statement = pd.read_excel("data/input/AccountStatement_edited.xlsx", header=1)
    print(f"   Shape: {df_statement.shape}")
    print(f"   Columns: {df_statement.columns.tolist()}")
    
    # Check reference file
    print("\n2. 01-01-25_31-12-25.xls:")
    df_ref = pd.read_excel("data/input/01-01-25_31-12-25.xls")
    print(f"   Shape: {df_ref.shape}")
    print(f"   Columns: {df_ref.columns.tolist()}")
    print(f"   Transaction types: {df_ref['Income/Expense'].unique()}")
    
    print("\n" + "="*60)
    print("[OK] Excel Structure Test Complete!")
    print("="*60)

if __name__ == "__main__":
    print("\nRunning Component Tests...\n")
    
    try:
        # Test Excel structure
        test_excel_structure()
        
        # Test data extraction
        extractor, transactions = test_data_extraction()
        
        print("\n" + "="*60)
        print("[OK] ALL TESTS PASSED!")
        print("="*60)
        print("\nNext steps:")
        print("1. Create .env file with your OpenAI API key")
        print("2. Run: python main.py")
        
    except Exception as e:
        print(f"\n[FAIL] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
