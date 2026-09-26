"""
Main Semantic Kernel Bank Statement Processor
Orchestrates the complete transaction processing pipeline
"""

import asyncio
import logging
from datetime import datetime

from data_extractor import DataExtractor
from categorizer import TransactionCategorizer
from excel_exporter import ExcelExporter
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('transaction_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BankStatementProcessor:
    """Main orchestrator for bank statement processing"""
    
    def __init__(self):
        self.extractor = None
        self.categorizer = None
        self.exporter = None
        
    async def process(self):
        """Execute the complete processing pipeline"""
        try:
            logger.info("="*60)
            logger.info("Starting Bank Statement Processing Pipeline")
            logger.info("="*60)
            
            # Step 1: Initialize Data Extractor
            logger.info("\n[Step 1/5] Initializing Data Extractor...")
            self.extractor = DataExtractor(
                statement_file=config.INPUT_STATEMENT_FILE,
                reference_file=config.REFERENCE_FILE
            )
            
            # Step 2: Load Reference Data
            logger.info("\n[Step 2/5] Loading Reference Data...")
            self.extractor.load_reference_data()
            category_mappings = self.extractor.get_category_mappings()
            transaction_examples = self.extractor.get_transaction_examples()
            
            logger.info(f"Loaded {len(category_mappings)} categories")
            logger.info(f"Categories: {', '.join(list(category_mappings.keys())[:10])}...")
            
            # Step 3: Extract Transactions
            logger.info("\n[Step 3/5] Extracting Transactions from Statement...")
            transactions = self.extractor.extract_transactions()
            
            if not transactions:
                logger.error("No transactions extracted. Exiting.")
                return False
            
            logger.info(f"Extracted {len(transactions)} transactions")
            
            # Step 4: Initialize AI Categorizer
            logger.info("\n[Step 4/5] Initializing AI Categorizer...")
            
            # Check API key
            api_key = config.AZURE_OPENAI_API_KEY if config.USE_AZURE_OPENAI else config.OPENAI_API_KEY
            
            if not api_key:
                logger.error("No API key found! Please set OPENAI_API_KEY or AZURE_OPENAI_API_KEY in .env file")
                logger.info("Copy .env.example to .env and add your API key")
                return False
            
            self.categorizer = TransactionCategorizer(
                api_key=api_key,
                use_azure=config.USE_AZURE_OPENAI,
                azure_endpoint=config.AZURE_OPENAI_ENDPOINT if config.USE_AZURE_OPENAI else None,
                deployment_name=config.AZURE_OPENAI_DEPLOYMENT_NAME if config.USE_AZURE_OPENAI else None,
                model=config.OPENAI_MODEL
            )
            
            self.categorizer.set_reference_data(category_mappings, transaction_examples)
            
            # Categorize transactions
            logger.info("\n[Step 5/5] Categorizing Transactions with AI...")
            categorized_transactions = await self.categorizer.categorize_batch(transactions)
            
            # Step 6: Export to Excel
            logger.info("\n[Step 6/5] Exporting to Excel...")
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
                
                logger.info(f"\nOutput file: {config.OUTPUT_FILE}")
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
    processor = BankStatementProcessor()
    success = await processor.process()
    
    if success:
        print("\n✓ All done! Check the output file.")
    else:
        print("\n✗ Processing failed. Check the logs for details.")
    
    return success


if __name__ == "__main__":
    # Run the async pipeline
    asyncio.run(main())
