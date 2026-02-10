# Monthly Aggregation for Portfolio Value Trends

## Problem

When you have multiple accounts (e.g., 3 CIBC accounts) with statement dates on different days within the same month, it creates artificial dips in portfolio value trend charts. For example:

- May 2025: Account A statement on 5/30, Account B on 5/31
- August 2025: Account A statement on 8/29, Account B on 8/31

This results in two separate data points for each month, where one shows only partial portfolio value (missing accounts that haven't reported yet), creating misleading dips in the trend line.

## Solution

The solution aggregates portfolio values by month using the **latest statement date** for each account in that month. This ensures:

1. Each month has one data point representing the complete portfolio
2. All accounts use their most recent statement within that month
3. No artificial dips from partial month data

## Implementation

### 1. New Database View

A new view `v_portfolio_value_trend_monthly` was created that:
- Groups statements by year-month
- For each account, uses the latest statement in each month
- Aggregates all account values to get the complete portfolio value per month

### 2. Updated Methods

**DatabaseManager.get_portfolio_value_trend()**
- New parameter: `monthly=True` (default)
- When `monthly=True`: Uses the new monthly aggregation view
- When `monthly=False`: Uses exact statement dates (original behavior)

**PortfolioAnalyzer.get_value_over_time()**
- New parameter: `monthly=True` (default)
- Passes through to DatabaseManager

## How to Apply

### Option 1: Apply to Existing Database

```bash
# Apply the new view to your existing database
psql -U your_username -d portfolio_db -f update_views.sql
```

### Option 2: Recreate Schema

```bash
# If you want to recreate the entire schema
psql -U your_username -d portfolio_db -f database/schema.sql
```

## Usage

### Default Behavior (Monthly Aggregation)

```python
from database import DatabaseManager
from analysis import PortfolioAnalyzer
import config

db_manager = DatabaseManager(config.DB_CONFIG)
analyzer = PortfolioAnalyzer(db_manager)

# Get monthly aggregated values (default)
trend = analyzer.get_value_over_time()
```

This will now show smooth trends without artificial dips.

### Exact Dates (If Needed)

If you ever need the exact statement dates:

```python
# Get exact statement date values
trend = analyzer.get_value_over_time(monthly=False)
```

## Example Before/After

### Before (Multiple Days per Month)
```
Date         | Total Value
2025-05-30   | $250,000  (only Account A)
2025-05-31   | $500,000  (Account A + B)
2025-08-29   | $260,000  (only Account A)
2025-08-31   | $520,000  (Account A + B)
```

Creates a sawtooth pattern with dips on the earlier dates.

### After (Monthly Aggregation)
```
Date         | Total Value
2025-05-01   | $500,000  (All accounts, using latest in May)
2025-08-01   | $520,000  (All accounts, using latest in Aug)
```

Smooth trend line representing complete portfolio value each month.

## Technical Details

### The View Logic

```sql
WITH latest_statement_per_month AS (
    -- Find the latest statement date in each month for each account
    SELECT
        account_id,
        DATE_TRUNC('month', statement_date) as month_date,
        MAX(statement_date) as latest_statement_date
    FROM statements
    GROUP BY account_id, DATE_TRUNC('month', statement_date)
),
monthly_account_values AS (
    -- Get holdings for those latest statements
    SELECT
        DATE_TRUNC('month', s.statement_date) as month_date,
        institution_name,
        account_number,
        SUM(market_value) as total_value
    FROM statements s
    JOIN latest_statement_per_month lspm
        ON s.account_id = lspm.account_id
        AND s.statement_date = lspm.latest_statement_date
    -- ... joins for holdings, institutions, etc
)
```

### Why This Works

1. **Preserves Data**: Original statement dates are still stored exactly as parsed
2. **View-Level Aggregation**: The logic is in the view, not the parsers
3. **Transparent**: Existing code works with no changes (uses monthly by default)
4. **Flexible**: Can still access exact dates if needed (`monthly=False`)
5. **Accurate**: Uses the most recent data available for each account each month

## Files Modified

1. `database/schema.sql` - Added `v_portfolio_value_trend_monthly` view
2. `database/db_manager.py` - Added `monthly` parameter to `get_portfolio_value_trend()`
3. `analysis/portfolio_analyzer.py` - Added `monthly` parameter to `get_value_over_time()`
4. `update_views.sql` - Standalone script to update existing databases

## Testing

After applying the update:

```python
# Test monthly aggregation
from database import DatabaseManager
from analysis import PortfolioAnalyzer
import config

db_manager = DatabaseManager(config.DB_CONFIG)
analyzer = PortfolioAnalyzer(db_manager)

# Monthly view (should show smooth trends)
monthly_trend = analyzer.get_value_over_time(monthly=True)
print(monthly_trend[['statement_date', 'total_account_value']].groupby('statement_date').sum())

# Daily view (will show the dips)
daily_trend = analyzer.get_value_over_time(monthly=False)
print(daily_trend[['statement_date', 'total_account_value']])

db_manager.close_all_connections()
```

## Benefits

1. **Accurate Visualization**: Charts show true portfolio trends without artificial dips
2. **Better Analysis**: Month-over-month comparisons are meaningful
3. **Performance**: Monthly aggregation reduces data points for large date ranges
4. **Backward Compatible**: Original behavior available via `monthly=False`
5. **No Data Loss**: All original statement dates preserved in database

## Notes

- The view returns `statement_date` as the first day of each month (e.g., `2025-05-01`)
- All accounts use their latest statement within each month
- If you need to see which exact dates were used, query `statements` table directly
- The visualization code automatically uses monthly aggregation by default
