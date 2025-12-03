"""
Parser for CIBC Personal Portfolio Services (PPS) financial statements.
Handles bank-managed investment accounts (RRSP, TFSA, etc.).
"""

import re
import pdfplumber
from datetime import datetime
from typing import Dict, List
from parsers.base_parser import BaseStatementParser


class CIBCPPSParser(BaseStatementParser):
    """Parser for CIBC Personal Portfolio Services (PPS) PDF statements."""

    def __init__(self, pdf_path: str):
        super().__init__(pdf_path)
        self.statement_data['institution'] = 'CIBC'

    def parse(self) -> Dict:
        """Parse the CIBC PPS PDF statement."""
        with pdfplumber.open(self.pdf_path) as pdf:
            full_text = ''
            for page in pdf.pages:
                full_text += page.extract_text() + '\n'

        self.extract_account_info(full_text)
        self.extract_holdings(full_text)

        return self.statement_data

    def extract_account_info(self, text: str) -> None:
        """Extract account information from CIBC PPS statement."""
        # Extract account number - format: "Account Number: 2595031"
        account_match = re.search(r'Account\s+Number:\s*(\d+)', text, re.IGNORECASE)
        if account_match:
            self.statement_data['account_number'] = account_match.group(1)

        # Extract account type - format: "Account Type: RRSP"
        acct_type_match = re.search(r'Account\s+Type:\s*([^\n]+)', text, re.IGNORECASE)
        if acct_type_match:
            account_type = acct_type_match.group(1).strip()
            self.statement_data['account_type'] = account_type

        # Extract statement date - format: "For the period ending: September 30, 2025"
        date_match = re.search(
            r'For\s+the\s+period\s+ending:\s*([A-Za-z]+)\s+(\d+),\s+(\d{4})',
            text,
            re.IGNORECASE
        )
        if date_match:
            month = date_match.group(1)
            day = date_match.group(2)
            year = date_match.group(3)
            date_str = f'{month} {day}, {year}'
            self.statement_data['statement_date'] = self.parse_date(date_str)
            self.statement_data['period_end'] = self.statement_data['statement_date']

        # Extract ending account value - format: "Ending Account Value 270,341.06"
        value_match = re.search(r'Ending\s+Account\s+Value\s+([\d,]+\.\d+)', text, re.IGNORECASE)
        if value_match:
            self.statement_data['total_value'] = self.clean_currency_value(value_match.group(1))

        # Extract cash balance from holdings section if present
        cash_match = re.search(
            r'Cash\s+and\s+Cash\s+Equivalents\s+Total\s+Cash.*?\s+([\d,]+\.\d+)\s+([\d,]+\.\d+)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if cash_match:
            self.statement_data['cash_balance'] = self.clean_currency_value(cash_match.group(2))
        else:
            # If no cash holdings found, set to 0
            self.statement_data['cash_balance'] = 0.0

    def extract_holdings(self, text: str) -> List[Dict]:
        """Extract holdings from CIBC PPS statement."""
        holdings = []

        # Find the Account Holdings section
        # Format: "Y O U R  A C C O U N T  H O L D I N G S" (with spaces between letters)
        # Columns: Number of Units | Description | Book Cost ($) | Price on Date | Value on Date
        holdings_match = re.search(
            r'Y\s+O\s+U\s+R\s+A\s+C\s+C\s+O\s+U\s+N\s+T\s+H\s+O\s+L\s+D\s+I\s+N\s+G\s+S.*?'
            r'Number.*?Description.*?'
            r'(.*?)(?:Total\s+Account|Holdings|\*\d+\*)',
            text,
            re.DOTALL | re.IGNORECASE
        )

        if not holdings_match:
            return holdings

        holdings_text = holdings_match.group(1)
        current_category = None
        lines = holdings_text.strip().split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines
            if not line:
                i += 1
                continue

            # Skip Total lines
            if line.startswith('Total '):
                i += 1
                continue

            # Check for lines that start with a category and contain holdings data
            # Format: "Canadian Short-Term 2214.7673 Imperial Short-Term Bond Pool 22,157.41 10.0983 22,365.38"
            # or just category: "Fixed Income"
            category_with_data_match = re.match(
                r'^(Cash and Cash Equivalents|Fixed Income|Canadian Short-Term Bonds?|Canadian Bonds?|'
                r'Canadian Long-Term Bonds?|Equities|Canadian Equities|U\.S\. Equities|'
                r'International and Global Equities)\s+'
                r'([\d,]+\.\d+)\s+(.+?)\s+([\d,]+\.\d+)\s+([\d,]+\.\d+)\s+([\d,]+\.\d+)$',
                line,
                re.IGNORECASE
            )

            if category_with_data_match:
                # Category name followed by data on same line
                current_category = category_with_data_match.group(1)
                quantity = self.clean_currency_value(category_with_data_match.group(2))
                security_name = category_with_data_match.group(3).strip()
                book_value = self.clean_currency_value(category_with_data_match.group(4))
                price = self.clean_currency_value(category_with_data_match.group(5))
                market_value = self.clean_currency_value(category_with_data_match.group(6))

                if quantity and price and market_value:
                    classification = self.classify_security(security_name)

                    # Determine asset category based on section
                    asset_category = classification['asset_category']
                    if current_category:
                        if 'Equities' in current_category or 'Equity' in current_category:
                            asset_category = 'Equity'
                        elif 'Fixed Income' in current_category or 'Bond' in current_category:
                            asset_category = 'Fixed Income'
                        elif 'Cash' in current_category:
                            asset_category = 'Cash'

                    # Determine more specific asset type based on category and name
                    asset_type = classification['asset_type']
                    if 'Pool' in security_name:
                        if 'Bond' in security_name:
                            asset_type = 'Mutual Fund - Fixed Income'
                        elif 'Equity' in security_name or 'Dividend' in security_name:
                            asset_type = 'Mutual Fund - Equity'
                        else:
                            asset_type = 'Mutual Fund'

                    holding = {
                        'security_name': security_name,
                        'quantity': quantity,
                        'price': price,
                        'book_value': book_value,
                        'market_value': market_value,
                        'account_type': self.statement_data.get('account_type', 'RRSP'),
                        'asset_type': asset_type,
                        'asset_category': asset_category,
                        'currency': 'CAD'
                    }
                    holdings.append(holding)

                i += 1
                continue

            # Check for standalone category headers
            category_match = re.match(
                r'^(Cash and Cash Equivalents|Fixed Income|Canadian Short-Term Bonds?|Canadian Bonds?|'
                r'Canadian Long-Term Bonds?|Equities|Canadian Equities|U\.S\. Equities|'
                r'International and Global Equities)$',
                line,
                re.IGNORECASE
            )
            if category_match:
                current_category = category_match.group(1)
                i += 1
                continue

            # Parse holding entry without category prefix
            # Format: units security_name book_cost price value
            # Example: "2214.7673 Imperial Short-Term Bond Pool 22,157.41 10.0983 22,365.38"
            holding_match = re.match(
                r'^([\d,]+\.\d+)\s+(.+?)\s+([\d,]+\.\d+)\s+([\d,]+\.\d+)\s+([\d,]+\.\d+)$',
                line
            )

            if holding_match:
                quantity = self.clean_currency_value(holding_match.group(1))
                security_name = holding_match.group(2).strip()
                book_value = self.clean_currency_value(holding_match.group(3))
                price = self.clean_currency_value(holding_match.group(4))
                market_value = self.clean_currency_value(holding_match.group(5))

                if quantity and price and market_value:
                    classification = self.classify_security(security_name)

                    # Determine asset category based on section
                    asset_category = classification['asset_category']
                    if current_category:
                        if 'Equities' in current_category or 'Equity' in current_category:
                            asset_category = 'Equity'
                        elif 'Fixed Income' in current_category or 'Bond' in current_category:
                            asset_category = 'Fixed Income'
                        elif 'Cash' in current_category:
                            asset_category = 'Cash'

                    # Determine more specific asset type based on category and name
                    asset_type = classification['asset_type']
                    if 'Pool' in security_name:
                        if 'Bond' in security_name:
                            asset_type = 'Mutual Fund - Fixed Income'
                        elif 'Equity' in security_name or 'Dividend' in security_name:
                            asset_type = 'Mutual Fund - Equity'
                        else:
                            asset_type = 'Mutual Fund'

                    holding = {
                        'security_name': security_name,
                        'quantity': quantity,
                        'price': price,
                        'book_value': book_value,
                        'market_value': market_value,
                        'account_type': self.statement_data.get('account_type', 'RRSP'),
                        'asset_type': asset_type,
                        'asset_category': asset_category,
                        'currency': 'CAD'
                    }
                    holdings.append(holding)

            i += 1

        self.statement_data['holdings'] = holdings
        return holdings
