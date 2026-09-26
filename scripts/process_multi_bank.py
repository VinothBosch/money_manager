"""
Multi-Bank Statement Processor
Processes transactions from multiple bank accounts (SBI + HDFC)
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Allow running this script directly from the scripts/ folder
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from money_manager.data_extractor import DataExtractor
from money_manager.hdfc_extractor import HDFCExtractor
from money_manager.categorizer import TransactionCategorizer
from money_manager.excel_exporter import ExcelExporter
from money_manager import config_multi_bank as config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/multi_bank_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MultiBankProcessor:
    """Process statements from multiple banks"""
    
    def __init__(self):
        self.categorizer = None
        self.exporter = None
        
    async def process(self):
        """Execute the complete processing pipeline for all banks"""
        try:
            logger.info("="*60)
            logger.info("Multi-Bank Statement Processing Pipeline")
            logger.info("="*60)
            
            # Step 1: Load Reference Data
            logger.info("\n[Step 1/5] Loading Reference Data...")
            reference_extractor = DataExtractor(
                statement_file=config.BANK_ACCOUNTS['SBI']['statement_file'],
                reference_file=config.REFERENCE_FILE
            )
            reference_extractor.load_reference_data()
            category_mappings = reference_extractor.get_category_mappings()
            transaction_examples = reference_extractor.get_transaction_examples()
            
            logger.info(f"Loaded {len(category_mappings)} categories")
            
            # Step 2: Extract Transactions from All Banks
            logger.info("\n[Step 2/5] Extracting Transactions from All Banks...")
            all_transactions = []
            
            for bank_name, bank_config in config.BANK_ACCOUNTS.items():
                logger.info(f"\nProcessing {bank_name} Account...")
                
                try:
                    if bank_config['extractor_type'] == 'SBI':
                        extractor = DataExtractor(
                            statement_file=bank_config['statement_file'],
                            reference_file=config.REFERENCE_FILE
                        )
                        transactions = extractor.extract_transactions()
                    elif bank_config['extractor_type'] == 'HDFC':
                        extractor = HDFCExtractor(
                            statement_file=bank_config['statement_file']
                        )
                        transactions = extractor.extract_transactions()
                    else:
                        logger.warning(f"Unknown extractor type: {bank_config['extractor_type']}")
                        continue
                    
                    # Add account name to each transaction
                    for txn in transactions:
                        txn['source_account'] = bank_config['account_name']
                    
                    all_transactions.extend(transactions)
                    logger.info(f"  ✓ Extracted {len(transactions)} transactions from {bank_name}")
                    
                except FileNotFoundError:
                    logger.warning(f"  ⚠ Statement file not found for {bank_name}: {bank_config['statement_file']}")
                except Exception as e:
                    logger.error(f"  ✗ Error processing {bank_name}: {str(e)}")
            
            if not all_transactions:
                logger.error("No transactions extracted from any bank. Exiting.")
                return False
            
            logger.info(f"\nTotal transactions extracted: {len(all_transactions)}")
            
            # Sort transactions by date
            all_transactions.sort(key=lambda x: x['date'])
            
            # Step 3: Initialize AI Categorizer
            logger.info("\n[Step 3/5] Initializing AI Categorizer...")
            
            api_key = config.AZURE_OPENAI_API_KEY if config.USE_AZURE_OPENAI else config.OPENAI_API_KEY
            
            if not api_key:
                logger.error("No API key found! Please set API key in .env file")
                return False
            
            self.categorizer = TransactionCategorizer(
                api_key=api_key,
                use_azure=config.USE_AZURE_OPENAI,
                azure_endpoint=config.AZURE_OPENAI_ENDPOINT if config.USE_AZURE_OPENAI else None,
                deployment_name=config.AZURE_OPENAI_DEPLOYMENT_NAME if config.USE_AZURE_OPENAI else None,
                model=config.OPENAI_MODEL
            )
            
            self.categorizer.set_reference_data(category_mappings, transaction_examples)
            
            # Step 4: Categorize Transactions
            logger.info("\n[Step 4/5] Categorizing Transactions with AI...")
            categorized_transactions = await self.categorizer.categorize_batch(all_transactions)
            
            # Ensure account field is set from source_account for ALL transactions
            for txn in categorized_transactions:
                # Always use source_account if available, otherwise keep existing account
                if 'source_account' in txn and txn['source_account']:
                    txn['account'] = txn['source_account']
                elif 'account' not in txn or not txn['account'] or txn['account'] == 'null':
                    # Fallback: try to determine from original transaction data
                    # This shouldn't happen, but ensures no null accounts
                    txn['account'] = 'SBI Account'  # Default fallback
            
            # Step 5: Export to TSV
            logger.info("\n[Step 5/5] Exporting to TSV...")
            self.exporter = ExcelExporter(
                output_file=config.OUTPUT_FILE,
                date_format=config.OUTPUT_DATE_FORMAT
            )
            
            success = self.exporter.export_transactions(categorized_transactions)
            
            if success:
                logger.info("\n" + "="*60)
                logger.info("✓ Processing Complete!")
                logger.info("="*60)
                
                # Generate and display summary
                summary = self.exporter.generate_summary_report(categorized_transactions)
                logger.info(summary)
                
                # Bank-wise summary
                logger.info("\n=== Bank-wise Summary ===")
                for bank_name in config.BANK_ACCOUNTS.keys():
                    account_name = config.BANK_ACCOUNTS[bank_name]['account_name']
                    bank_txns = [t for t in categorized_transactions if t.get('source_account') == account_name]
                    if bank_txns:
                        total = len(bank_txns)
                        income = sum(t['amount'] for t in bank_txns if t.get('transaction_type') == 'Income')
                        expense = sum(t['amount'] for t in bank_txns if t.get('transaction_type') == 'Expense')
                        logger.info(f"\n{bank_name} ({account_name}):")
                        logger.info(f"  Transactions: {total}")
                        logger.info(f"  Income: ₹{income:,.2f}")
                        logger.info(f"  Expense: ₹{expense:,.2f}")
                        logger.info(f"  Net: ₹{(income - expense):,.2f}")
                
                logger.info(f"\n\nOutput file: {config.OUTPUT_FILE}")
                logger.info("Ready for import into your financial app!")
                
                return True
            else:
                logger.error("Export failed!")
                return False
                
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            return False


async def main():
    """Main entry point"""
    processor = MultiBankProcessor()
    success = await processor.process()
    
    if success:
        print("\n✓ All done! Check the output file.")
    else:
        print("\n✗ Processing failed. Check the logs for details.")
    
    return success


if __name__ == "__main__":
    asyncio.run(main())
