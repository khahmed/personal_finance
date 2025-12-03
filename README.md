# Personal Banking Portfolio Management System

A comprehensive system for parsing financial statements, storing holdings data in PostgreSQL, and analyzing portfolio trends over time.

## Features

- **PDF Parsing**: Automatically extracts holdings data from statements from multiple financial institutions:
  - SunLife
  - ScotiaBank (ScotiaMcLeod)
  - Olympia Trust Company

- **Database Storage**: Stores all holdings data in a PostgreSQL database with proper schema for:
  - Institutions and accounts
  - Securities and asset types
  - Holdings at different points in time
  - Performance metrics

- **Analysis Tools**: Comprehensive portfolio analysis including:
  - Current allocation by asset class
  - Portfolio value trends over time
  - Returns calculations
  - Concentration risk analysis
  - Diversification metrics
  - Top holdings analysis

- **Visualization**: Generates professional charts and reports:
  - Asset allocation pie charts
  - Value trend line charts
  - Allocation evolution over time
  - Holdings by account
  - Top holdings bar charts
  - Returns visualization

## Directory Structure

```
personal_banking/
├── statements/                 # PDF statements directory
│   ├── SunLife/
│   ├── ScotiaBank/
│   └── Olympia/
├── database/                   # Database management
│   ├── schema.sql             # Database schema
│   ├── db_manager.py          # Database operations
│   └── __init__.py
├── parsers/                    # PDF parsers
│   ├── base_parser.py         # Base parser class
│   ├── sunlife_parser.py      # SunLife parser
│   ├── scotiabank_parser.py   # ScotiaBank parser
│   ├── olympia_parser.py      # Olympia parser
│   └── __init__.py
├── analysis/                   # Analysis tools
│   ├── portfolio_analyzer.py  # Portfolio analysis
│   └── __init__.py
├── visualization/              # Visualization tools
│   ├── portfolio_visualizer.py # Chart generation
│   └── __init__.py
├── reports/                    # Generated reports (created automatically)
├── process_statements.py       # Main script
├── config.py                   # Configuration
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## Installation

### 1. Install PostgreSQL

Make sure you have PostgreSQL installed and running. On Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
```

### 2. Create Database

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE portfolio_db;
CREATE USER your_username WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE portfolio_db TO your_username;
\q
```

### 3. Initialize Database Schema

```bash
psql -U your_username -d portfolio_db -f database/schema.sql
```

### 4. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 5. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your database credentials
nano .env
```

Update the following in `.env`:
```
DB_HOST=localhost
DB_NAME=portfolio_db
DB_USER=your_username
DB_PASSWORD=your_password
DB_PORT=5432
```

## Usage

### Process All Statements

Process all PDF statements in the `statements` directory and load them into the database:

```bash
python process_statements.py process
```

Or specify a custom statements directory:

```bash
python process_statements.py process --statements-dir /path/to/statements
```

### Generate Reports

Generate analysis reports and charts:

```bash
python process_statements.py report
```

Or specify a custom output directory:

```bash
python process_statements.py report --output-dir /path/to/reports
```

### Do Both (Process + Report)

```bash
python process_statements.py all
```

### Using Python Interactively

You can also use the components programmatically:

```python
from database import DatabaseManager
from analysis import PortfolioAnalyzer
from visualization import PortfolioVisualizer
import config

# Initialize components
db_manager = DatabaseManager(config.DB_CONFIG)
analyzer = PortfolioAnalyzer(db_manager)
visualizer = PortfolioVisualizer(analyzer)

# Get portfolio summary
summary = analyzer.get_portfolio_summary()
print(f"Total Value: ${summary['total_value']:,.2f}")

# Get current holdings
holdings = analyzer.get_holdings_by_account()
print(holdings)

# Generate specific chart
visualizer.plot_asset_allocation('allocation.png')

# Get value trend
trend = analyzer.get_value_over_time()
print(trend)

# Close connections
db_manager.close_all_connections()
```

## Database Schema

The system uses the following main tables:

- **institutions**: Financial institutions (SunLife, ScotiaBank, etc.)
- **accounts**: Individual accounts (RRSP, TFSA, LIRA, etc.)
- **asset_types**: Types of assets (Stock, ETF, Mutual Fund, etc.)
- **securities**: Individual securities/holdings
- **statements**: Statement metadata
- **holdings**: Holdings at specific points in time
- **cash_balances**: Cash balances
- **account_performance**: Performance metrics

## Analysis Features

### Portfolio Summary
- Total portfolio value
- Number of accounts and securities
- Gain/loss calculations
- Breakdown by institution and asset category

### Allocation Analysis
- Current allocation by asset class
- Historical allocation trends
- Allocation by account

### Performance Analysis
- Value trends over time
- Returns calculations (period and cumulative)
- Performance by account

### Risk Analysis
- Concentration risk (top holdings)
- Diversification metrics (HHI, effective N)
- Asset category distribution

## Visualization Outputs

The system generates the following charts:

1. **Asset Allocation Pie Chart**: Current portfolio allocation by asset category
2. **Value Trend Chart**: Portfolio value over time
3. **Allocation Trend Chart**: Stacked area chart showing how allocation has evolved
4. **Allocation by Account**: Bar chart showing allocation for each account
5. **Top Holdings**: Bar chart of largest holdings
6. **Returns Chart**: Portfolio value and cumulative returns over time
7. **Summary Report**: Text file with portfolio statistics

## Adding New Statement Formats

To add support for a new financial institution:

1. Create a new parser in `parsers/` inheriting from `BaseStatementParser`
2. Implement the required methods: `parse()`, `extract_account_info()`, `extract_holdings()`
3. Update `process_statements.py` to recognize the new institution
4. Add the institution name to `database/schema.sql` if needed

## Troubleshooting

### PDF Parsing Issues

If a statement is not parsing correctly:
- Check the PDF structure manually
- Enable debug logging in the parser
- Review the regex patterns in the parser for that institution

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -U your_username -d portfolio_db -c "SELECT version();"

# Check if database exists
psql -U your_username -l
```

### Missing Dependencies

```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

## Security Notes

- Never commit `.env` file or database credentials to version control
- Use environment variables for sensitive configuration
- Restrict database access appropriately
- Keep backups of your database

## Backup Database

```bash
# Backup
pg_dump -U your_username portfolio_db > portfolio_backup.sql

# Restore
psql -U your_username -d portfolio_db < portfolio_backup.sql
```

## License

This is a personal project for managing your own financial data.

## Support

For issues or questions, review the code and logs for troubleshooting.
