"""
Data Extraction Module
Handles reading and cleaning transaction data from bank statements
"""

import pandas as pd
import re
from datetime import datetime
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataExtractor:
    """Extract and clean transaction data from bank statement Excel files"""
    
    def __init__(self, statement_file: str, reference_file: str):
        self.statement_file = statement_file
        self.reference_file = reference_file
        self.transactions = []
        self.reference_data = None
        
    def load_reference_data(self) -> pd.DataFrame:
        """Load reference file to understand category patterns"""
        logger.info(f"Loading reference file: {self.reference_file}")
        try:
            # Try with different engines for .xls files
            if self.reference_file.endswith('.xls'):
                try:
                    df = pd.read_excel(self.reference_file, engine='xlrd')
                except Exception:
                    # Fallback to openpyxl if xlrd fails
                    df = pd.read_excel(self.reference_file, engine='openpyxl')
            else:
                df = pd.read_excel(self.reference_file)
            
            self.reference_data = df
            logger.info(f"Successfully loaded {len(df)} reference transactions")
            return df
        except FileNotFoundError:
            logger.error(f"Reference file not found: {self.reference_file}")
            raise
        except Exception as e:
            logger.error(f"Error loading reference file: {str(e)}")
            raise
    
    def extract_transactions(self) -> List[Dict[str, Any]]:
        """Extract transactions from bank statement"""
        logger.info(f"Extracting transactions from: {self.statement_file}")
        
        try:
            # Read statement with proper header (row 1)
            df = pd.read_excel(self.statement_file, header=1)
            
            # Clean column names
            df.columns = ['Date', 'Details', 'Ref_No', 'Debit', 'Credit', 'Balance']
            
            # Drop rows with invalid dates
            df = df[pd.notna(df['Date'])]
            
            transactions = []
            for idx, row in df.iterrows():
                try:
                    transaction = self._parse_transaction(row)
                    if transaction:
                        transactions.append(transaction)
                except Exception as e:
                    logger.warning(f"Error parsing row {idx}: {str(e)}")
                    continue
            
            self.transactions = transactions
            logger.info(f"Extracted {len(transactions)} transactions")
            return transactions
        
        except FileNotFoundError:
            logger.error(f"Statement file not found: {self.statement_file}")
            raise
        except Exception as e:
            logger.error(f"Error extracting transactions: {str(e)}")
            raise
    
    def _parse_transaction(self, row: pd.Series) -> Dict[str, Any]:
        """Parse a single transaction row"""
        # Parse date
        date_str = str(row['Date'])
        try:
            if '/' in date_str:
                date_obj = datetime.strptime(date_str, '%d/%m/%Y')
            else:
                date_obj = pd.to_datetime(row['Date'])
        except (ValueError, TypeError):
            logger.warning(f"Could not parse date: {date_str}")
            return None
        
        # Clean and normalize details (handle truncated text)
        details = self._clean_details(str(row['Details']))
        
        # Determine amount and type
        debit = row['Debit']
        credit = row['Credit']
        
        # Handle debit (outgoing - expense)
        if pd.notna(debit):
            try:
                amount = float(debit)
                if amount > 0:
                    transaction_type = 'Expense'  # Will be refined by AI
                else:
                    return None
            except (ValueError, TypeError):
                return None
        # Handle credit (incoming - income)
        elif pd.notna(credit):
            try:
                amount = float(credit)
                if amount > 0:
                    transaction_type = 'Income'  # Will be refined by AI
                else:
                    return None
            except (ValueError, TypeError):
                return None
        else:
            return None
        
        return {
            'date': date_obj,
            'details': details,
            'amount': amount,
            'transaction_type': transaction_type,
            'ref_no': str(row['Ref_No']) if pd.notna(row['Ref_No']) else '',
            'balance': float(row['Balance']) if pd.notna(row['Balance']) else 0.0
        }
    
    def _clean_details(self, details: str) -> str:
        """
        Clean and normalize transaction details
        Handle truncated words and extract meaningful information
        """
        if pd.isna(details) or details == 'nan':
            return ''
        
        # Remove multiple spaces and newlines
        details = re.sub(r'\s+', ' ', details)
        details = details.strip()
        
        # Common truncation fixes
        # Handle cases where words are cut off (e.g., 'frui ' -> 'fruit')
        truncation_fixes = {
            r'\bfrui\s': 'fruit ',
            r'\bveget\s': 'vegetable ',
            r'\bgroceri\s': 'groceries ',
            r'\bsnack\s': 'snacks ',
            r'\brestauran\s': 'restaurant ',
            r'\bpharma\s': 'pharmacy ',
            r'\bmedica\s': 'medical ',
            r'\belectri\s': 'electricity ',
            r'\binte\s': 'internet ',
            r'\bsubscriptio\s': 'subscription ',
            r'\bchic\b': 'chicken',
            r'\bchick\b': 'chicken',
            r'\blunc\b': 'lunch',
        }
        
        # Context-specific fixes based on payee and description patterns
        # Fix "wat" prefix when paying to PAULRAJ R (likely water)
        if 'PAULRAJ R' in details and re.search(r'\bwat\b', details, re.IGNORECASE):
            details = re.sub(r'\bwat\b', 'water', details, flags=re.IGNORECASE)
        
        # Fix "prozone" as parking charge
        if re.search(r'\bprozone\b', details, re.IGNORECASE):
            details = re.sub(r'\bprozone\b', 'prozone parking', details, flags=re.IGNORECASE)
        
        # ACHCr indicates investment returns or dividend
        if re.search(r'\bACHCr\b', details, re.IGNORECASE):
            details += ' investment return'
        
        # XX602-VINOTH P indicates self transfer from HDFC to SBI
        if re.search(r'XX602-VINOTH\s*P', details, re.IGNORECASE):
            details += ' self transfer HDFC to SBI'
        
        for pattern, replacement in truncation_fixes.items():
            details = re.sub(pattern, replacement, details, flags=re.IGNORECASE)
        
        return details
    
    def get_category_mappings(self) -> Dict[str, List[str]]:
        """Extract category and subcategory mappings from reference file"""
        if self.reference_data is None:
            self.load_reference_data()
        
        mappings = {}
        df = self.reference_data
        
        # Group by category and collect unique subcategories
        for category in df['Category'].unique():
            if pd.notna(category):
                subcats = df[df['Category'] == category]['Subcategory'].unique()
                subcats = [str(s) for s in subcats if pd.notna(s) and str(s) != 'nan']
                mappings[str(category)] = subcats
        
        return mappings
    
    def get_transaction_examples(self, limit: int = 50) -> str:
        """Get example transactions from reference file for AI context"""
        if self.reference_data is None:
            self.load_reference_data()
        
        df = self.reference_data.head(limit)
        examples = []
        
        for _, row in df.iterrows():
            example = {
                'description': str(row.get('Description', row.get('Note', ''))),
                'category': str(row['Category']),
                'subcategory': str(row['Subcategory']) if pd.notna(row['Subcategory']) else 'None',
                'type': str(row['Income/Expense']),
                'amount': float(row['Amount']) if pd.notna(row['Amount']) else float(row.get('INR', 0))
            }
            examples.append(example)
        
        return str(examples)
