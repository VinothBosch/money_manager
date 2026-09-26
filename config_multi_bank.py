"""
Configuration file for processing both SBI and HDFC statements
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Azure OpenAI Configuration
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

# Bank statement configurations
BANK_ACCOUNTS = {
    'SBI': {
        'statement_file': 'AccountStatement_edited.xlsx',
        'account_name': 'SBI Account',
        'extractor_type': 'SBI'
    },
    'HDFC': {
        'statement_file': 'HDFC_account.xls',
        'account_name': 'HDFC Savings Account',
        'extractor_type': 'HDFC'
    }
}

# Reference file for categorization
REFERENCE_FILE = "01-01-25_31-12-25.xls"

# Output file
OUTPUT_FILE = "processed_transactions_combined.tsv"

# Date format for output
OUTPUT_DATE_FORMAT = "%d/%m/%Y"

# Use Azure OpenAI or standard OpenAI
USE_AZURE_OPENAI = True
