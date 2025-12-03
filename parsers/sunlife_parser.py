"""
Parser for SunLife financial statements.
"""

import re
import pdfplumber
from datetime import datetime
from typing import Dict, List
from parsers.base_parser import BaseStatementParser


class SunLifeParser(BaseStatementParser):
    """Parser for SunLife PDF statements."""

    def __init__(self, pdf_path: str):
        super().__init__(pdf_path)
        self.statement_data['institution'] = 'SunLife'

    def parse(self) -> Dict:
        """Parse the SunLife PDF statement."""
        with pdfplumber.open(self.pdf_path) as pdf:
            full_text = ''
            for page in pdf.pages:
                full_text += page.extract_text() + '\n'

        self.extract_account_info(full_text)
        self.extract_holdings(full_text)
        self.extract_performance(full_text)

        return self.statement_data

    def extract_account_info(self, text: str) -> None:
        """Extract account information from SunLife statement."""
        # Extract account number
        account_match = re.search(r'Account number:\s*(\d+)', text)
        if account_match:
            self.statement_data['account_number'] = account_match.group(1)

        # Determine account type(s) - SunLife statements can have multiple account types
        # Priority: RRSP > LIRA > Group Plan
        if re.search(r'Registered Retirement Savings Plan \(RRSP\)', text):
            self.statement_data['account_type'] = 'RRSP'
        elif re.search(r'Locked-in Retirement Account \(LIRA\)', text):
            self.statement_data['account_type'] = 'LIRA'
        elif re.search(r'Group Choices Plan', text):
            self.statement_data['account_type'] = 'Group Plan'
        else:
            # Default fallback
            self.statement_data['account_type'] = 'Group Plan'

        # Extract statement period
        period_match = re.search(r'For the period\s+(\w+ \d+)\s+to\s+(\w+ \d+,\s*\d{4})', text)
        if period_match:
            period_start_str = period_match.group(1)
            period_end_str = period_match.group(2)

            # Extract year from end date
            year_match = re.search(r'\d{4}', period_end_str)
            if year_match:
                year = year_match.group(0)
                period_start_str += f', {year}'

            self.statement_data['period_start'] = self.parse_date(period_start_str)
            self.statement_data['period_end'] = self.parse_date(period_end_str)
            self.statement_data['statement_date'] = self.statement_data['period_end']

        # Extract total value
        total_value_match = re.search(r'Value of my plans on \w+ \d+, \d{4}\s*\.+\s*\$?([\d,]+\.?\d*)', text)
        if total_value_match:
            self.statement_data['total_value'] = self.clean_currency_value(total_value_match.group(1))

    def extract_holdings(self, text: str) -> List[Dict]:
        """Extract holdings from SunLife statement."""
        holdings = []

        # Find RRSP holdings
        # Pattern: My investments section followed by holdings until "Total investments"
        rrsp_match = re.search(
            r'My Registered Retirement Savings Plan \(RRSP\).*?My investments.*?INVESTMENT NAME.*?\n(.*?)(?:Total investments|\Z)',
            text, re.DOTALL
        )
        if rrsp_match:
            rrsp_holdings = self._parse_holdings_section(rrsp_match.group(1), 'RRSP')
            holdings.extend(rrsp_holdings)

        # Find LIRA holdings
        lira_match = re.search(
            r'My Locked-in Retirement Account \(LIRA\).*?My investments.*?INVESTMENT NAME.*?\n(.*?)(?:Total investments|\Z)',
            text, re.DOTALL
        )
        if lira_match:
            lira_holdings = self._parse_holdings_section(lira_match.group(1), 'LIRA')
            holdings.extend(lira_holdings)

        self.statement_data['holdings'] = holdings
        return holdings

    def _parse_holdings_section(self, section_text: str, account_type: str) -> List[Dict]:
        """Parse a holdings section from SunLife statement."""
        holdings = []
        current_category = None

        lines = section_text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if this is a category line
            if any(cat in line for cat in ['Foreign/global equity', 'Balanced', 'Fixed income',
                                           'Canadian equity', 'U.S. equity', 'International equity']):
                current_category = line
                continue

            # Parse holding line
            # Format: SECURITY_NAME units price value
            match = re.match(
                r'^(.+?)\s+([\d,]+\.?\d*)\s+\$?([\d,]+\.?\d*)\s+\$?([\d,]+\.?\d*)$',
                line
            )
            if match:
                security_name = match.group(1).strip()
                units = self.clean_currency_value(match.group(2))
                price = self.clean_currency_value(match.group(3))
                value = self.clean_currency_value(match.group(4))

                if units and price and value:
                    classification = self.classify_security(security_name)

                    holding = {
                        'security_name': security_name,
                        'quantity': units,
                        'price': price,
                        'market_value': value,
                        'account_type': account_type,
                        'asset_type': classification['asset_type'],
                        'asset_category': classification['asset_category'],
                        'currency': 'CAD'
                    }
                    holdings.append(holding)

        return holdings

    def extract_performance(self, text: str) -> None:
        """Extract performance data from SunLife statement."""
        # Extract RRSP performance
        rrsp_perf_match = re.search(
            r'Personal rates of return for my Registered Retirement Savings\s*Plan.*?'
            r'3 MONTH\s+YEAR-TO-DATE\s+1 YEAR\s+3 YEAR\s+5 YEAR.*?'
            r'([\d.]+)%\s+([\d.]+)%\s+([\d.]+)%\s+([\d.]+)%\s+[-\d.]+\s+([\d.]+)%',
            text, re.DOTALL
        )

        if rrsp_perf_match:
            self.statement_data['performance']['rrsp'] = {
                '3m': float(rrsp_perf_match.group(1)),
                'ytd': float(rrsp_perf_match.group(2)),
                '1y': float(rrsp_perf_match.group(3)),
                '3y': float(rrsp_perf_match.group(4)),
                'inception': float(rrsp_perf_match.group(5))
            }

        # Extract LIRA performance
        lira_perf_match = re.search(
            r'Personal rates of return for my Locked-in Retirement Account.*?'
            r'3 MONTH\s+YEAR-TO-DATE\s+1 YEAR\s+3 YEAR\s+5 YEAR.*?'
            r'([\d.]+)%\s+([\d.]+)%\s+([\d.]+)%\s+([\d.]+)%\s+[-\d.]+\s+([\d.]+)%',
            text, re.DOTALL
        )

        if lira_perf_match:
            self.statement_data['performance']['lira'] = {
                '3m': float(lira_perf_match.group(1)),
                'ytd': float(lira_perf_match.group(2)),
                '1y': float(lira_perf_match.group(3)),
                '3y': float(lira_perf_match.group(4)),
                'inception': float(lira_perf_match.group(5))
            }
