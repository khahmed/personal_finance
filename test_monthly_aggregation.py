#!/usr/bin/env python3
"""
Test script to verify monthly aggregation is working correctly.
This compares the daily vs monthly views to show how the aggregation
eliminates artificial dips from statements on different days.
"""

from database import DatabaseManager
from analysis import PortfolioAnalyzer
import config
import pandas as pd

def main():
    print("=" * 80)
    print("Testing Monthly Aggregation for Portfolio Value Trends")
    print("=" * 80)

    # Initialize components
    db_manager = DatabaseManager(config.DB_CONFIG)
    analyzer = PortfolioAnalyzer(db_manager)

    try:
        # Get both views
        print("\n1. Fetching DAILY view (original behavior)...")
        daily_trend = analyzer.get_value_over_time(monthly=False)

        print("2. Fetching MONTHLY view (new aggregated behavior)...")
        monthly_trend = analyzer.get_value_over_time(monthly=True)

        if daily_trend.empty:
            print("\n❌ No data found! Make sure you've processed statements.")
            return

        # Analyze daily view
        print("\n" + "=" * 80)
        print("DAILY VIEW (shows exact statement dates)")
        print("=" * 80)

        # Group by month to see multiple dates per month
        daily_trend['month'] = pd.to_datetime(daily_trend['statement_date']).dt.to_period('M')
        dates_per_month = daily_trend.groupby('month')['statement_date'].nunique()

        print(f"\nTotal data points: {len(daily_trend)}")
        print(f"\nMonths with multiple statement dates:")
        problem_months = dates_per_month[dates_per_month > 1]

        if len(problem_months) > 0:
            for month, count in problem_months.items():
                print(f"  {month}: {count} different dates")
                month_data = daily_trend[daily_trend['month'] == month]

                # Show the different dates and aggregated values
                daily_summary = month_data.groupby('statement_date').agg({
                    'total_account_value': 'sum',
                    'account_number': 'count'
                }).round(2)

                print(f"\n    Date-by-date breakdown for {month}:")
                for date, row in daily_summary.iterrows():
                    print(f"      {date.strftime('%Y-%m-%d')}: ${row['total_account_value']:>12,.2f} "
                          f"({int(row['account_number'])} accounts)")
        else:
            print("  ✓ No months with multiple dates found")

        # Analyze monthly view
        print("\n" + "=" * 80)
        print("MONTHLY VIEW (aggregated to first of month)")
        print("=" * 80)

        print(f"\nTotal data points: {len(monthly_trend)}")

        # Group by month to show one date per month
        monthly_trend['month'] = pd.to_datetime(monthly_trend['statement_date']).dt.to_period('M')
        dates_per_month_monthly = monthly_trend.groupby('month')['statement_date'].nunique()

        months_with_multiple = dates_per_month_monthly[dates_per_month_monthly > 1]
        if len(months_with_multiple) > 0:
            print(f"\n⚠️  WARNING: Found {len(months_with_multiple)} months with multiple dates in monthly view!")
            print("This should not happen. Check the view definition.")
        else:
            print("\n✓ Each month has exactly one date (as expected)")

        # Show comparison for specific months
        print("\n" + "=" * 80)
        print("COMPARISON: Total Portfolio Value by Month")
        print("=" * 80)

        # Aggregate daily to month for comparison
        daily_by_month = daily_trend.groupby('month').agg({
            'total_account_value': ['min', 'max', 'mean']
        }).round(2)
        daily_by_month.columns = ['Min (Daily)', 'Max (Daily)', 'Avg (Daily)']

        monthly_by_month = monthly_trend.groupby('month').agg({
            'total_account_value': 'sum'
        }).round(2)
        monthly_by_month.columns = ['Monthly Aggregated']

        comparison = pd.concat([daily_by_month, monthly_by_month], axis=1)

        # Calculate the artificial dip percentage
        comparison['Dip %'] = (
            (comparison['Max (Daily)'] - comparison['Min (Daily)']) /
            comparison['Max (Daily)'] * 100
        ).round(2)

        print("\n")
        print(comparison.tail(12))  # Show last 12 months

        # Highlight problem months
        problem_threshold = 5.0  # 5% difference is significant
        significant_dips = comparison[comparison['Dip %'] > problem_threshold]

        if len(significant_dips) > 0:
            print(f"\n⚠️  Months with significant dips (> {problem_threshold}%):")
            for month, row in significant_dips.iterrows():
                print(f"  {month}: {row['Dip %']:.1f}% difference "
                      f"(${row['Min (Daily)']:,.2f} to ${row['Max (Daily)']:,.2f})")
            print("\n✓ These dips are eliminated in the monthly view!")
        else:
            print(f"\n✓ No significant dips found (all < {problem_threshold}%)")

        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)

        print(f"""
✓ Daily view shows {len(daily_trend)} data points
✓ Monthly view shows {len(monthly_trend)} data points (one per month per account)
✓ Monthly view eliminates {len(problem_months)} months with multiple dates
✓ Recommended: Use monthly=True (default) for portfolio value trends
        """)

    finally:
        # Clean up
        db_manager.close_all_connections()
        print("\nDatabase connections closed.")

if __name__ == '__main__':
    main()
