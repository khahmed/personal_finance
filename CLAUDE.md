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

**6. Multi-Agent Financial Advisory System** (`multi_agent/`)
- CrewAI-based system that runs tax, estate, and investment analysis agents over portfolio data
- Self-evolving at runtime: agent prompts and business rules are stored in the database and updated by `MetaEvolutionAgent` based on LLM critique of each run's outputs
- See [Multi-Agent Architecture](#multi-agent-architecture) section below for details

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

---

## Multi-Agent Architecture

### Directory layout

```
multi_agent/
├── agents/
│   ├── base_agent.py              # BaseAgent – loads config from DB at init
│   ├── portfolio_data_agent.py    # Retrieves and aggregates portfolio data
│   ├── tax_advisor_agent.py       # Tax optimization analysis
│   ├── estate_planner_agent.py    # Estate planning analysis
│   ├── investment_analyst_agent.py # Investment analysis and rebalancing
│   └── meta_evolution_agent.py    # ← NEW: evaluates outputs, evolves configs
├── config/
│   ├── agent_config.yaml          # Static YAML (legacy, superseded by DB)
│   └── agent_config_store.py      # ← NEW: DB-backed config store (singleton)
├── flows/
│   ├── workflow_orchestrator.py   # Coordinates agent execution + evolution step
│   └── financial_advisory_flow.py # High-level entry point
├── tools/
│   ├── database_tools.py          # Portfolio DB queries
│   ├── analysis_tools.py          # Calculation helpers
│   └── llm_tools.py               # DeepSeek / Anthropic wrappers
├── schemas/
│   ├── agent_outputs.py           # Pydantic output models
│   └── workflow_state.py          # WorkflowState, UserContext
├── observability/                 # Session/span tracking
└── main.py                        # CLI entry point
```

### Self-evolution design

Each agent loads its `role`, `goal`, `backstory`, `system_prompts`, and
`business_rules` from the `agent_configs` database table at **init time**,
falling back to hardcoded constructor defaults if the DB is unavailable.

After every workflow run, `MetaEvolutionAgent.evaluate_and_evolve()` is called
as a post-workflow step. It:

1. Logs each agent's output summary + user feedback to `agent_interactions`.
2. Once the interaction count threshold is met, asks the LLM to critique the
   outputs against the user context and propose specific improvements.
3. For proposals above the confidence threshold (default 0.7), writes a new
   versioned config row to `agent_configs` (old version deactivated).
4. The next workflow run automatically picks up the evolved config.

```
Run N → agents load config vX from DB
      → analysis executes
      → MetaEvolutionAgent critiques outputs
      → writes vX+1 to agent_configs (if confidence ≥ threshold)

Run N+1 → agents load config vX+1 from DB  ← evolved
```

### Database tables (agent evolution)

Schema lives in `database/schema.sql` alongside the portfolio tables (one file initializes the entire database):

| Table | Purpose |
|---|---|
| `agent_configs` | Versioned agent configurations. `is_active=TRUE` row is loaded at runtime. |
| `agent_interactions` | Per-session output summaries + user feedback for evolution decisions. |

### Business rules pattern

Each domain agent defines `_DEFAULT_RULES` as a module-level dict with all
threshold values. At init, these are merged with whatever the DB provides:

```python
self.business_rules = {**_DEFAULT_RULES, **self.business_rules}
```

Agents then read thresholds through `self._rule("key")` instead of magic
numbers, making them evolvable without code changes.

| Agent | Key evolvable rules |
|---|---|
| TaxAdvisorAgent | `inclusion_rate`, `default_tax_rate`, `min_loss_threshold` |
| EstatePlannerAgent | `equity_threshold_pct`, `fixed_income_threshold_pct`, `equity_etf_allocation_pct` |
| InvestmentAnalystAgent | `overweight_threshold_pct`, `target_allocation_pct`, `health_score_base` |
| MetaEvolutionAgent | `min_interactions_before_evolution`, `min_confidence_to_evolve` |

### CLI usage

```bash
# Standard run (evolution enabled)
venv/bin/python -m multi_agent.main

# Disable evolution (faster, no DB writes)
venv/bin/python -m multi_agent.main --no-evolution

# Pass explicit feedback that informs evolution
venv/bin/python -m multi_agent.main --feedback accepted

# Parallel workflow
venv/bin/python -m multi_agent.main --parallel

# Show config version history for all agents
venv/bin/python -m multi_agent.main --history

# Roll back TaxAdvisorAgent to version 1
venv/bin/python -m multi_agent.main --rollback TaxAdvisorAgent --version 1
```

### Setting up the evolution tables

The `agent_configs` and `agent_interactions` tables are created and seeded by
`database/schema.sql` (a single file now initializes both the portfolio tables
and the multi-agent evolution tables). They are also auto-created by
`AgentConfigStore._ensure_tables()` on first use, so manual SQL is only needed
for fresh database setup or bulk inspection.

### Rollback and safety

- Configs are **append-only**: every evolution creates a new row, old rows are
  never deleted.
- `MetaEvolutionAgent.rollback_agent(agent_name, version)` reactivates any
  prior version.
- The `--history` CLI flag lists all versions with timestamps and reasons.
- Evolution only runs when an LLM API key is available; if no key is set the
  step is silently skipped and the hardcoded defaults remain in effect.
- `MetaEvolutionAgent` is excluded from its own evolution loop.

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
