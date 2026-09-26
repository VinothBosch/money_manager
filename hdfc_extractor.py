"""
HDFC Bank Statement Extractor
Handles reading and cleaning transaction data from HDFC bank statements
"""

import pandas as pd
import re
from datetime import datetime
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HDFCExtractor:
    """Extract and clean transaction data from HDFC bank statement Excel files"""
    
    def __init__(self, statement_file: str):
        self.statement_file = statement_file
        self.transactions = []
        
    def extract_transactions(self) -> List[Dict[str, Any]]:
        """Extract transactions from HDFC bank statement"""
        logger.info(f"Extracting transactions from HDFC: {self.statement_file}")
        
        try:
            # Read statement without header
            df = pd.read_excel(self.statement_file, header=None)
            
            # Find the header row (contains 'Date', 'Narration', etc.)
            header_row = None
            for idx, row in df.iterrows():
                if any('Date' in str(cell) for cell in row.values):
                    header_row = idx
                    break
            
            if header_row is None:
                logger.error("Could not find header row in HDFC statement")
                return []
            
            # Re-read with correct header
            df = pd.read_excel(self.statement_file, header=header_row)
            
            # Clean column names
            df.columns = ['Date', 'Narration', 'Chq_Ref_No', 'Value_Dt', 'Withdrawal', 'Deposit', 'Balance']
            
            # Skip asterisk rows and rows with invalid dates
            df = df[~df['Date'].astype(str).str.contains(r'\*+', na=False)]
            df = df[pd.notna(df['Date'])]
            df = df[df['Date'].astype(str).str.match(r'\d{2}/\d{2}/\d{2}', na=False)]
            
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
            logger.info(f"Extracted {len(transactions)} HDFC transactions")
            return transactions
        
        except FileNotFoundError:
            logger.error(f"Statement file not found: {self.statement_file}")
            raise
        except Exception as e:
            logger.error(f"Error extracting transactions: {str(e)}")
            raise
    
    def _parse_transaction(self, row: pd.Series) -> Dict[str, Any]:
        """Parse a single HDFC transaction row"""
        # Parse date (format: dd/mm/yy)
        date_str = str(row['Date'])
        try:
            # Handle dd/mm/yy format
            date_obj = datetime.strptime(date_str, '%d/%m/%y')
        except:
            logger.warning(f"Could not parse date: {date_str}")
            return None
        
        # Clean and normalize narration
        narration = self._clean_details(str(row['Narration']))
        
        # Determine amount and type
        withdrawal = row['Withdrawal']
        deposit = row['Deposit']
        
        # Handle withdrawal (outgoing - expense)
        if pd.notna(withdrawal):
            try:
                amount = float(withdrawal)
                if amount > 0:
                    transaction_type = 'Expense'
                else:
                    return None
            except (ValueError, TypeError):
                return None
        # Handle deposit (incoming - income)
        elif pd.notna(deposit):
            try:
                amount = float(deposit)
                if amount > 0:
                    transaction_type = 'Income'
                else:
                    return None
            except (ValueError, TypeError):
                return None
        else:
            return None
        
        return {
            'date': date_obj,
            'details': narration,
            'amount': amount,
            'transaction_type': transaction_type,
            'ref_no': str(row['Chq_Ref_No']) if pd.notna(row['Chq_Ref_No']) else '',
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
        
        for pattern, replacement in truncation_fixes.items():
            details = re.sub(pattern, replacement, details, flags=re.IGNORECASE)
        
        # Context-specific fixes
        # Fix "prozone" as parking charge
        if re.search(r'\bprozone\b', details, re.IGNORECASE):
            details = re.sub(r'\bprozone\b', 'prozone parking', details, flags=re.IGNORECASE)
        
        # IMPS transfers to VINOTH P are self transfers
        if re.search(r'IMPS.*VINOTH\s*P.*SBIN', details, re.IGNORECASE):
            details += ' self transfer HDFC to SBI'
        
        # UPI transfers to self
        if re.search(r'VINOTH\s*P.*SBIN', details, re.IGNORECASE):
            details += ' self transfer'
        
        return details
