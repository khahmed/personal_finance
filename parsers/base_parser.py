"""
Base parser class for financial statement PDFs.
All institution-specific parsers inherit from this class.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional
import re


class BaseStatementParser(ABC):
    """Abstract base class for statement parsers."""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.statement_data = {
            'institution': None,
            'account_number': None,
            'account_type': None,
            'statement_date': None,
            'period_start': None,
            'period_end': None,
            'total_value': None,
            'cash_balance': None,
            'holdings': [],
            'performance': {}
        }

    @abstractmethod
    def parse(self) -> Dict:
        """Parse the PDF and extract holdings data."""
        pass

    @abstractmethod
    def extract_account_info(self, text: str) -> None:
        """Extract account information from the statement."""
        pass

    @abstractmethod
    def extract_holdings(self, text: str) -> List[Dict]:
        """Extract holdings data from the statement."""
        pass

    def clean_currency_value(self, value_str: str) -> Optional[float]:
        """
        Clean and convert currency strings to float.
        Handles formats like: $1,234.56, ($1,234.56), -$1,234.56
        """
        if not value_str or value_str.strip() == '':
            return None

        # Remove currency symbols, commas, and spaces
        cleaned = re.sub(r'[\$,\s]', '', value_str)

        # Handle parentheses for negative numbers
        if '(' in cleaned and ')' in cleaned:
            cleaned = '-' + cleaned.replace('(', '').replace(')', '')

        try:
            return float(cleaned)
        except ValueError:
            return None

    def parse_date(self, date_str: str, formats: List[str] = None) -> Optional[datetime]:
        """
        Parse date string into datetime object.
        Tries multiple date formats.
        """
        if not date_str:
            return None

        if formats is None:
            formats = [
                '%B %d, %Y',  # January 1, 2025
                '%b %d, %Y',  # Jan 1, 2025
                '%Y-%m-%d',   # 2025-01-01
                '%m/%d/%Y',   # 01/01/2025
                '%d/%m/%Y',   # 01/01/2025
                '%B %d to %B %d, %Y',  # January 1 to October 31, 2025
                '%Y-%m-%d - %Y-%m-%d'  # 2025-10-15 - 2025-10-15
            ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None

    def classify_security(self, security_name: str) -> Dict[str, str]:
        """
        Classify a security based on its name.
        Returns asset type and category.
        """
        security_lower = security_name.lower()

        # GIC and bank deposit detection (must come before other checks)
        # These are fixed income instruments issued by banks
        if ('bank' in security_lower or 'trust company' in security_lower or
            'trust co' in security_lower or 'gic' in security_lower or
            'guaranteed investment' in security_lower):
            return {
                'asset_type': 'GIC',
                'asset_category': 'Fixed Income'
            }

        # ETF detection
        if 'etf' in security_lower:
            category = 'Equity'
            if 'bond' in security_lower or 'fixed income' in security_lower:
                category = 'Fixed Income'
            return {
                'asset_type': 'ETF',
                'asset_category': category
            }

        # Index fund detection
        if 'index' in security_lower:
            if 'bond' in security_lower or 'fixed income' in security_lower:
                return {
                    'asset_type': 'Index Fund - Fixed Income',
                    'asset_category': 'Fixed Income'
                }
            elif 'balanced' in security_lower:
                return {
                    'asset_type': 'Index Fund - Balanced',
                    'asset_category': 'Balanced'
                }
            elif 'cdn' in security_lower or 'canadian' in security_lower:
                return {
                    'asset_type': 'Index Fund - Canadian Equity',
                    'asset_category': 'Equity'
                }
            elif 'u.s' in security_lower or 'us ' in security_lower or 'american' in security_lower:
                return {
                    'asset_type': 'Index Fund - US Equity',
                    'asset_category': 'Equity'
                }
            elif 'intl' in security_lower or 'international' in security_lower:
                return {
                    'asset_type': 'Index Fund - International Equity',
                    'asset_category': 'Equity'
                }
            elif 'global' in security_lower:
                return {
                    'asset_type': 'Index Fund - Global Equity',
                    'asset_category': 'Equity'
                }
            else:
                return {
                    'asset_type': 'ETF',
                    'asset_category': 'Equity'
                }

        # Balanced fund detection
        if 'balanced' in security_lower or 'asset allocation' in security_lower:
            return {
                'asset_type': 'Mutual Fund - Balanced',
                'asset_category': 'Balanced'
            }

        # Fixed income detection
        if ('bond' in security_lower or 'fixed income' in security_lower or
            'fixedincome' in security_lower or 'income fund' in security_lower):
            return {
                'asset_type': 'Mutual Fund - Fixed Income',
                'asset_category': 'Fixed Income'
            }

        # Equity fund detection
        if 'equity' in security_lower or 'stock' in security_lower:
            return {
                'asset_type': 'Mutual Fund - Equity',
                'asset_category': 'Equity'
            }

        # Exempt market / private securities
        if 'exempt' in security_lower or 'private' in security_lower:
            return {
                'asset_type': 'Exempt Market Security',
                'asset_category': 'Alternative'
            }

        # Default to equity if unsure
        return {
            'asset_type': 'Stock',
            'asset_category': 'Equity'
        }

    def get_statement_data(self) -> Dict:
        """Return the parsed statement data."""
        return self.statement_data
