# Personal Banking Portfolio Management System

A comprehensive system for parsing financial statements, storing holdings data in PostgreSQL, and analyzing portfolio trends over time. Features AI-powered parser generation and a natural language query interface.

## Features

### Core Capabilities

- **PDF Parsing**: Automatically extracts holdings data from statements from multiple financial institutions
  - Dynamic parser loading system with pattern matching
  - Support for multiple parsers per institution
  - Currently supports: SunLife, ScotiaBank, Olympia Trust, CIBC

- **AI Parser Generation**: Automatically generate parsers for new institutions using CrewAI
  - Analyzes PDF statement structures
  - Generates production-ready Python code
  - 5-10 minutes vs 2-4 hours manual coding

- **Database Storage**: PostgreSQL database with proper schema for:
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

- **Natural Language Query Interface**: Web-based interface for portfolio queries
  - Ask questions in plain English
  - Automatic SQL generation using LLM
  - Code generation for reusable analysis methods
  - Safe query execution (SELECT only)

## Quick Start

### 1. Install PostgreSQL and Create Database

```bash
# On Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Create database
sudo -u postgres psql
CREATE DATABASE portfolio_db;
CREATE USER your_username WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE portfolio_db TO your_username;
\q
```

### 2. Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Update `.env`:
```bash
DB_HOST=localhost
DB_NAME=portfolio_db
DB_USER=your_username
DB_PASSWORD=your_password
DB_PORT=5432

# Optional: API keys for advanced features
ANTHROPIC_API_KEY=your-key-here    # For AI parser generation
DEEPSEEK_API_KEY=your-key-here     # For web interface (recommended)
# OR
OPENAI_API_KEY=your-key-here       # Alternative for web interface
```

### 4. Initialize Database Schema

```bash
psql -U your_username -d portfolio_db -f database/schema.sql
```

### 5. Process Statements

```bash
# Place PDF statements in statements/ directory
mkdir -p statements/YourBank
cp /path/to/statements/*.pdf statements/YourBank/

# Process all statements
python process_statements.py process

# Generate reports
python process_statements.py report

# Or do both
python process_statements.py all
```

### 6. Launch Web Interface (Optional)

```bash
# Run web application
./run_web_app.sh
# OR
python -m web.app

# Open browser to http://localhost:5000
```

## Directory Structure

```
personal_finance/
├── statements/                 # PDF statements (organized by institution)
│   ├── SunLife/
│   ├── ScotiaBank/
│   ├── Olympia/
│   └── CIBC/
├── database/                   # Database management
│   ├── schema.sql             # PostgreSQL schema
│   └── db_manager.py          # Database operations
├── parsers/                    # PDF parsers
│   ├── base_parser.py         # Base parser class
│   └── *_parser.py            # Institution-specific parsers
├── parser_generator/           # AI parser generation
│   └── agent.py               # CrewAI agents
├── analysis/                   # Analysis tools
│   └── portfolio_analyzer.py  # Portfolio analysis
├── visualization/              # Visualization tools
│   └── portfolio_visualizer.py # Chart generation
├── web/                        # Web application
│   ├── app.py                 # Flask API
│   ├── nl_to_sql.py           # Natural language queries
│   ├── code_generator.py      # Python code generation
│   └── templates/             # HTML templates
├── reports/                    # Generated reports (auto-created)
├── process_statements.py       # Main CLI script
├── parser_loader.py           # Dynamic parser loading
├── institutions.yaml          # Parser configuration
├── config.py                  # Configuration
├── requirements.txt           # Python dependencies
└── .env                       # Environment variables (gitignored)
```

## Usage

### Processing Statements

```bash
# Process all PDFs in statements/ directory
python process_statements.py process

# Process from custom directory
python process_statements.py process --statements-dir /path/to/statements

# Generate analysis reports and charts
python process_statements.py report --output-dir reports

# Process and generate reports
python process_statements.py all
```

### Database Management

```bash
# Reset data tables only (preserves reference data)
python process_statements.py reset --reset-type data

# Reset ALL tables (complete wipe - requires confirmation)
python process_statements.py reset --reset-type all
```

### Parser Management

```bash
# List all configured parsers
python parser_loader.py list

# Test which parser matches a file
python parser_loader.py test "statements/TD/statement.pdf"

# Add a parser to configuration
python parser_loader.py add TD TDParser parsers.td_parser "TD Bank accounts"
```

### Programmatic Usage

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

# Generate charts
visualizer.plot_asset_allocation('allocation.png')

# Close connections
db_manager.close_all_connections()
```

## AI Parser Generation

Generate parsers for new institutions automatically using AI agents.

### Setup

```bash
# Install CrewAI dependencies
venv/bin/pip install crewai crewai-tools anthropic pyyaml

# Set API key
export ANTHROPIC_API_KEY="your-api-key-here"
# Or add to .env file
echo "ANTHROPIC_API_KEY=your-api-key-here" >> .env
```

### Generate a Parser

```bash
# 1. Organize statements
mkdir statements/TD
cp /path/to/td-statements/*.pdf statements/TD/

# 2. Generate parser (analyzes PDFs and creates code)
venv/bin/python parser_generator/agent.py TD

# 3. Review generated code
cat parsers/td_parser.py
cat parsers/td_analysis.md

# 4. Test the parser
venv/bin/python -c "
from parsers.td_parser import TDParser
parser = TDParser('statements/TD/sample.pdf')
data = parser.parse()
print(f'Account: {data[\"account_number\"]}')
print(f'Holdings: {len(data[\"holdings\"])}')
"

# 5. Register the parser
venv/bin/python parser_loader.py add TD TDParser parsers.td_parser "TD Bank accounts"

# 6. Process statements
venv/bin/python process_statements.py process
```

### How AI Parser Generation Works

The parser generator uses CrewAI with specialized agents:

1. **Financial Statement Analyzer** - Analyzes PDF structure:
   - Account number formats
   - Date formats
   - Holdings table structures
   - Category headers
   - Currency indicators
   - Special cases and edge cases

2. **Parser Code Generator** - Generates Python code:
   - Inherits from `BaseStatementParser`
   - Implements required methods
   - Uses regex for extraction
   - Handles edge cases
   - Follows PEP 8 style

3. **Integration** - Saves to `parsers/<institution>_parser.py`:
   - Can be tested immediately
   - Register in `institutions.yaml`
   - Works with existing database and analysis code

### Configuration Format

`institutions.yaml` structure:
```yaml
institutions:
  TD:
    name: "TD Bank"
    parsers:
      - pattern: "direct"  # Matches files containing "direct"
        class: "TDDirectParser"
        module: "parsers.td_direct_parser"
        description: "TD Direct Investing accounts"
      - pattern: "*"  # Default fallback
        class: "TDParser"
        module: "parsers.td_parser"
        description: "Standard TD investment accounts"
```

**Pattern Matching Rules:**
- Patterns match against lowercase filename
- `"*"` matches anything (default/fallback)
- Use keywords: "pps", "tfsa", "rrsp", "direct"
- First matching pattern wins

### Cost Considerations

- Analysis phase: ~10-20K tokens
- Code generation: ~30-50K tokens
- Total cost: ~$0.50-$2.00 per parser (Claude Sonnet)

### Manual vs Automatic

**Manual (Old Way):**
- Time: 2-4 hours per institution
- Requires: PDF analysis, regex expertise, Python knowledge

**Automatic (New Way):**
- Time: 5-10 minutes per institution
- Requires: Sample PDFs, API key

## Web Query Interface

Natural language interface for querying your portfolio.

### Launch Web App

```bash
# Quick start
./run_web_app.sh

# Or manually
python -m web.app

# Access at http://localhost:5000
```

### Setup API Key (Optional but Recommended)

```bash
# Priority order: DeepSeek > OpenAI > Anthropic
export DEEPSEEK_API_KEY="your-key-here"
# OR
export OPENAI_API_KEY="your-key-here"
# OR
export ANTHROPIC_API_KEY="your-key-here"
```

Without an API key, the system uses rule-based SQL generation (less accurate).

### Example Queries

- "Show me my top 10 holdings by value"
- "What is my total portfolio value?"
- "Show me allocation by asset category"
- "What are my holdings for Scotiabank?"
- "Show me portfolio value over the last 6 months"
- "What is my allocation by institution?"

### Generate Reusable Code

1. Execute a query
2. Check "Generate Python code for this query"
3. Click "Add to portfolio_analyzer.py"
4. The method will be added to `analysis/portfolio_analyzer.py`

### API Endpoints

**POST `/api/query`** - Execute natural language query
```json
{
  "query": "Show me my top holdings",
  "generate_code": false
}
```

**POST `/api/generate_code`** - Generate Python code for SQL
**GET `/api/schema`** - Get database schema
**GET `/api/examples`** - Get example queries

### Web Interface Features

- Natural language to SQL conversion
- Safe query execution (SELECT only)
- Automatic code generation
- Modern, responsive UI
- Example queries included
- Schema information display

## Database Schema

Main tables:

- **institutions**: Financial institutions (SunLife, ScotiaBank, etc.)
- **accounts**: Individual accounts (RRSP, TFSA, LIRA, etc.)
- **asset_types**: Types of assets (Stock, ETF, Mutual Fund, etc.)
- **securities**: Individual securities/holdings
- **statements**: Statement metadata
- **holdings**: Holdings at specific points in time
- **cash_balances**: Cash balances
- **account_performance**: Performance metrics

Database views for analysis:
- `v_latest_holdings` - Current holdings with full details
- `v_portfolio_allocation` - Allocation by asset category
- `v_portfolio_value_trend` - Value over time

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

1. **Asset Allocation Pie Chart**: Current portfolio allocation
2. **Value Trend Chart**: Portfolio value over time
3. **Allocation Trend Chart**: Stacked area chart showing evolution
4. **Allocation by Account**: Bar chart per account
5. **Top Holdings**: Bar chart of largest holdings
6. **Returns Chart**: Portfolio value and cumulative returns
7. **Summary Report**: Text file with statistics

## Troubleshooting

### PDF Parsing Issues

If a statement is not parsing correctly:
- Check the PDF structure manually
- Enable debug logging in the parser
- Review regex patterns in the parser
- Consider using AI parser generator to regenerate

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

### Web Interface Issues

**Port already in use?**
```python
# Edit web/app.py
app.run(debug=True, host='0.0.0.0', port=5001)  # Change port
```

**Database connection error?**
```bash
# Set environment variables
export DB_HOST=localhost
export DB_NAME=portfolio_db
export DB_USER=your_user
export DB_PASSWORD=your_password
```

### Parser Generator Issues

**Parser not found for institution:**
```bash
# Check configuration
venv/bin/python parser_loader.py list

# Test file detection
venv/bin/python parser_loader.py test "path/to/file.pdf"

# Add missing institution
venv/bin/python parser_loader.py add Institution Parser parsers.module
```

**Generated parser has errors:**
1. Review analysis report: `parsers/<institution>_analysis.md`
2. Check if PDFs have consistent format
3. Edit generated parser manually
4. Regenerate with more/different sample PDFs

## Security Notes

- Never commit `.env` file or database credentials
- Use environment variables for sensitive configuration
- Web interface only allows SELECT queries
- SQL injection protection through validation
- Restrict database access appropriately
- Keep database backups

## Database Backup

```bash
# Backup
pg_dump -U your_username portfolio_db > portfolio_backup.sql

# Restore
psql -U your_username -d portfolio_db < portfolio_backup.sql
```

## Best Practices

1. **Use 3-5 sample PDFs** when generating parsers
2. **Review generated code** before production use
3. **Test thoroughly** with all statement variations
4. **Version control** - Commit parsers to git
5. **Document changes** - If editing generated code, explain why
6. **Regular backups** - Back up your database regularly
7. **Keep statements organized** - One directory per institution

## Advanced Features

### Multiple Parsers per Institution

```yaml
CIBC:
  parsers:
    - pattern: "pps"           # Bank-managed accounts
      class: "CIBCPPSParser"
    - pattern: "investorsedge" # Self-directed accounts
      class: "CIBCInvestorsEdgeParser"
    - pattern: "*"             # Fallback
      class: "CIBCParser"
```

### Custom AI Model for Parser Generation

Edit `parser_generator/agent.py`:
```python
# Use Claude Opus for better quality
llm = ChatAnthropic(
    model="claude-opus-4-20250514",
    api_key=os.getenv("ANTHROPIC_API_KEY")
)
```

## Support

For issues or questions:
1. Check this README and CLAUDE.md
2. Review existing parsers in `parsers/` directory
3. Check `web/TROUBLESHOOTING.md` for web interface issues
4. Review agent prompts in `parser_generator/agent.py`
5. Check CrewAI documentation: https://docs.crewai.com

## License

This is a personal project for managing your own financial data.
