"""
Configuration file for Semantic Kernel Bank Statement Processor
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Azure OpenAI Configuration (update with your credentials)
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")

# OpenAI Configuration (alternative if not using Azure)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

# File paths
INPUT_STATEMENT_FILE = "AccountStatement_edited.xlsx"
REFERENCE_FILE = "01-01-25_31-12-25.xls"
OUTPUT_FILE = "processed_transactions.tsv"  # Using .xlsx for better compatibility

# Default account name
DEFAULT_ACCOUNT = "SBI Account"

# Date format for output
OUTPUT_DATE_FORMAT = "%d/%m/%Y"

# Use Azure OpenAI or standard OpenAI
USE_AZURE_OPENAI = True  # Set to True if using Azure OpenAI
