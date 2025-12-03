# Quick Start Guide

## 1. Initial Setup

### Install PostgreSQL (if not already installed)
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
```

### Run the database setup script
```bash
./setup_database.sh
```

This will:
- Create the database
- Initialize the schema
- Create your `.env` configuration file

### Install Python dependencies
```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Process Your Statements

Your statements are already organized in the `statements/` directory:
- `statements/SunLife/` - SunLife statements
- `statements/ScotiaBank/` - ScotiaBank statements
- `statements/Olympia/` - Olympia Trust statements

Process all statements:
```bash
python process_statements.py process
```

## 3. Generate Reports

Generate analysis and visualizations:
```bash
python process_statements.py report
```

Reports will be saved in the `reports/` directory including:
- Asset allocation pie chart
- Portfolio value trend chart
- Allocation evolution over time
- Top holdings chart
- Returns analysis
- Summary text report

## 4. All-in-One Command

Process statements and generate reports in one command:
```bash
python process_statements.py all
```

## Example: Using Python Interactively

```python
from database import DatabaseManager
from analysis import PortfolioAnalyzer
from visualization import PortfolioVisualizer
import config

# Initialize
db = DatabaseManager(config.DB_CONFIG)
analyzer = PortfolioAnalyzer(db)
visualizer = PortfolioVisualizer(analyzer)

# Get portfolio summary
summary = analyzer.get_portfolio_summary()
print(f"Total Value: ${summary['total_value']:,.2f}")
print(f"Accounts: {summary['num_accounts']}")
print(f"Securities: {summary['num_securities']}")

# Get current holdings
holdings = analyzer.get_holdings_by_account()
print("\nYour Holdings:")
print(holdings[['institution_name', 'account_number', 'security_name',
               'quantity', 'market_value']])

# Get allocation
allocation = analyzer.get_current_allocation()
print("\nAsset Allocation:")
print(allocation.groupby('asset_category')['total_value'].sum())

# Get top holdings
top = analyzer.get_top_holdings(10)
print("\nTop 10 Holdings:")
print(top[['security_name', 'market_value', 'portfolio_pct']])

# Analyze concentration
risk = analyzer.get_concentration_risk()
print(f"\nTop 5 Holdings Concentration: {risk['top5_concentration']:.1f}%")

# Generate charts
visualizer.plot_asset_allocation('my_allocation.png')
visualizer.plot_value_trend('my_trend.png')

# Close connections
db.close_all_connections()
```

## Direct Database Queries

You can also query the database directly:

```bash
psql -U your_username -d portfolio_db
```

Useful queries:

```sql
-- Get latest total value by institution
SELECT
    i.institution_name,
    SUM(h.market_value) as total_value
FROM holdings h
JOIN accounts a ON h.account_id = a.account_id
JOIN institutions i ON a.institution_id = i.institution_id
JOIN statements s ON h.statement_id = s.statement_id
WHERE s.statement_date = (SELECT MAX(statement_date) FROM statements WHERE account_id = a.account_id)
GROUP BY i.institution_name;

-- Get all holdings for a specific account
SELECT * FROM v_latest_holdings
WHERE account_number = '01749108553433';

-- Get portfolio value over time
SELECT * FROM v_portfolio_value_trend
ORDER BY statement_date;
```

## Troubleshooting

### Database connection errors
Check your `.env` file has correct credentials:
```bash
cat .env
```

Test connection:
```bash
psql -U your_username -d portfolio_db -c "SELECT COUNT(*) FROM institutions;"
```

### PDF parsing errors
Enable debug mode by editing the parser file and checking the output.

### Missing data
Check if the statement was processed:
```sql
SELECT * FROM statements ORDER BY processed_at DESC;
```

## Next Steps

1. Add more statements to the `statements/` directory
2. Run `python process_statements.py process` to update the database
3. Generate new reports with `python process_statements.py report`
4. Use the Python API for custom analysis
