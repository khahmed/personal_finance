# Portfolio Web Interface

A web interface for portfolio querying and analysis, with two modes:

1. **SQL Queries Mode** — Natural language to SQL conversion for direct database queries.
2. **Multi-Agent Analysis Mode** — Comprehensive financial analysis using specialized AI agents (Tax, Estate, Investment).

## Table of Contents

- [Features](#features)
- [Setup](#setup)
- [Running the Application](#running-the-application)
- [Usage](#usage)
  - [SQL Queries Mode](#sql-queries-mode)
  - [Multi-Agent Analysis Mode](#multi-agent-analysis-mode)
- [API Endpoints](#api-endpoints)
  - [v1 — SQL Mode](#v1--sql-mode)
  - [v2 — Multi-Agent Mode](#v2--multi-agent-mode)
- [Architecture](#architecture)
- [Security](#security)
- [Troubleshooting](#troubleshooting)

## Features

- **Natural Language Queries**: Ask portfolio questions in plain English.
- **Automatic SQL Generation**: LLM-powered (DeepSeek, OpenAI, or Anthropic) NL-to-SQL conversion.
- **Safe Query Execution**: SQL validator restricts to SELECT only, with parameterized queries.
- **Code Generation**: Generate Python methods for `analysis/portfolio_analyzer.py` from queries.
- **Multi-Agent Analysis**: Tax, estate, and investment recommendations driven by user context.
- **Modern UI**: Clean, responsive interface with example queries and dual-mode toggle.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

For multi-agent mode, also ensure:
```bash
pip install crewai langchain pydantic
```

### 2. Configure API Keys (Optional but Recommended)

Priority order: **DeepSeek > OpenAI > Anthropic**.

```bash
# DeepSeek (recommended — cost-effective)
export DEEPSEEK_API_KEY="your-api-key-here"

# OR OpenAI
export OPENAI_API_KEY="your-api-key-here"

# OR Anthropic
export ANTHROPIC_API_KEY="your-api-key-here"
```

Without an API key, SQL mode falls back to a rule-based generator (less accurate). Multi-agent mode falls back to rule-based analysis (no LLM insights).

### 3. Configure Database

Set credentials in `config.py` or via environment variables:

```bash
export DB_HOST=localhost
export DB_NAME=portfolio_db
export DB_USER=bankapp
export DB_PASSWORD=your-password
export DB_PORT=5432
```

## Running the Application

```bash
# From repo root
python -m web.app

# Or
cd web && python app.py

# Or use the startup script
./run_web_app.sh
```

The application will be available at `http://localhost:5000`.

## Usage

### SQL Queries Mode

1. Enter a natural language query.
2. Click **Execute Query** (or press Ctrl+Enter).
3. View the generated SQL and results.

**Example queries:**
- "Show me my current portfolio allocation by asset category"
- "What are my top 10 holdings by value?"
- "Show me portfolio value over the last 6 months"
- "What is my total portfolio value?"
- "Show me holdings for Scotiabank accounts"
- "What is my allocation by institution?"

**Generating reusable code:**

1. Execute a query.
2. Check **Generate Python code for this query** (or click **Generate Code**).
3. Review the generated method.
4. Click **Add to portfolio_analyzer.py** to append it to `analysis/portfolio_analyzer.py`.

### Multi-Agent Analysis Mode

Toggle to **Multi-Agent Analysis** in the UI. Fill out the user context form (tax rate, province, age, risk profile), then choose an analysis type.

**Analysis types:**
- **Comprehensive Review** — All agents (Tax + Estate + Investment).
- **Tax Analysis** — Tax optimization and loss harvesting.
- **Estate Planning** — Product recommendations and structure.
- **Investment Analysis** — Securities analysis and rebalancing.
- **Portfolio Data** — Structured data access.

**Natural-language queries**: A free-form text area sends complex questions through the agents using the user context.

**Results display**: Cards show portfolio summary metrics, agent-specific analysis, prioritized recommendations, and LLM insights (when an LLM key is configured).

#### Performance Notes

- Comprehensive Review: ~5–10 seconds (sequential execution of 4 agents).
- Individual analysis: ~2–3 seconds.
- Portfolio Data: <1 second (direct DB access).

#### Portfolio Data Agent vs. Direct SQL

| Feature | SQL Mode | Portfolio Data Agent |
|---------|----------|---------------------|
| Query Type | Natural language → SQL | Pre-built methods |
| Data Access | Direct SELECT queries | Agent abstraction |
| Calculations | Basic aggregations | Full analytics |
| Context | Query results only | Data + business logic |
| Safety | SQL validator | Parameterized + validated |

## API Endpoints

### v1 — SQL Mode

#### `POST /api/query`
Execute a natural language query.

**Request:**
```json
{
  "query": "Show me my top holdings",
  "generate_code": false
}
```

**Response:**
```json
{
  "sql": "SELECT ...",
  "params": [],
  "data": [...],
  "row_count": 10,
  "columns": ["security_name", "market_value", ...],
  "explanation": "...",
  "generated_code": "..."
}
```

#### `POST /api/generate_code`
Generate Python code for a SQL query.

**Request:**
```json
{
  "method_name": "get_custom_analysis",
  "description": "Custom analysis",
  "sql": "SELECT ...",
  "add_to_file": false,
  "return_type": "pd.DataFrame"
}
```

#### `GET /api/schema`
Get database schema information.

#### `GET /api/examples`
Get example queries.

### v2 — Multi-Agent Mode

#### `POST /api/v2/comprehensive-review`
Run all agents (Tax, Estate, Investment) and return a combined report.

**Request:**
```json
{
  "user_context": {
    "tax_rate": 0.30,
    "province": "ON",
    "age": 55,
    "risk_profile": "moderate"
  }
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "portfolio_data": { ... },
  "tax_analysis": { ... },
  "estate_analysis": { ... },
  "investment_analysis": { ... },
  "workflow_state": { ... }
}
```

#### `POST /api/v2/agent-query`
Process a natural-language query through the multi-agent system.

**Request:**
```json
{
  "query": "What's the most tax-efficient way to withdraw $50,000?",
  "user_context": {
    "tax_rate": 0.30,
    "province": "ON"
  },
  "workflow_type": "sequential"
}
```

#### `GET /api/v2/portfolio-data`
Get structured portfolio data from the Portfolio Data Agent.

**Query parameters:**
- `institution` (optional)
- `account_number` (optional)
- `action`: `get_all`, `get_summary`, `get_holdings`, `get_allocation`

#### `POST /api/v2/tax-analysis`
Tax optimization analysis.

```json
{
  "user_context": {
    "tax_rate": 0.30,
    "province": "ON",
    "age": 55
  }
}
```

#### `POST /api/v2/estate-analysis`
Estate planning analysis.

```json
{
  "user_context": {
    "province": "ON",
    "age": 55,
    "marital_status": "married",
    "dependents": 2
  }
}
```

#### `POST /api/v2/investment-analysis`
Investment analysis and rebalancing recommendations.

```json
{
  "user_context": {
    "risk_profile": "moderate",
    "investment_goals": ["retirement", "growth"]
  }
}
```

### API Testing with curl

```bash
# Comprehensive review
curl -X POST http://localhost:5000/api/v2/comprehensive-review \
  -H "Content-Type: application/json" \
  -d '{
    "user_context": {
      "tax_rate": 0.30,
      "province": "ON",
      "age": 55,
      "risk_profile": "moderate"
    }
  }'

# Portfolio data
curl http://localhost:5000/api/v2/portfolio-data?action=get_summary

# Tax analysis
curl -X POST http://localhost:5000/api/v2/tax-analysis \
  -H "Content-Type: application/json" \
  -d '{"user_context": {"tax_rate": 0.30, "province": "ON"}}'
```

## Architecture

```
web/
├── app.py                 # Flask app: v1 SQL endpoints + v2 multi-agent endpoints
├── nl_to_sql.py           # Natural language → SQL converter
├── sql_validator.py       # SQL safety validator (SELECT-only)
├── code_generator.py      # Python code generator for analysis methods
├── templates/
│   └── index.html         # Frontend (dual-mode UI)
└── static/
    ├── css/style.css      # Styling
    └── js/app.js          # Frontend JavaScript
```

The multi-agent system **preserves** all existing SQL functionality. Mode switching is seamless. If the `multi_agent` package is not installed, SQL mode continues to work (progressive enhancement).

### Key Design Decisions

- **Dual-mode interface**: SQL mode is preserved alongside multi-agent mode so users can pick the right tool for the question.
- **User context form**: Collected once per session and reused across agent calls.
- **Individual vs. comprehensive**: Users can request a single agent (fast, focused) or the full review (slower, complete picture).
- **Progressive enhancement**: Multi-agent endpoints return 503 if the package is missing — the rest of the app keeps working.

## Security

- Only SELECT queries allowed in SQL mode.
- SQL injection protection via validator + parameterized queries.
- Read-only database access for agents.
- No DROP, DELETE, INSERT, UPDATE, or other destructive operations.
- API keys stored in environment variables, not in code.
- All endpoints validate user input.

## Troubleshooting

### Network Error: "NetworkError when attempting to fetch resource"

The frontend cannot reach the backend. Work through the steps below.

**1. Check if the server is running**

```bash
# Is port 5000 in use?
lsof -i :5000
# or
netstat -tuln | grep 5000

# Start the server
python -m web.app
# or
./run_web_app.sh
```

Expected output:
```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

**2. Check server logs**

Look in the Flask terminal for:

- *Database connection error*: Verify `config.py` or environment variables.
- *Import errors*: `pip install -r requirements.txt`.

**3. Check browser console**

Open DevTools (F12):
- **Console tab** — JavaScript errors.
- **Network tab** — confirm `/api/query` requests return 200, with the right URL.

**4. Verify URL configuration**

In `web/static/js/app.js` line 3:
```javascript
const API_BASE = '/api';
```

If the frontend and backend are on different origins, change to:
```javascript
const API_BASE = 'http://localhost:5000/api';
```

**5. Test the backend directly**

```bash
curl http://localhost:5000/

curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is my total portfolio value?"}'
```

**6. CORS issues**

The app already configures `CORS(app)`. If you still see CORS errors in the browser, verify the configuration is taking effect.

**7. Database connection**

```bash
sudo systemctl status postgresql
# or
pg_isready

python -c "from database.db_manager import DatabaseManager; from config import DB_CONFIG; db = DatabaseManager(DB_CONFIG); print('Connected!')"
```

**8. Port already in use**

Change the port in `web/app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

Or kill the process holding port 5000:
```bash
lsof -ti:5000 | xargs kill -9
```

**9. Firewall (remote access)**

```bash
sudo ufw allow 5000
```

### Common Error Messages

| Error Message | Solution |
|---|---|
| "Database manager not initialized" | Check database connection in `config.py` |
| "ModuleNotFoundError: No module named 'X'" | `pip install -r requirements.txt` |
| "Connection refused" | Server is not running — start the Flask app |
| "CORS policy" | Check CORS configuration in `app.py` |
| "Timeout" | Database is slow or unresponsive |
| "No module named 'flask'" | `pip install -r requirements.txt` |
| "API key not found" | Optional — system falls back to rule-based; add a key for better results |

### Multi-Agent–Specific Issues

**"Multi-agent system not available"**
```bash
pip install crewai langchain pydantic
```

**LLM insights not showing**: Set an LLM API key.
```bash
export DEEPSEEK_API_KEY="your-key"
```

**Agents taking too long (>30s)**:
- Use individual analyses instead of comprehensive review.
- Check database performance.
- Verify network connectivity to the LLM provider.

See `multi_agent/README.md` for deeper multi-agent troubleshooting.

### Generated SQL Is Incorrect

- Try rephrasing your query.
- Be more specific about what you want.
- Check the example queries for patterns.
- Configure an LLM API key for better results.

### Quick Diagnostic Script

```bash
#!/bin/bash
echo "Checking Flask server..."
curl -s http://localhost:5000/ > /dev/null && echo "✓ Server running" || echo "✗ Server not running"

echo "Checking database..."
python -c "from database.db_manager import DatabaseManager; from config import DB_CONFIG; DatabaseManager(DB_CONFIG)" 2>/dev/null && echo "✓ Database OK" || echo "✗ Database failed"

echo "Checking dependencies..."
python -c "import flask, pandas, psycopg2" 2>/dev/null && echo "✓ Dependencies installed" || echo "✗ Missing dependencies"
```

### Verbose Logging

In `web/app.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

### Other Checks

- **Python version**: 3.7+ (`python --version`)
- **File permissions**: All files readable
- **Test query**: Try "What is my total portfolio value?" first
