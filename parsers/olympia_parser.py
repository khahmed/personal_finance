"""
Parser for Olympia Trust Company financial statements.
"""

import re
import pdfplumber
from datetime import datetime
from typing import Dict, List
from parsers.base_parser import BaseStatementParser


class OlympiaParser(BaseStatementParser):
    """Parser for Olympia Trust Company PDF statements."""

    def __init__(self, pdf_path: str):
        super().__init__(pdf_path)
        self.statement_data['institution'] = 'Olympia'

    def parse(self) -> Dict:
        """Parse the Olympia PDF statement."""
        with pdfplumber.open(self.pdf_path) as pdf:
            full_text = ''
            for page in pdf.pages:
                full_text += page.extract_text() + '\n'

        self.extract_account_info(full_text)
        self.extract_cash_balance(full_text)
        self.extract_holdings(full_text)

        return self.statement_data

    def extract_account_info(self, text: str) -> None:
        """Extract account information from Olympia statement."""
        # Extract account number and type
        # Format: "Statement of Account RRSP - Self-Directed #262412"
        account_match = re.search(r'Statement of Account\s+([A-Z][A-Za-z\s-]+?)\s+#(\d+)', text)

        if account_match:
            account_type = account_match.group(1).strip()
            account_number = account_match.group(2)
            self.statement_data['account_type'] = account_type
            self.statement_data['account_number'] = account_number

        # Extract statement period
        period_match = re.search(r'(\w+ \d+, \d{4})\s+To\s+(\w+ \d+, \d{4})', text)
        if period_match:
            self.statement_data['period_start'] = self.parse_date(period_match.group(1))
            self.statement_data['period_end'] = self.parse_date(period_match.group(2))
            self.statement_data['statement_date'] = self.statement_data['period_end']

        # Extract total plan value
        total_value_match = re.search(r'Total Plan Value:\s+\$?([\d,]+\.?\d*)', text)
        if total_value_match:
            self.statement_data['total_value'] = self.clean_currency_value(total_value_match.group(1))

    def extract_cash_balance(self, text: str) -> None:
        """Extract cash balance from Olympia statement."""
        # Look for Total Cash Balance in CAD section
        cash_match = re.search(r'Total Cash Balance:\s+\$?([\d,]+\.?\d*)', text)
        if cash_match:
            self.statement_data['cash_balance'] = self.clean_currency_value(cash_match.group(1))

    def extract_holdings(self, text: str) -> List[Dict]:
        """Extract holdings from Olympia statement."""
        holdings = []

        # Find the SECURITIES HELD section
        securities_match = re.search(
            r'SECURITIES HELD \(CAD\)(.*?)Total Securities:',
            text, re.DOTALL
        )

        if not securities_match:
            return holdings

        securities_text = securities_match.group(1)

        # Look for the exempt market securities subsection
        # Match everything after "EXEMPT MARKET SECURITIES" header
        exempt_match = re.search(
            r'EXEMPT MARKET SECURITIES\s*\n(.*)',
            securities_text, re.DOTALL
        )

        if exempt_match:
            exempt_text = exempt_match.group(1).strip()
            lines = exempt_text.split('\n')

            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if not line or 'Item Description' in line or 'Units' in line:
                    i += 1
                    continue

                # Parse format: units SECURITY_NAME book_value price market_value
                # Security name may span multiple lines
                match = re.match(
                    r'^([\d,]+\.?\d*)\s+(.+?)\s+\$?([\d,]+\.?\d*)\s+\$?([\d.]+)\s+\$?([\d,]+\.?\d*)$',
                    line
                )

                if match:
                    units = self.clean_currency_value(match.group(1))
                    security_name = match.group(2).strip()
                    book_value = self.clean_currency_value(match.group(3))
                    price = self.clean_currency_value(match.group(4))
                    market_value = self.clean_currency_value(match.group(5))

                    # Check if the next line is a continuation of the security name
                    # (doesn't start with a number and doesn't have $ values)
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and not re.match(r'^\d', next_line) and '$' not in next_line:
                            security_name += ' ' + next_line
                            i += 1  # Skip the next line since we've processed it

                    if units and security_name and market_value:
                        holding = {
                            'security_name': security_name,
                            'quantity': units,
                            'price': price,
                            'book_value': book_value,
                            'market_value': market_value,
                            'account_type': self.statement_data.get('account_type', 'RRSP'),
                            'asset_type': 'Exempt Market Security',
                            'asset_category': 'Alternative',
                            'currency': 'CAD'
                        }
                        holdings.append(holding)

                i += 1

        self.statement_data['holdings'] = holdings
        return holdings
