"""
Excel Export Module
Generates compliant .xls files with proper formatting and validation
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ExcelExporter:
    """Export categorized transactions to TSV or Excel format"""
    
    def __init__(self, output_file: str, date_format: str = "%m/%d/%Y"):
        self.output_file = output_file
        self.date_format = date_format
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
    def export_transactions(self, transactions: List[Dict[str, Any]]) -> bool:
        """
        Export transactions to Excel file with required format
        
        Required columns: Date – Account – Category – Subcategory – Note – Amount – Income/Expense – Description
        """
        try:
            logger.info(f"Exporting {len(transactions)} transactions to {self.output_file}")
            
            # Prepare data for export
            export_data = []
            errors = []
            
            for idx, txn in enumerate(transactions):
                try:
                    row = self._prepare_row(txn)
                    
                    # Validate mandatory fields
                    validation_errors = self._validate_row(row, idx)
                    if validation_errors:
                        errors.extend(validation_errors)
                        logger.warning(f"Row {idx} validation errors: {validation_errors}")
                    
                    export_data.append(row)
                    
                except Exception as e:
                    logger.error(f"Error preparing row {idx}: {str(e)}")
                    errors.append(f"Row {idx}: {str(e)}")
            
            # Create DataFrame with exact column order
            df = pd.DataFrame(export_data, columns=[
                'Date',
                'Account',
                'Category',
                'Subcategory',
                'Note',
                'Amount',
                'Income/Expense',
                'Description'
            ])
            
            # Export based on file extension
            if self.output_file.endswith('.tsv') or self.output_file.endswith('.txt'):
                # Export as TSV (tab-separated values)
                df.to_csv(self.output_file, index=False, sep='\t', encoding='utf-8')
            elif self.output_file.endswith('.csv'):
                # Export as CSV
                df.to_csv(self.output_file, index=False, encoding='utf-8')
            elif self.output_file.endswith('.xlsx'):
                # Export as Excel .xlsx
                df.to_excel(self.output_file, index=False, engine='openpyxl')
            else:
                # Default to TSV
                df.to_csv(self.output_file, index=False, sep='\t', encoding='utf-8')
            
            logger.info(f"Successfully exported to {self.output_file}")
            
            if errors:
                logger.warning(f"Export completed with {len(errors)} validation warnings")
                for error in errors[:10]:  # Show first 10 errors
                    logger.warning(error)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to export transactions: {str(e)}")
            return False
    
    def _prepare_row(self, txn: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare a single transaction row for export"""
        
        # Format date
        date_obj = txn['date']
        if isinstance(date_obj, str):
            # Parse if string
            try:
                date_obj = datetime.strptime(date_obj, '%d/%m/%Y')
            except ValueError:
                date_obj = datetime.now()
        
        date_str = date_obj.strftime(self.date_format)
        
        # Get transaction type (normalize)
        txn_type = txn.get('transaction_type', 'Expense')
        if txn_type not in ['Income', 'Expense', 'Transfer-Out']:
            txn_type = 'Expense'
        
        # Prepare row data
        row = {
            'Date': date_str,
            'Account': txn.get('account', 'SBI Account'),
            'Category': txn.get('category', 'Miscellaneous'),
            'Subcategory': txn.get('subcategory', ''),
            'Note': txn.get('note', '')[:200],  # Limit note length
            'Amount': abs(float(txn['amount'])),  # Ensure positive
            'Income/Expense': txn_type,
            'Description': txn.get('description', '')[:500]  # Limit description
        }
        
        # Clean empty strings to None for better Excel display
        if not row['Subcategory'] or row['Subcategory'] in ['nan', 'None']:
            row['Subcategory'] = ''
        
        if not row['Note']:
            row['Note'] = ''
        
        return row
    
    def _validate_row(self, row: Dict[str, Any], row_idx: int) -> List[str]:
        """Validate a row against mandatory requirements"""
        errors = []
        
        # Check mandatory fields
        if not row.get('Date'):
            errors.append(f"Row {row_idx}: Missing Date")
        
        if not row.get('Account'):
            errors.append(f"Row {row_idx}: Missing Account (MANDATORY)")
        
        if not row.get('Category'):
            errors.append(f"Row {row_idx}: Missing Category (MANDATORY)")
        
        if row.get('Amount') is None:
            errors.append(f"Row {row_idx}: Missing Amount")
        
        # Validate transaction type
        valid_types = ['Income', 'Expense', 'Transfer-Out']
        if row.get('Income/Expense') not in valid_types:
            errors.append(f"Row {row_idx}: Invalid Income/Expense value: {row.get('Income/Expense')}")
        
        # Validate date format
        try:
            datetime.strptime(row['Date'], self.date_format)
        except ValueError:
            errors.append(f"Row {row_idx}: Invalid date format: {row.get('Date')}")
        
        return errors
    
    def generate_summary_report(self, transactions: List[Dict[str, Any]]) -> str:
        """Generate a summary report of the exported transactions"""
        
        if not transactions:
            return "No transactions to report"
        
        # Calculate statistics
        total_count = len(transactions)
        
        income_txns = [t for t in transactions if t.get('transaction_type') == 'Income']
        expense_txns = [t for t in transactions if t.get('transaction_type') == 'Expense']
        transfer_txns = [t for t in transactions if t.get('transaction_type') == 'Transfer-Out']
        
        total_income = sum(t['amount'] for t in income_txns)
        total_expense = sum(t['amount'] for t in expense_txns)
        total_transfer = sum(t['amount'] for t in transfer_txns)
        
        # Category breakdown
        categories = {}
        for t in transactions:
            cat = t.get('category', 'Unknown')
            if cat not in categories:
                categories[cat] = {'count': 0, 'amount': 0}
            categories[cat]['count'] += 1
            categories[cat]['amount'] += t['amount']
        
        # Build report
        report = f"""
=== Transaction Export Summary ===
Total Transactions: {total_count}

By Type:
- Income: {len(income_txns)} transactions (₹{total_income:,.2f})
- Expense: {len(expense_txns)} transactions (₹{total_expense:,.2f})
- Transfer-Out: {len(transfer_txns)} transactions (₹{total_transfer:,.2f})

Net: ₹{(total_income - total_expense - total_transfer):,.2f}

Top 5 Categories by Amount:
"""
        
        sorted_cats = sorted(categories.items(), key=lambda x: x[1]['amount'], reverse=True)
        for cat, data in sorted_cats[:5]:
            report += f"- {cat}: {data['count']} txns, ₹{data['amount']:,.2f}\n"
        
        return report
