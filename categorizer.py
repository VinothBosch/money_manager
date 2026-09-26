"""
Semantic Kernel Categorization Engine
Uses AI to categorize transactions based on patterns from reference data
"""

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, OpenAIChatCompletion
from typing import Dict, Any, List
import json
import logging
import asyncio

logger = logging.getLogger(__name__)


class TransactionCategorizer:
    """AI-powered transaction categorization using Semantic Kernel"""
    
    def __init__(self, api_key: str, use_azure: bool = False, 
                 azure_endpoint: str = None, deployment_name: str = None,
                 model: str = "gpt-4"):
        """Initialize Semantic Kernel with OpenAI/Azure OpenAI"""
        self.kernel = sk.Kernel()
        
        # Configure AI service
        if use_azure and azure_endpoint and deployment_name:
            logger.info("Using Azure OpenAI")
            self.ai_service = AzureChatCompletion(
                deployment_name=deployment_name,
                endpoint=azure_endpoint,
                api_key=api_key
            )
        else:
            logger.info("Using OpenAI")
            self.ai_service = OpenAIChatCompletion(
                ai_model_id=model,
                api_key=api_key
            )
        
        self.kernel.add_service(self.ai_service)
        self.category_mappings = {}
        self.transaction_examples = ""
        
    def set_reference_data(self, category_mappings: Dict[str, List[str]], 
                          transaction_examples: str):
        """Set reference data for categorization context"""
        self.category_mappings = category_mappings
        self.transaction_examples = transaction_examples
        
    async def categorize_transaction(self, transaction: Dict[str, Any], 
                                    max_retries: int = 3) -> Dict[str, Any]:
        """
        Categorize a single transaction using AI with retry logic
        Returns: dict with category, subcategory, type, account, note
        """
        
        # Build the categorization prompt
        prompt = self._build_categorization_prompt(transaction)
        
        # Create semantic function
        categorization_function = self.kernel.add_function(
            plugin_name="TransactionPlugin",
            function_name="categorize",
            prompt=prompt,
            description="Categorizes a bank transaction"
        )
        
        last_error = None
        for attempt in range(max_retries):
            try:
                # Execute the function
                result = await self.kernel.invoke(categorization_function)
                result_text = str(result)
                
                # Parse the JSON response
                categorization = self._parse_categorization_result(result_text, transaction)
                return categorization
                
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)  # Wait before retry
        
        logger.error(f"All retry attempts failed: {str(last_error)}")
        return self._get_default_categorization(transaction)
    
    def _build_categorization_prompt(self, transaction: Dict[str, Any]) -> str:
        """Build the AI prompt for transaction categorization"""
        
        categories_str = "\n".join([
            f"- {cat}: {', '.join(subcats) if subcats else 'No subcategories'}"
            for cat, subcats in self.category_mappings.items()
        ])
        
        prompt = f"""You are an expert financial transaction categorizer. Analyze the bank transaction and categorize it accurately.

**Available Categories and Subcategories:**
{categories_str}

**Transaction Types:**
- Income: Money received (salary, repayment received, investment returns, etc.)
  * Income should NEVER use 'Household' category
  * Income should NEVER use 'SBI Account' category
  * Use appropriate income categories like: Salary, Investment, Repay, etc.
- Expense: Money spent on goods/services
- Transfer-Out: Money transferred between your own accounts/assets
  * Use Transfer-Out ONLY for moving money between your own accounts
  * If description contains "VINOTH P-SBIN-XXXXXXX7522", it's a transfer to SBI Account
  * For such transfers: transaction_type = "Transfer-Out", Category = "SBI Account"
  * Account = source account (e.g., 'HDFC Savings Account' or 'SBI Account')
  * This is NOT income or expense, just moving money between your assets

**Important Category Rules:**
- 'SBI Account' is a valid category ONLY for Transfer-Out transactions (when transferring TO SBI)
- 'SBI Account' should NOT be used for regular Income or Expense transactions
- 'HDFC Savings Account' is a valid category ONLY for Transfer-Out transactions (when transferring TO HDFC)
- 'Household' category is for expenses only, NEVER for income
- When you see "VINOTH P-SBIN-XXXXXXX7522" in details: Always use Transfer-Out with Category="SBI Account"

**Transaction to Categorize:**
- Details: {transaction['details']}
- Amount: ₹{transaction['amount']}
- Current Type: {transaction['transaction_type']}
- Date: {transaction['date'].strftime('%d/%m/%Y')}

**Reference Examples (first 20):**
{self.transaction_examples[:2000]}

**Instructions:**
1. Analyze the transaction details carefully
2. Handle partial/truncated words (e.g., "frui" likely means "fruit")
3. Match to the EXACT category names from the available list
4. Choose appropriate subcategory if available
5. Determine if it's Income, Expense, or Transfer-Out
6. Extract meaningful keywords for the Note field

**Respond ONLY with valid JSON in this exact format:**
{{
    "category": "exact category name from list",
    "subcategory": "exact subcategory name or null",
    "transaction_type": "Income or Expense or Transfer-Out",
    "account": "SBI Account",
    "note": "brief description/keywords"
}}

JSON Response:"""
        
        return prompt
    
    def _parse_categorization_result(self, result_text: str, 
                                     transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI response and validate categorization"""
        try:
            # Extract JSON from response
            result_text = result_text.strip()
            
            # Find JSON content between curly braces
            start_idx = result_text.find('{')
            end_idx = result_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = result_text[start_idx:end_idx+1]
                categorization = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
            
            # Validate required fields
            required_fields = ['category', 'transaction_type', 'account']
            for field in required_fields:
                if field not in categorization or not categorization[field]:
                    logger.warning(f"Missing required field: {field}")
                    return self._get_default_categorization(transaction)
            
            # Ensure transaction_type is valid
            valid_types = ['Income', 'Expense', 'Transfer-Out']
            if categorization['transaction_type'] not in valid_types:
                categorization['transaction_type'] = transaction['transaction_type']
            
            # Clean up subcategory
            if 'subcategory' in categorization:
                if categorization['subcategory'] in ['null', 'None', None, 'nan']:
                    categorization['subcategory'] = ''
            else:
                categorization['subcategory'] = ''
            
            # Add original transaction data
            categorization['amount'] = transaction['amount']
            categorization['date'] = transaction['date']
            categorization['description'] = transaction['details']
            
            # Preserve source_account if it exists
            if 'source_account' in transaction:
                categorization['source_account'] = transaction['source_account']
            
            return categorization
            
        except Exception as e:
            logger.error(f"Error parsing categorization result: {str(e)}")
            logger.debug(f"Result text: {result_text}")
            return self._get_default_categorization(transaction)
    
    def _get_default_categorization(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Return default categorization when AI fails"""
        default_cat = {
            'category': 'Missilaneous',
            'subcategory': '',
            'transaction_type': transaction['transaction_type'],
            'account': transaction.get('source_account', 'SBI Account'),
            'note': transaction['details'][:100],
            'amount': transaction['amount'],
            'date': transaction['date'],
            'description': transaction['details']
        }
        
        # Preserve source_account if it exists
        if 'source_account' in transaction:
            default_cat['source_account'] = transaction['source_account']
        
        return default_cat
    
    async def categorize_batch(self, transactions: List[Dict[str, Any]], 
                              batch_size: int = 10) -> List[Dict[str, Any]]:
        """Categorize multiple transactions"""
        categorized = []
        
        logger.info(f"Categorizing {len(transactions)} transactions...")
        
        for i, transaction in enumerate(transactions):
            try:
                result = await self.categorize_transaction(transaction)
                categorized.append(result)
                
                if (i + 1) % batch_size == 0:
                    logger.info(f"Processed {i + 1}/{len(transactions)} transactions")
                    
            except Exception as e:
                logger.error(f"Error processing transaction {i}: {str(e)}")
                categorized.append(self._get_default_categorization(transaction))
        
        logger.info(f"Completed categorization of {len(categorized)} transactions")
        return categorized
