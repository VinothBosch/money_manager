"""
Bank Statement Processor Package
AI-powered transaction categorization using Semantic Kernel
"""

__version__ = "1.0.0"
__author__ = "AI Assistant"

from .data_extractor import DataExtractor
from .categorizer import TransactionCategorizer
from .excel_exporter import ExcelExporter

__all__ = ['DataExtractor', 'TransactionCategorizer', 'ExcelExporter']
