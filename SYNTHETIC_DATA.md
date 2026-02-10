# Synthetic Data Generator

This document describes the synthetic data generator for creating realistic demo data without exposing personal financial information.

## Overview

The `generate_synthetic_data.py` script generates a complete synthetic portfolio dataset with:
- **6 accounts** across 3 institutions (DemoBank, DemoInvestCo, WealthAdvisors)
- **$1-2 million** total portfolio value
- **2 years** of quarterly statements (8 statements per account)
- **Real-world securities** (ETFs, stocks, mutual funds, bonds, GICs)
- **Realistic price movements** using geometric Brownian motion
- **Diversified asset allocations** appropriate for each account type

## Account Structure

### DemoBank
1. **RRSP-001234** (Personal RRSP)
   - Target: $450k
   - Allocation: 60% ETF, 20% Stock, 10% Mutual Fund, 10% Bond
   - Monthly contribution: $500

2. **TFSA-005678** (Tax-Free Savings)
   - Target: $150k
   - Allocation: 70% ETF, 25% Stock, 5% Mutual Fund
   - Monthly contribution: $300

### DemoInvestCo
3. **RRSP-987654** (Spousal RRSP)
   - Target: $380k
   - Allocation: 50% ETF, 15% Stock, 20% Mutual Fund, 15% Bond
   - Monthly contribution: $400

4. **NON-REG-112233** (Non-Registered Investment)
   - Target: $520k
   - Allocation: 50% Stock, 30% ETF, 20% Bond
   - Monthly contribution: $1000

### WealthAdvisors
5. **LIRA-445566** (Locked-In Retirement)
   - Target: $280k
   - Allocation: 40% ETF, 35% Mutual Fund, 15% Bond, 10% GIC
   - Monthly contribution: $0 (locked-in)

6. **RESP-778899** (Education Savings)
   - Target: $120k
   - Allocation: 55% ETF, 30% Mutual Fund, 15% Bond
   - Monthly contribution: $200

## Securities Pool

The generator includes 40+ real-world securities:

### ETFs (10)
- VGRO, VFV, VCN, XAW, XIC, ZAG, VDY, XEF, VIU, ZRE

### Stocks (14)
- **Canadian**: TD.TO, RY.TO, BMO.TO, ENB.TO, CNR.TO, SU.TO, BCE.TO, T.TO, SHOP.TO
- **US**: AAPL, MSFT, GOOGL, AMZN, JPM

### Mutual Funds (6)
- RBC Canadian Equity Fund
- TD Canadian Bond Fund
- Fidelity Global Equity Fund
- BMO Balanced Fund
- Scotia Canadian Dividend Fund
- Mackenzie US Equity Fund

### Bonds (3)
- Government of Canada 5-Year and 10-Year Bonds
- Province of Ontario 5-Year Bond

### GICs (3)
- TD, RBC, and BMO GICs with varying terms and rates

## Price Generation

Prices are generated using **geometric Brownian motion** to simulate realistic market movements:

- **Drift**: 8% annual return (base growth rate)
- **Volatility**: Varies by security type (4-35%)
  - GICs: 0% (fixed price)
  - Bonds: 4-6%
  - ETFs: 12-18%
  - Stocks: 15-35%
- **Random shocks**: Gaussian distribution for daily price changes

Holdings show realistic:
- Unrealized gains/losses (book value vs market value)
- Position sizing based on account allocation
- Cash balances (1-5% of portfolio)

## Usage

### Generate Fresh Dataset

```bash
# Generate 2 years of quarterly data (default)
python generate_synthetic_data.py --reset --yes

# Generate custom time period
python generate_synthetic_data.py --reset --yes --months 12

# Interactive mode (prompts for confirmation)
python generate_synthetic_data.py --reset
```

### Command-Line Options

- `--reset`: Reset database before generating (WARNING: deletes all data)
- `--yes, -y`: Skip confirmation prompts (for automation)
- `--months MONTHS`: Number of months to generate (default: 24)
- `--help`: Show help message

### Example Output

```
INFO:__main__:Synthetic data generation complete!
INFO:__main__:  Total accounts: 6
INFO:__main__:  Total statements: 48
INFO:__main__:  Total holdings created: 635

Portfolio Summary (Latest Statement):
----------------------------------------------------------------------
  DemoInvestCo         - 2 account(s): $1,094,347.02
  DemoBank             - 2 account(s): $  729,985.77
  WealthAdvisors       - 2 account(s): $  462,178.03
----------------------------------------------------------------------
  TOTAL PORTFOLIO                   $2,286,510.82
```

## Use Cases

### Demos and Presentations
Show portfolio management capabilities without exposing real data:
```bash
python generate_synthetic_data.py --reset --yes
python -m web.app
# Access web interface at http://localhost:5000
```

### Development and Testing
Generate test data for development:
```bash
# Quick 6-month dataset for testing
python generate_synthetic_data.py --reset --yes --months 6

# Run analysis
python process_statements.py report
```

### Training and Documentation
Create consistent datasets for tutorials and documentation:
```bash
# Generate standard 2-year dataset
python generate_synthetic_data.py --reset --yes

# Generate reports
python process_statements.py report --output-dir demo-reports
```

## Data Quality Features

### Realistic Characteristics
- Portfolio growth over time (contributions + market returns)
- Quarterly rebalancing (holdings change between statements)
- Appropriate asset allocation per account type
- Realistic security names and symbols
- Cash balances for liquidity

### Data Integrity
- All foreign key relationships maintained
- Proper asset type classifications
- Valid date ranges
- Positive prices and quantities
- Consistent statement periods

### Reproducibility
- Uses fixed random seed (42) for consistent results
- Same parameters generate identical data
- Useful for regression testing

## Integration with Existing System

The generator:
- Uses existing `DatabaseManager` for all database operations
- Respects existing schema constraints
- Works with existing parsers and analysis tools
- Compatible with web interface and reporting

After generating data, all existing commands work normally:
```bash
# Generate reports
python process_statements.py report

# Start web app
python -m web.app

# Query database
python -c "from database.db_manager import DatabaseManager; from config import DB_CONFIG; ..."
```

## Customization

To customize the synthetic data:

### Modify Account Configurations
Edit `ACCOUNT_CONFIGS` in generate_synthetic_data.py (line 127):
```python
{
    'institution': 'YourBank',
    'account_number': 'CUSTOM-123',
    'account_type': 'RRSP',
    'target_value': 500000,
    'allocation': {'ETF': 0.6, 'Stock': 0.4},
    'monthly_contribution': 1000,
}
```

### Add Securities
Edit `SECURITIES_POOL` in generate_synthetic_data.py (line 33):
```python
'Stock': [
    {'symbol': 'NEW.TO', 'name': 'New Company', 'base_price': 50.0, 'volatility': 0.20},
    ...
]
```

### Adjust Market Parameters
Edit price generation function (line 230):
```python
drift = 0.10 / 365  # Change to 10% annual return
volatility = security['volatility'] * 1.5  # Increase volatility
```

## Limitations

- **Historical accuracy**: Prices are simulated, not real historical data
- **Market events**: Does not model crashes, bull markets, or specific events
- **Correlation**: Securities move independently (no market correlation)
- **Transactions**: No buy/sell transactions, just snapshot holdings
- **Fees**: No trading fees or management fees included
- **Dividends**: Not explicitly tracked (included in price growth)

## Safety

The generator:
- Only creates demo institutions (DemoBank, DemoInvestCo, WealthAdvisors)
- Requires explicit `--reset` flag to modify database
- Prompts for confirmation unless `--yes` specified
- Logs all operations for audit trail
- Can be run repeatedly without side effects (with reset)

## Performance

- Generates 48 statements (6 accounts × 8 quarters) in ~5 seconds
- Creates ~600-700 holdings records
- Minimal database load (uses connection pooling)
- Can generate years of data quickly

## Next Steps

After generating synthetic data:
1. Run `python process_statements.py report` to generate charts
2. Start web interface with `python -m web.app`
3. Try natural language queries to explore the data
4. Use for demos, training, or development

For questions or issues, see the main README.md or CLAUDE.md for system architecture details.
