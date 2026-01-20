# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Personal Banking Portfolio Management System - A Python application that parses financial statement PDFs from multiple institutions, stores holdings data in PostgreSQL, and provides portfolio analysis, visualization, and natural language query capabilities.

## System Architecture

### Core Components

**1. Parser System (Dynamic & AI-Assisted)**
- `parsers/base_parser.py` - Abstract base class with common utilities (clean_currency_value, parse_date, classify_security)
- Institution-specific parsers inherit from BaseStatementParser and implement parse(), extract_account_info(), extract_holdings()
- `parser_loader.py` - Dynamic parser loading system based on institutions.yaml configuration
- `institutions.yaml` - Maps institution directory names and filename patterns to parser classes
- `parser_generator/agent.py` - CrewAI-based system for auto-generating parsers from sample PDFs

**2. Database Layer**
- `database/db_manager.py` - Connection pooling, CRUD operations, statement data persistence
- `database/schema.sql` - PostgreSQL schema with tables for institutions, accounts, securities, holdings, statements, cash_balances
- Database views for latest holdings, portfolio allocation, value trends

**3. Analysis & Visualization**
- `analysis/portfolio_analyzer.py` - Portfolio summary, allocation, performance metrics, concentration risk
- `visualization/portfolio_visualizer.py` - Generates charts (allocation pie, value trends, top holdings)

**4. Web Application**
- `web/app.py` - Flask API with natural language query interface
- `web/nl_to_sql.py` - LLM-powered natural language to SQL converter (DeepSeek/OpenAI/Anthropic)
- `web/code_generator.py` - Generates Python methods for portfolio_analyzer.py from queries
- `web/sql_validator.py` - Ensures only safe SELECT queries are executed

**5. Main Processing Script**
- `process_statements.py` - CLI for processing PDFs, generating reports, resetting database

## Development Commands

### Environment Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure database credentials
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

### Database Operations

```bash
# Initialize database schema
psql -U your_username -d portfolio_db -f database/schema.sql

# Reset data tables only (preserves reference data)
python process_statements.py reset --reset-type data

# Reset ALL tables (complete wipe)
python process_statements.py reset --reset-type all
```

### Processing Statements

```bash
# Process all PDFs in statements/ directory
python process_statements.py process

# Process from custom directory
python process_statements.py process --statements-dir /path/to/statements

# Generate analysis reports and charts
python process_statements.py report --output-dir reports

# Do both (process + report)
python process_statements.py all
```

### Parser Management

```bash
# List all configured parsers
python parser_loader.py list

# Test which parser matches a file
python parser_loader.py test "statements/TD/statement.pdf"

# Add a new parser to configuration
python parser_loader.py add InstitutionName ParserClass parsers.module "Description"
```

### AI Parser Generation

```bash
# Generate parser for a new institution
# 1. Place sample PDFs in statements/InstitutionName/
# 2. Set API key (if not already set)
export ANTHROPIC_API_KEY="your-key-here"

# 3. Generate parser
python parser_generator/agent.py InstitutionName

# 4. Review generated code
cat parsers/institutionname_parser.py
cat parsers/institutionname_analysis.md

# 5. Register the parser
python parser_loader.py add InstitutionName ParserClass parsers.institutionname_parser "Description"
```

### Web Application

```bash
# Run web interface
./run_web_app.sh
# OR
python -m web.app

# Access at http://localhost:5000

# Optional: Set LLM API key for better natural language queries
export DEEPSEEK_API_KEY="your-key"      # Recommended (cost-effective)
export OPENAI_API_KEY="your-key"        # Alternative
export ANTHROPIC_API_KEY="your-key"     # Alternative
```

### Testing Parsers

```bash
# Test a specific parser programmatically
python -c "
from parsers.sunlife_parser import SunLifeParser
parser = SunLifeParser('statements/SunLife/sample.pdf')
data = parser.parse()
print(f'Account: {data[\"account_number\"]}')
print(f'Holdings: {len(data[\"holdings\"])}')
print(f'Total Value: {data[\"total_value\"]}')
"
```

## Key Design Patterns

### Parser Pattern Matching

The system uses a flexible pattern-matching approach in institutions.yaml:
- Match by parent directory name (e.g., statements/CIBC/ → CIBC parsers)
- Match by filename pattern (e.g., "pps" in filename → CIBCPPSParser)
- Fallback to "*" pattern for default parser
- First match wins

### Statement Data Structure

All parsers return a dictionary with standardized keys:
```python
{
    'institution': str,           # Required
    'account_number': str,        # Required
    'account_type': str,          # e.g., RRSP, TFSA, LIRA
    'statement_date': datetime,   # Required
    'period_start': datetime,
    'period_end': datetime,
    'total_value': float,
    'cash_balance': float,
    'holdings': [                 # List of holdings
        {
            'symbol': str,
            'security_name': str,
            'quantity': float,
            'price': float,
            'book_value': float,
            'market_value': float,
            'asset_type': str,     # Auto-classified
            'asset_category': str  # Auto-classified
        }
    ],
    'performance': {}             # Optional metrics
}
```

### Security Classification

The `classify_security()` method in BaseStatementParser automatically determines asset_type and asset_category based on security name:
- GIC detection (must come before other checks)
- ETF detection
- Index funds (Canadian, US, International, Global)
- Balanced funds
- Fixed income / bonds
- Equity funds
- Exempt market securities
- Default to Stock/Equity

### Database Connection Management

DatabaseManager uses connection pooling (minconn=1, maxconn=10):
- Always use try/finally to release connections
- Call close_all_connections() when done
- Transactions auto-commit on success, rollback on error

### Code Generation Workflow

When using the web interface to generate Python code:
1. Execute a natural language query
2. Check "Generate Python code"
3. System generates a method with proper typing, docstrings
4. Click "Add to portfolio_analyzer.py"
5. New method is appended to PortfolioAnalyzer class

## Important Constraints

### Parser Requirements

When creating or modifying parsers:
- MUST inherit from BaseStatementParser
- MUST implement: parse(), extract_account_info(), extract_holdings()
- MUST use pdfplumber for PDF extraction
- MUST return standardized statement_data dictionary
- MUST handle missing/optional fields gracefully
- Use utility methods: clean_currency_value(), parse_date(), classify_security()

### Database Safety

- Never commit .env file
- Always use parameterized queries
- Reset operations require explicit confirm=True
- Web interface only allows SELECT queries
- SQL validator prevents injection attacks

### Parser Generator Usage

- Requires ANTHROPIC_API_KEY environment variable
- Place 3-5 sample PDFs in statements/InstitutionName/
- Generated code should be reviewed before production use
- Analysis report saved to parsers/institutionname_analysis.md
- Cost: ~$0.50-$2.00 per parser (Claude Sonnet)

## File Organization

```
statements/                    # Place PDFs here (gitignored)
├── InstitutionName/          # One directory per institution
│   └── *.pdf

parsers/                       # Parser implementations
├── base_parser.py            # Abstract base class
└── *_parser.py               # Institution-specific parsers

database/
├── schema.sql                # PostgreSQL schema
└── db_manager.py             # Database operations

analysis/
└── portfolio_analyzer.py     # Analysis methods

visualization/
└── portfolio_visualizer.py   # Chart generation

web/                          # Flask web application
├── app.py                    # Main Flask app
├── nl_to_sql.py              # Natural language queries
├── code_generator.py         # Python code generation
└── templates/                # HTML templates

parser_generator/             # AI-assisted parser generation
└── agent.py                  # CrewAI agents

reports/                      # Generated reports (gitignored)
```

## Configuration Files

- `config.py` - Database config, paths, logging (reads from env vars)
- `.env` - Database credentials and API keys (gitignored)
- `institutions.yaml` - Parser configuration (pattern matching)
- `requirements.txt` - Python dependencies

## Python Virtual Environment

Always use the venv when running Python commands:
```bash
venv/bin/python process_statements.py process
venv/bin/pip install crewai
```

## LLM API Key Priority

For web interface natural language queries:
1. DeepSeek (DEEPSEEK_API_KEY) - Most cost-effective
2. OpenAI (OPENAI_API_KEY) - Alternative
3. Anthropic (ANTHROPIC_API_KEY) - Alternative
4. Fallback to rule-based converter (no API key needed)

For parser generation:
- Only Anthropic Claude supported (ANTHROPIC_API_KEY)
