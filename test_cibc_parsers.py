#!/usr/bin/env python3
"""
Test script for CIBC parsers.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from parsers.cibc_investorsedge_parser import CIBCInvestorsEdgeParser
from parsers.cibc_pps_parser import CIBCPPSParser


def test_parser(parser_class, pdf_path, description):
    """Test a parser with a given PDF file."""
    print(f"\n{'=' * 80}")
    print(f"Testing: {description}")
    print(f"File: {pdf_path}")
    print('=' * 80)

    try:
        parser = parser_class(pdf_path)
        data = parser.parse()

        print(f"\nInstitution: {data.get('institution')}")
        print(f"Account Number: {data.get('account_number')}")
        print(f"Account Type: {data.get('account_type')}")
        print(f"Statement Date: {data.get('statement_date')}")
        print(f"Period Start: {data.get('period_start')}")
        print(f"Period End: {data.get('period_end')}")
        print(f"Total Value: ${data.get('total_value'):,.2f}" if data.get('total_value') else "Total Value: None")
        print(f"Cash Balance: ${data.get('cash_balance'):,.2f}" if data.get('cash_balance') else "Cash Balance: None")
        print(f"\nNumber of Holdings: {len(data.get('holdings', []))}")

        if data.get('holdings'):
            print("\nFirst 5 Holdings:")
            for i, holding in enumerate(data['holdings'][:5], 1):
                print(f"\n  {i}. {holding['security_name']}")
                print(f"     Quantity: {holding['quantity']:,.4f}")
                print(f"     Price: ${holding['price']:,.4f}")
                print(f"     Market Value: ${holding['market_value']:,.2f}")
                print(f"     Asset Type: {holding['asset_type']}")
                print(f"     Asset Category: {holding['asset_category']}")

        print("\n✓ SUCCESS\n")
        return True

    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run tests on CIBC statement files."""

    statements_dir = Path('statements/CIBC')

    if not statements_dir.exists():
        print(f"Error: {statements_dir} does not exist!")
        sys.exit(1)

    tests = [
        # Investor's Edge Self-Directed RRSP
        (CIBCInvestorsEdgeParser,
         statements_dir / 'CIBC-RRSP-Self-2025_10_eStatements.pdf',
         'CIBC Investor\'s Edge Self-Directed RRSP (October 2025)'),

        # Investor's Edge Self-Directed TFSA
        (CIBCInvestorsEdgeParser,
         statements_dir / 'CIBC-TFSA-Self-2025_10_eStatements.pdf',
         'CIBC Investor\'s Edge Self-Directed TFSA (October 2025)'),

        # Investor's Edge Non-Registered
        (CIBCInvestorsEdgeParser,
         statements_dir / 'CIBC-Investors-Edge-2025_10_eStatements.pdf',
         'CIBC Investor\'s Edge Non-Registered (October 2025)'),

        # PPS Bank-Managed RRSP
        (CIBCPPSParser,
         statements_dir / 'CIBC-RRSP-PPS-2025-09-30.pdf',
         'CIBC Personal Portfolio Services RRSP (September 2025)'),
    ]

    results = []
    for parser_class, pdf_path, description in tests:
        if pdf_path.exists():
            success = test_parser(parser_class, str(pdf_path), description)
            results.append((description, success))
        else:
            print(f"\n✗ SKIPPED: {description} - File not found: {pdf_path}")
            results.append((description, False))

    # Summary
    print(f"\n{'=' * 80}")
    print("TEST SUMMARY")
    print('=' * 80)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for description, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {description}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print('=' * 80)

    return 0 if passed == total else 1


if __name__ == '__main__':
    sys.exit(main())
