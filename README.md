# Semantic Kernel Bank Statement Processor

An AI-powered transaction categorization system using **Microsoft Semantic Kernel** and **OpenAI/Azure OpenAI** to automatically process bank statements and generate formatted Excel outputs for financial app import.

## Features

- ✅ **Automatic Transaction Extraction** from bank statements
- ✅ **AI-Powered Categorization** using GPT-4 via Semantic Kernel
- ✅ **Smart Text Cleaning** handles truncated/partial words (e.g., "frui" → "fruit")
- ✅ **Category Learning** from reference transaction history
- ✅ **Compliant Excel Export** with mandatory field validation
- ✅ **Support for Income/Expense/Transfer** transaction types

## Architecture

```
┌─────────────────────┐
│  AccountStatement   │
│   _edited.xlsx      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐      ┌──────────────────┐
│  Data Extractor     │◄─────┤  Reference File  │
│  - Parse dates      │      │  (Categories)    │
│  - Clean text       │      └──────────────────┘
│  - Extract amounts  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  AI Categorizer     │
│  (Semantic Kernel)  │
│  - GPT-4 Analysis   │
│  - Category Match   │
│  - Type Detection   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Excel Exporter     │
│  - Format dates     │
│  - Validate fields  │
│  - Generate .xls    │
└──────────┬──────────┘
           │
           ▼
    processed_transactions.xls
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- Virtual environment (already exists: `venv/`)
- OpenAI API key or Azure OpenAI credentials

### 2. Install Dependencies

```bash
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Configure API Keys

Copy the example environment file and add your API key:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

**For OpenAI:**
```env
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4
```

**For Azure OpenAI:**
```env
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
```

Then update `config.py` to set `USE_AZURE_OPENAI = True` if using Azure.

### 4. Run the Processor

```bash
python main.py
```

## Input Files

### 1. `AccountStatement_edited.xlsx`
Your bank statement with columns:
- Date
- Details
- Ref No/Cheque No
- Debit
- Credit
- Balance

### 2. `01-01-25_31-12-25.xls`
Reference file containing:
- Historical transactions
- Valid categories and subcategories
- Transaction type examples

## Output Format

The generated `.xls` file contains these columns in **exact order**:

```
Date – Account – Category – Subcategory – Note – Amount – Income/Expense – Description
```

### Mandatory Rules

1. **Date Format**: MM/DD/YYYY (e.g., 11/15/2023)
2. **Account**: MANDATORY - Must not be empty
3. **Category**: MANDATORY - Must match predefined categories
4. **Transaction Types**: Only `Income`, `Expense`, or `Transfer-Out`
5. **Transfer Rules**: 
   - Account = sender's account
   - Category = beneficiary's account

## File Structure

```
Money_manager/
├── main.py                          # Main orchestrator
├── data_extractor.py                # Extract & clean transactions
├── categorizer.py                   # AI categorization engine
├── excel_exporter.py                # Export to Excel
├── config.py                        # Configuration
├── requirements.txt                 # Python dependencies
├── .env                            # API keys (create from .env.example)
├── AccountStatement_edited.xlsx    # Input: Bank statement
├── 01-01-25_31-12-25.xls          # Input: Reference data
└── processed_transactions.xls      # Output: Categorized transactions
```

## How It Works

### 1. Data Extraction (`data_extractor.py`)
- Reads bank statement Excel file
- Cleans transaction details
- Handles truncated text (e.g., "frui" → "fruit")
- Extracts amounts, dates, and descriptions
- Loads reference categories from historical data

### 2. AI Categorization (`categorizer.py`)
- Uses **Semantic Kernel** framework
- Sends transactions to GPT-4 with context:
  - Available categories/subcategories
  - Reference transaction examples
  - Pattern matching rules
- AI analyzes details and assigns:
  - Category
  - Subcategory
  - Transaction type (Income/Expense/Transfer)
  - Account name
  - Descriptive note

### 3. Excel Export (`excel_exporter.py`)
- Formats dates to MM/DD/YYYY
- Validates mandatory fields
- Generates compliant .xls file
- Creates summary report with statistics

## Handling Truncated Text

The system automatically fixes common truncation issues:

```python
# Examples:
"frui " → "fruit"
"veget " → "vegetable"
"groceri " → "groceries"
"restauran " → "restaurant"
```

## Example Output

```
Date          Account      Category    Subcategory   Note        Amount  Income/Expense  Description
11/15/2023    SBI Account  Food        fruits        Grace Pa    229.00  Expense         UPI/DR/.../Grace Pa/...
11/16/2023    SBI Account  Salary      -             Monthly     90100   Income          ACHCr HDFC/Salary...
11/17/2023    SBI Account  Transfer    -             To Cash     5000    Transfer-Out    Transfer to Cash...
```

## Logging

All operations are logged to:
- Console (real-time progress)
- `transaction_processor.log` (detailed logs)

## Troubleshooting

### No API Key Error
```
Error: No API key found!
Solution: Create .env file from .env.example and add your API key
```

### Missing Dependencies
```bash
pip install -r requirements.txt
```

### Import Fails in Financial App
- Check that Account and Category fields are not empty
- Verify date format is MM/DD/YYYY
- Ensure transaction types are: Income, Expense, or Transfer-Out

## Customization

### Add New Categories
Edit `01-01-25_31-12-25.xls` to include new categories, then re-run.

### Change Output Format
Modify `excel_exporter.py` column order or date format.

### Adjust AI Behavior
Edit the prompt in `categorizer.py` → `_build_categorization_prompt()`

## Summary Report Example

```
=== Transaction Export Summary ===
Total Transactions: 338

By Type:
- Income: 42 transactions (₹270,300.00)
- Expense: 290 transactions (₹185,450.00)
- Transfer-Out: 6 transactions (₹15,000.00)

Net: ₹69,850.00

Top 5 Categories by Amount:
- Food: 95 txns, ₹45,230.00
- Transportation: 45 txns, ₹32,100.00
- Investment: 12 txns, ₹28,000.00
- Household: 38 txns, ₹22,450.00
- Entertainment: 28 txns, ₹15,670.00
```

## Technical Stack

- **Python 3.8+**
- **Semantic Kernel** - AI orchestration framework
- **OpenAI GPT-4** - Transaction categorization
- **Pandas** - Data manipulation
- **OpenPyXL** - Excel file handling

## License

Private use for personal financial management.
