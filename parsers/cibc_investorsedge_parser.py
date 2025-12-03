"""
Parser for CIBC Investor's Edge Self-Directed financial statements.
Handles RRSP, TFSA, and non-registered investment accounts.
"""

import re
import pdfplumber
from datetime import datetime
from typing import Dict, List
from parsers.base_parser import BaseStatementParser


class CIBCInvestorsEdgeParser(BaseStatementParser):
    """Parser for CIBC Investor's Edge Self-Directed PDF statements."""

    def __init__(self, pdf_path: str):
        super().__init__(pdf_path)
        self.statement_data['institution'] = 'CIBC'

    def parse(self) -> Dict:
        """Parse the CIBC Investor's Edge PDF statement."""
        with pdfplumber.open(self.pdf_path) as pdf:
            full_text = ''
            for page in pdf.pages:
                full_text += page.extract_text() + '\n'

        self.extract_account_info(full_text)
        self.extract_holdings(full_text)

        return self.statement_data

    def extract_account_info(self, text: str) -> None:
        """Extract account information from CIBC Investor's Edge statement."""
        # Extract account number - format: "Account # 596-30991"
        account_match = re.search(r'Account\s*#\s*(\d+-\d+)', text, re.IGNORECASE)
        if account_match:
            self.statement_data['account_number'] = account_match.group(1)

        # Extract account type from the title
        # "Investor's Edge Self-Directed Registered Retirement Savings Plan"
        # "Investor's Edge Self-Directed Tax Free Savings Account"
        # "Investor's Edge Investment Account" (non-registered)
        if 'Registered Retirement Savings Plan' in text:
            self.statement_data['account_type'] = 'RRSP'
        elif 'Tax Free Savings Account' in text:
            self.statement_data['account_type'] = 'TFSA'
        elif 'Investment Account' in text and 'Investor\'s Edge' in text:
            self.statement_data['account_type'] = 'Non-Registered'

        # Extract statement period - format: "October 1-October 31, 2025"
        period_match = re.search(
            r'([A-Za-z]+)\s+(\d+)-([A-Za-z]+)\s+(\d+),\s+(\d{4})',
            text
        )
        if period_match:
            start_month = period_match.group(1)
            start_day = period_match.group(2)
            end_month = period_match.group(3)
            end_day = period_match.group(4)
            year = period_match.group(5)

            start_date_str = f'{start_month} {start_day}, {year}'
            end_date_str = f'{end_month} {end_day}, {year}'

            self.statement_data['period_start'] = self.parse_date(start_date_str)
            self.statement_data['period_end'] = self.parse_date(end_date_str)
            self.statement_data['statement_date'] = self.statement_data['period_end']

        # Extract total portfolio value - format: "total portfolio 100% $114,324.32"
        total_match = re.search(r'total\s+portfolio\s+\d+%\s+\$?([\d,]+\.?\d*)', text, re.IGNORECASE)
        if total_match:
            self.statement_data['total_value'] = self.clean_currency_value(total_match.group(1))

        # Extract cash balance - format: "Cash & Cash Equivalents 18% $20,224.15"
        cash_match = re.search(
            r'Cash\s*&\s*Cash\s+Equivalents\s+\d+%\s+\$?([\d,]+\.?\d*)',
            text,
            re.IGNORECASE
        )
        if cash_match:
            self.statement_data['cash_balance'] = self.clean_currency_value(cash_match.group(1))

    def extract_holdings(self, text: str) -> List[Dict]:
        """Extract holdings from CIBC Investor's Edge statement."""
        holdings = []

        # Find the Portfolio Assets section
        # Format has multiple sections: Cash & Cash Equivalents, Equities, Mutual Funds
        # Can also have separate currency sections (Canadian Dollars, U.S. Dollars)
        portfolio_match = re.search(
            r'Portfolio Assets.*?description\s+quantity\s+book\s+value\s+current\s+market\s+value.*?'
            r'(.*?)(?:Messages|Disclosures|total portfolio in)',
            text,
            re.DOTALL | re.IGNORECASE
        )

        if not portfolio_match:
            return holdings

        portfolio_text = portfolio_match.group(1)
        current_category = None
        current_currency = 'CAD'  # Default to CAD
        lines = portfolio_text.strip().split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines
            if not line:
                i += 1
                continue

            # Check for currency section headers
            # Format: "Portfolio Assets — U.S. Dollars" or "subtotal for Canadian Dollars"
            if re.search(r'U\.?S\.?\s+Dollars|Portfolio Assets.*U\.S\. Dollars', line, re.IGNORECASE):
                current_currency = 'USD'
                i += 1
                continue
            elif re.search(r'Canadian Dollars', line, re.IGNORECASE):
                current_currency = 'CAD'
                # Don't skip this line as it might be a subtotal line that should be processed below

            # Check for category headers
            if re.match(r'^(Cash & Cash Equivalents|Equities|Mutual Funds|Fixed Income)$', line, re.IGNORECASE):
                current_category = line
                i += 1
                continue

            # Skip subtotal and total lines
            if 'subtotal' in line.lower() or line.startswith('total portfolio'):
                i += 1
                continue

            # Skip column headers and page headers
            if 'description' in line.lower() and 'quantity' in line.lower():
                i += 1
                continue
            if 'Investor\'s Edge' in line or 'Account #' in line:
                i += 1
                continue

            # Parse holding entry
            # Format: SECURITY_NAME quantity book_value price market_value segregation
            # Example: "TELUS CORPORATION 400 $9,074.20 20.510 $8,204.00 400"
            # For transferred securities: "SECURITY_NAME quantity $book_value ƒ price $market_value segregation"
            # Example: "INTERNATIONAL BUSINESS 737 $99,988.79 ƒ 307.410 $226,561.17 737"
            # or multi-line where security name is separate

            # Try to match a complete holding line with all data
            # The ƒ? makes the 'ƒ' character optional
            holding_match = re.match(
                r'^(.+?)\s+([\d,]+(?:\.\d+)?)\s+\$?([\d,]+\.\d+)\s+ƒ?\s*([\d,]+\.\d+)\s+\$?([\d,]+\.\d+)\s*(\d+)?',
                line
            )

            if holding_match:
                security_name = holding_match.group(1).strip()
                quantity = self.clean_currency_value(holding_match.group(2))
                book_value = self.clean_currency_value(holding_match.group(3))
                price = self.clean_currency_value(holding_match.group(4))
                market_value = self.clean_currency_value(holding_match.group(5))

                if quantity and price and market_value:
                    classification = self.classify_security(security_name)

                    # Use classification category, but validate against section if available
                    asset_category = classification['asset_category']
                    # Only override if current_category is more specific and classification is generic
                    if current_category:
                        if 'Fixed Income' in current_category and classification['asset_category'] != 'Fixed Income':
                            asset_category = 'Fixed Income'
                        elif 'Equities' in current_category and classification['asset_category'] == 'Fixed Income':
                            # Trust classification over section for Fixed Income (e.g., GICs)
                            asset_category = classification['asset_category']
                        elif 'Equities' in current_category and classification['asset_category'] not in ['Fixed Income', 'Balanced']:
                            asset_category = 'Equity'

                    holding = {
                        'security_name': security_name,
                        'quantity': quantity,
                        'price': price,
                        'book_value': book_value,
                        'market_value': market_value,
                        'account_type': self.statement_data.get('account_type', 'RRSP'),
                        'asset_type': classification['asset_type'],
                        'asset_category': asset_category,
                        'currency': current_currency
                    }
                    holdings.append(holding)

            i += 1

        self.statement_data['holdings'] = holdings
        return holdings
