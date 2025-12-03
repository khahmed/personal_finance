"""
Parser for ScotiaBank (ScotiaMcLeod) financial statements.
"""

import re
import pdfplumber
from datetime import datetime
from typing import Dict, List
from parsers.base_parser import BaseStatementParser


class ScotiaBankParser(BaseStatementParser):
    """Parser for ScotiaBank (ScotiaMcLeod) PDF statements."""

    def __init__(self, pdf_path: str):
        super().__init__(pdf_path)
        self.statement_data['institution'] = 'ScotiaBank'

    def parse(self) -> Dict:
        """Parse the ScotiaBank PDF statement."""
        with pdfplumber.open(self.pdf_path) as pdf:
            full_text = ''
            for page in pdf.pages:
                full_text += page.extract_text() + '\n'

        self.extract_account_info(full_text)
        self.extract_holdings(full_text)

        return self.statement_data

    def extract_account_info(self, text: str) -> None:
        """Extract account information from ScotiaBank statement."""
        # Extract account number - handle both spaced and non-spaced formats
        account_match = re.search(r'Account\s*Number:\s*(\d+-\d+-\d+)', text, re.IGNORECASE)
        if not account_match:
            account_match = re.search(r'AccountNumber:\s*(\d+-\d+-\d+)', text)
        if not account_match:
            # Try confirmation notice format
            account_match = re.search(r'ACCOUNT\s*NO\.\s*(\d+[−\-]\d+[−\-]?\d*)', text)
        if account_match:
            # Normalize hyphens (replace − with -)
            account_number = account_match.group(1).replace('−', '-')
            self.statement_data['account_number'] = account_number

        # Extract account type - handle both spaced and non-spaced formats
        acct_type_match = re.search(r'Account\s*Type:\s*([^\n]+)', text, re.IGNORECASE)
        if not acct_type_match:
            acct_type_match = re.search(r'AccountType:\s*([^\n]+)', text)
        if not acct_type_match:
            # Try confirmation notice format with account number line
            # Format: "487−8150012 GRSP" or "487−8150012−GRSP"
            acct_type_match = re.search(r'ACCOUNT\s*NO\.\s*\d+[−\-]\d+(?:[−\-]\d+)?[−\s]*(GRSP|RRSP|TFSA)', text)
        if acct_type_match:
            account_type = acct_type_match.group(1).strip()
            # Normalize account type names
            type_mapping = {
                'RegisteredRetirementSavingsPlan': 'RRSP',
                'Tax-FreeSavingsAccount': 'TFSA',
                'GRSP': 'RRSP'
            }
            self.statement_data['account_type'] = type_mapping.get(account_type, account_type)

        # Extract statement period - handle both spaced and non-spaced formats
        period_match = re.search(r'For\s*the\s*Period:\s*(\w+)\s*(\d+)\s*to\s*(\d+),\s*(\d{4})', text, re.IGNORECASE)
        if not period_match:
            period_match = re.search(r'ForthePeriod:\s*(\w+)(\d+)to(\d+),(\d{4})', text)
        if not period_match:
            # Try confirmation notice format: "OCTOBER 6, 2025"
            conf_date_match = re.search(r'([A-Z]+)\s+(\d+),\s+(\d{4})', text)
            if conf_date_match:
                month = conf_date_match.group(1)
                day = conf_date_match.group(2)
                year = conf_date_match.group(3)
                date_str = f'{month} {day}, {year}'
                self.statement_data['statement_date'] = self.parse_date(date_str)

        if period_match:
            month = period_match.group(1)
            start_day = period_match.group(2)
            end_day = period_match.group(3)
            year = period_match.group(4)

            start_date_str = f'{month} {start_day}, {year}'
            end_date_str = f'{month} {end_day}, {year}'

            self.statement_data['period_start'] = self.parse_date(start_date_str)
            self.statement_data['period_end'] = self.parse_date(end_date_str)
            self.statement_data['statement_date'] = self.statement_data['period_end']

        # Extract total account value
        total_value_match = re.search(r'Total Value of Account\s+\$?([\d,]+\.?\d*)', text)
        if total_value_match:
            self.statement_data['total_value'] = self.clean_currency_value(total_value_match.group(1))

        # Extract cash balance
        cash_match = re.search(r'^Cash\s+\$?([\d,]+\.?\d*)$', text, re.MULTILINE)
        if cash_match:
            self.statement_data['cash_balance'] = self.clean_currency_value(cash_match.group(1))

    def extract_holdings(self, text: str) -> List[Dict]:
        """Extract holdings from ScotiaBank statement."""
        holdings = []

        # Find the holdings section - handle both spaced and non-spaced formats
        holdings_match = re.search(
            r'Details of Your Account Holdings.*?Security.*?Description.*?Quantity.*?(.*?)(?:Total Account Holdings|\Z)',
            text, re.DOTALL
        )

        if not holdings_match:
            return holdings

        holdings_text = holdings_match.group(1)
        current_category = 'Cash'

        lines = holdings_text.strip().split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines
            if not line:
                i += 1
                continue

            # Check for category headers
            if line in ['Cash', 'Fixed Income', 'Equity', 'Multi-Asset']:
                current_category = line
                i += 1
                continue

            # Skip subtotal lines
            if 'Subtotal' in line or 'Total' in line or 'Pending' in line:
                i += 1
                continue

            # Check if this line starts a security entry
            # ScotiaBank format can have security name on one line, then data on the next
            if not any(c.isdigit() for c in line):
                # This might be a security name
                security_name = line.strip()

                # Check if next line has the numbers
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    numbers_match = re.match(
                        r'^([\d,]+\.?\d*)\s+([\d.]+)\s+([\d,]+\.?\d*)\s+([\d.]+)\s+([\d,]+\.?\d*)$',
                        next_line
                    )

                    if numbers_match:
                        quantity = self.clean_currency_value(numbers_match.group(1))
                        avg_cost = self.clean_currency_value(numbers_match.group(2))
                        book_value = self.clean_currency_value(numbers_match.group(3))
                        price = self.clean_currency_value(numbers_match.group(4))
                        market_value = self.clean_currency_value(numbers_match.group(5))

                        if quantity and price and market_value:
                            classification = self.classify_security(security_name)

                            # Use classification category, but validate against section if available
                            asset_category = classification['asset_category']
                            # Only override if current_category is more specific and classification is generic
                            if current_category != 'Cash' and classification['asset_category'] == 'Equity' and current_category in ['Fixed Income', 'Multi-Asset']:
                                asset_category = current_category

                            holding = {
                                'security_name': security_name,
                                'quantity': quantity,
                                'price': price,
                                'book_value': book_value,
                                'market_value': market_value,
                                'account_type': self.statement_data.get('account_type', 'RRSP'),
                                'asset_type': classification['asset_type'],
                                'asset_category': asset_category,
                                'currency': 'CAD'
                            }
                            holdings.append(holding)

                        i += 2  # Skip the next line since we processed it
                        continue

            # Try to parse as single-line entry
            # Format: SECURITY_NAME quantity avg_cost book_value price market_value
            single_line_match = re.match(
                r'^(.+?)\s+([\d,]+\.?\d*)\s+([\d.]+)\s+([\d,]+\.?\d*)\s+([\d.]+)\s+([\d,]+\.?\d*)$',
                line
            )

            if single_line_match:
                security_name = single_line_match.group(1).strip()
                quantity = self.clean_currency_value(single_line_match.group(2))
                book_value = self.clean_currency_value(single_line_match.group(4))
                price = self.clean_currency_value(single_line_match.group(5))
                market_value = self.clean_currency_value(single_line_match.group(6))

                if quantity and price and market_value:
                    classification = self.classify_security(security_name)

                    # Use classification category, but validate against section if available
                    asset_category = classification['asset_category']
                    # Only override if current_category is more specific and classification is generic
                    if current_category != 'Cash' and classification['asset_category'] == 'Equity' and current_category in ['Fixed Income', 'Multi-Asset']:
                        asset_category = current_category

                    holding = {
                        'security_name': security_name,
                        'quantity': quantity,
                        'price': price,
                        'book_value': book_value,
                        'market_value': market_value,
                        'account_type': self.statement_data.get('account_type', 'RRSP'),
                        'asset_type': classification['asset_type'],
                        'asset_category': asset_category,
                        'currency': 'CAD'
                    }
                    holdings.append(holding)

            i += 1

        self.statement_data['holdings'] = holdings
        return holdings
