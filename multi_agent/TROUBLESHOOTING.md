# Troubleshooting Guide

## Common Issues and Solutions

### 1. OPENAI_API_KEY Warnings

**Problem**: CrewAI tries to create agents with OpenAI by default, causing warnings about missing API key.

**Solution**: The code has been updated to skip CrewAI Agent creation since we use direct method calls. The warnings are harmless but can be suppressed by:

1. **Option A (Recommended)**: The code now skips CrewAI Agent creation by default. No action needed.

2. **Option B**: If you want to use CrewAI tasks/crews with Anthropic:
   ```bash
   export ANTHROPIC_API_KEY="your-key-here"
   ```
   Then uncomment the Agent creation code in `base_agent.py` and configure it for Anthropic.

### 2. None Value Errors

**Problem**: `float() argument must be a string or a real number, not 'NoneType'`

**Solution**: Fixed in the code. All value conversions now handle None safely:
- `book_value` and `market_value` are checked for None before conversion
- Default to 0.0 if None or invalid

### 3. Pydantic Validation Errors

**Problem**: `symbol` field is None when it should be a string

**Solution**: Fixed. All string fields now use `or ''` to ensure they're never None:
- `symbol=holding.get('symbol') or ''`
- `security_name=holding.get('security_name') or 'Unknown'`

### 4. pkg_resources Deprecation Warning

**Problem**: Warning about pkg_resources being deprecated

**Solution**: This is a CrewAI dependency issue. To suppress:
- Pin setuptools to <81.0.0 (already done in requirements.txt)
- The warning is harmless and will be resolved when CrewAI updates

### 5. Empty Results

**Problem**: Analysis returns empty or zero values

**Possible Causes**:
1. Database has no data
2. Holdings have None values for book_value/market_value
3. Date filters exclude all data

**Solution**:
- Check database: `SELECT COUNT(*) FROM holdings;`
- Verify data quality: `SELECT * FROM v_latest_holdings LIMIT 5;`
- Check for NULL values: `SELECT COUNT(*) FROM holdings WHERE book_value IS NULL;`

## Configuration

### Using Anthropic Instead of OpenAI

1. Set environment variable:
   ```bash
   export ANTHROPIC_API_KEY="your-key-here"
   ```

2. The system will use Anthropic for any LLM-based features (currently not used in direct method calls)

3. If you want to use CrewAI tasks with Anthropic, update `base_agent.py` to configure the LLM.

## Running the System

### Basic Test
```bash
python -m multi_agent.main
```

### With Custom Context
```python
from multi_agent.flows.financial_advisory_flow import FinancialAdvisoryFlow

flow = FinancialAdvisoryFlow()
results = flow.get_comprehensive_review({
    "tax_rate": 0.30,
    "province": "ON",
    "age": 55
})
```

## Debugging

### Enable Verbose Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Database Connection
```python
from database.db_manager import DatabaseManager
from config import DB_CONFIG

db = DatabaseManager(DB_CONFIG)
result = db.execute_query("SELECT 1", None, fetch=True)
print("Database OK" if result else "Database Error")
```

### Verify Data
```python
from multi_agent.agents.portfolio_data_agent import PortfolioDataAgent

agent = PortfolioDataAgent()
summary = agent.get_portfolio_summary()
print(summary)
```

## Performance

If the system is slow:
1. Check database query performance
2. Reduce number of holdings analyzed
3. Use parallel workflow for independent analyses
4. Cache portfolio summary data

