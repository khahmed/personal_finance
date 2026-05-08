# Multi-Agent Financial Advisory System

This directory contains the implementation of the multi-agent financial advisory system as specified in `MULTI_AGENT_SPECIFICATION.md` (in the repo root).

The system uses CrewAI-style agents that analyze portfolio data for tax optimization, estate planning, and investment recommendations. Agent configurations are stored in the database and self-evolve based on LLM critique of each run's outputs.

## Table of Contents

- [Structure](#structure)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [LLM Setup](#llm-setup)
- [Agents](#agents)
- [Workflows](#workflows)
- [CLI Usage](#cli-usage)
- [Configuration](#configuration)
- [Observability](#observability)
- [Troubleshooting](#troubleshooting)

## Structure

```
multi_agent/
├── agents/              # Core advisory agents
│   ├── base_agent.py
│   ├── portfolio_data_agent.py
│   ├── tax_advisor_agent.py
│   ├── estate_planner_agent.py
│   ├── investment_analyst_agent.py
│   └── meta_evolution_agent.py
├── flows/              # Workflow orchestration
│   ├── financial_advisory_flow.py
│   └── workflow_orchestrator.py
├── tools/              # Agent tools
│   ├── database_tools.py
│   ├── analysis_tools.py
│   └── llm_tools.py
├── schemas/            # Data schemas
│   ├── messages.py
│   ├── agent_outputs.py
│   └── workflow_state.py
├── observability/      # Observability hooks and collector
│   ├── events.py       # Span/event types
│   ├── collector.py    # In-memory session/span store
│   └── hooks.py        # start_span, end_span, record_llm_call, etc.
├── config/             # Configuration
│   ├── agent_config.yaml      # Static YAML (legacy, superseded by DB)
│   └── agent_config_store.py  # DB-backed config store (singleton)
└── main.py             # CLI entry point
```

## Installation

### Resolving Dependency Conflicts

CrewAI 0.28.8 requires `langchain>=0.1.10,<0.2.0`. If you encounter dependency conflicts:

1. **Recommended**: Let pip resolve dependencies automatically:
   ```bash
   pip install crewai==0.28.8
   pip install -r requirements.txt
   ```

2. **Or install in order**:
   ```bash
   pip install langchain>=0.1.10,<0.2.0
   pip install crewai==0.28.8
   pip install -r requirements.txt
   ```

3. **If conflicts persist**, use a fresh virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### Common Installation Issues

**langchain version conflict** — `crewai 0.28.8 depends on langchain<0.2.0 and >=0.1.10`. Remove any pinned `langchain==0.1.0` and use `langchain>=0.1.10,<0.2.0`.

**pydantic version conflict** — CrewAI works with pydantic 2.x. Ensure `pydantic>=2.0.0`.

**`ModuleNotFoundError: No module named 'pkg_resources'`** — Install setuptools (required for CrewAI's telemetry):
```bash
pip install setuptools>=65.0.0
```
This is included in `requirements.txt`.

**`ImportError: cannot import name 'BaseTool' from 'crewai.tools'`** — `BaseTool` is not available in CrewAI 0.28.8. The codebase already handles this by using direct method calls instead of CrewAI tool wrappers; tool imports are optional.

### Verification

```bash
pip show crewai langchain pydantic
```

Expected:
- `crewai`: 0.28.8
- `langchain`: >=0.1.10, <0.2.0
- `pydantic`: >=2.0.0

### Alternative: Let CrewAI Handle Dependencies

```bash
pip install crewai==0.28.8
pip install -r requirements.txt --no-deps
pip install crewai==0.28.8  # Reinstall to ensure compatibility
```

## Quick Start

### Basic Usage

```python
from multi_agent.flows.financial_advisory_flow import FinancialAdvisoryFlow

flow = FinancialAdvisoryFlow()

user_context = {
    "tax_bracket": "mid",
    "tax_rate": 0.30,
    "province": "ON",
    "age": 55,
    "risk_profile": "moderate"
}

results = flow.get_comprehensive_review(user_context)
```

### Run Example

```bash
python -m multi_agent.main
```

## LLM Setup

The system supports LLM-enhanced analysis using DeepSeek or Anthropic Claude. Without an LLM key, agents fall back to rule-based analysis.

### Option 1: DeepSeek (Recommended — Cost-Effective)

```bash
# Get an API key from https://platform.deepseek.com/
export DEEPSEEK_API_KEY="your-deepseek-api-key"

# DeepSeek uses an OpenAI-compatible API
pip install openai
```

### Option 2: Anthropic Claude

```bash
# Get an API key from https://console.anthropic.com/
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Already in requirements.txt
pip install anthropic langchain-anthropic
```

### Priority Order

The system checks for API keys in this order:
1. **DeepSeek** (if `DEEPSEEK_API_KEY` is set)
2. **Anthropic** (if `ANTHROPIC_API_KEY` is set and DeepSeek is not)

### LLM-Enhanced Output

When an LLM is available, agent outputs include an `llm_insights` field:

```python
{
    "tax_optimization_report": {...},
    "recommendations": [...],
    "llm_insights": {
        "explanation": "Natural language explanation of the analysis...",
        "recommendations": [
            {
                "priority": "High",
                "action": "Specific action to take",
                "rationale": "Why this recommendation",
                "impact": "Expected impact"
            }
        ],
        "llm_provider": "DeepSeek"
    }
}
```

### What LLM Enhances

- **Tax Advisor**: Natural-language explanations of tax strategies, additional context-aware recommendations.
- **Estate Planner**: Estate-planning strategy explanations, product suggestions, probate/beneficiary commentary.
- **Investment Analyst**: Portfolio health-score explanations, market context, actionable recommendations.

### Custom Model Selection

```python
from multi_agent.agents.tax_advisor_agent import TaxAdvisorAgent

agent = TaxAdvisorAgent(model="deepseek-chat")  # or "claude-3-opus-20240229"
```

### Disabling LLM

```bash
unset DEEPSEEK_API_KEY
unset ANTHROPIC_API_KEY
python -m multi_agent.main
```

The system works fully without an LLM — it just lacks the enhanced narrative insights.

### Cost Considerations

- **DeepSeek**: Very cost-effective, good for high-volume usage.
- **Anthropic**: Higher cost, excellent quality, best for critical analysis.

## Agents

### Portfolio Data Agent
- Retrieves portfolio data from PostgreSQL
- Calculates portfolio metrics
- Provides data context to other agents

### Tax Advisor Agent
- Analyzes tax optimization opportunities
- Identifies tax-loss harvesting candidates
- Recommends withdrawal strategies

### Estate Planner Agent
- Analyzes estate structure
- Calculates probate fees
- Recommends products and account optimization

### Investment Analyst Agent
- Analyzes securities
- Identifies concentration risk
- Provides buy/sell recommendations

### Meta Evolution Agent
- Critiques each run's outputs against the user context
- Proposes config improvements (role, prompts, business rules)
- Writes new versioned configs to the `agent_configs` table when confidence ≥ threshold

## Workflows

### Sequential Workflow
Agents execute in sequence, each building on previous results.

### Parallel Workflow
Analysis agents execute in parallel for faster results.

## CLI Usage

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

## Configuration

Each agent loads its `role`, `goal`, `backstory`, `system_prompts`, and `business_rules` from the `agent_configs` database table at init time, falling back to hardcoded constructor defaults if the DB is unavailable.

The `agent_configs` and `agent_interactions` tables are created and seeded by `database/schema.sql` (a single file initializes both portfolio tables and multi-agent evolution tables). They are also auto-created by `AgentConfigStore._ensure_tables()` on first use.

### Static config (legacy)

`config/agent_config.yaml` holds the original static configuration. It is superseded by the DB-backed store but kept as a reference and fallback.

### Rollback and Safety

- Configs are append-only: every evolution creates a new row, old rows are never deleted.
- `MetaEvolutionAgent.rollback_agent(agent_name, version)` reactivates any prior version.
- The `--history` CLI flag lists all versions with timestamps and reasons.
- Evolution only runs when an LLM API key is available; if no key is set, the step is silently skipped and the hardcoded defaults remain in effect.
- `MetaEvolutionAgent` is excluded from its own evolution loop.

## Observability

This module provides hooks to monitor the sequence of LLM calls and agent interactions.

### Features

- **Session tracking**: Each workflow run is a session with a unique ID.
- **Span hierarchy**: Workflow → Agent steps → LLM calls (nested under the active agent).
- **In-memory store**: Recent sessions and spans are kept in memory and exposed via API.
- **Web monitor**: Built-in monitor UI at `/monitor`.

### Viewing Traces in the Web App

1. Start the web app: `python -m web.app`
2. Open **http://localhost:5000/monitor**
3. Trigger a run (e.g. POST to `/api/v2/comprehensive-review` with `user_context`).
4. Refresh the monitor; select a session to see the timeline of spans.

### API

- `GET /api/observability/sessions` — List recent sessions (query: `limit`, default 50).
- `GET /api/observability/sessions/<session_id>` — Get one session with all spans (ordered by start time).

Responses include:
- **Session**: `session_id`, `query`, `workflow_type`, `start_time`, `end_time`, `status`, `span_count`, `spans`.
- **Span**: `span_id`, `session_id`, `parent_span_id`, `kind`, `name`, `start_time`, `end_time`, `duration_ms`, `metadata`, `error`.

### Span Kinds

- **workflow**: Root span for the whole run.
- **agent**: One agent step (e.g. `portfolio_data`, `tax_advisor`, `estate_planner`, `investment_analyst`).
- **llm_call**: A single LLM request (nested under the agent that made it).
- **agent_message**: Optional; for explicit "data passed from A to B" events.

### Extending with OpenTelemetry or Langfuse

The current implementation is an in-memory collector. You can extend it to export to standard observability backends.

**Option 1: OpenTelemetry**

1. Install: `pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp`
2. In `collector.py`, after `add_span()` (or in a separate exporter), create an OTLP span from each `Span` and export it.
3. Run a collector (e.g. Jaeger) that receives OTLP and view traces in Jaeger UI.

When `add_span(span)` is called, start an OpenTelemetry span with the same `name`, parent context from `parent_span_id`, and attributes from `metadata`. End it when `end_span(span_id)` is called.

**Option 2: Langfuse**

1. Install: `pip install langfuse`
2. Set `LANGFUSE_SECRET_KEY` and `LANGFUSE_PUBLIC_KEY` (optionally `LANGFUSE_HOST`).
3. In the observability hooks, create a Langfuse trace for the session and Langfuse spans for each workflow/agent/LLM span. Add generation spans for LLM calls (input/output, model, latency).

This keeps the existing in-memory collector and UI; you add a parallel export so you can use both.

### Implementation Notes

- **Context variables**: `set_current_context(session_id, parent_span_id)` is set by the workflow orchestrator before each agent step. LLM tools read this via `get_current_context()` so each LLM call is recorded under the current agent span.
- **Thread safety**: The in-memory collector uses a lock; safe for multi-threaded use.
- **Limits**: Defaults are 100 sessions and 500 spans per session; older sessions are dropped.

## Troubleshooting

### OPENAI_API_KEY Warnings

CrewAI tries to create agents with OpenAI by default, causing warnings about a missing API key. The codebase skips CrewAI Agent creation by default and uses direct method calls instead, so the warnings are harmless. To use CrewAI tasks/crews with Anthropic, set `ANTHROPIC_API_KEY` and uncomment the Agent creation code in `base_agent.py`.

### None Value Errors

`float() argument must be a string or a real number, not 'NoneType'` — already fixed. All value conversions handle `None` safely; `book_value` and `market_value` default to `0.0` when missing or invalid.

### Pydantic Validation Errors

`symbol` field is `None` when it should be a string — already fixed. All optional string fields use the `or ''` pattern (e.g. `symbol=holding.get('symbol') or ''`, `security_name=holding.get('security_name') or 'Unknown'`).

### pkg_resources Deprecation Warning

CrewAI dependency issue. Suppressed by pinning `setuptools<81.0.0` (already in `requirements.txt`). Will resolve when CrewAI updates upstream.

### Empty Results

Possible causes:
1. Database has no data
2. Holdings have `None` values for `book_value`/`market_value`
3. Date filters exclude all data

Check with:
```sql
SELECT COUNT(*) FROM holdings;
SELECT * FROM v_latest_holdings LIMIT 5;
SELECT COUNT(*) FROM holdings WHERE book_value IS NULL;
```

### LLM Not Being Used

1. **Check API key**:
   ```bash
   echo $DEEPSEEK_API_KEY  # or $ANTHROPIC_API_KEY
   ```

2. **Check logs** for messages like:
   ```
   Tax Advisor Agent: LLM available (DeepSeek)
   Tax Advisor Agent: Enhancing analysis with LLM
   ```

3. **Verify installation**:
   ```bash
   pip list | grep -E "(openai|anthropic)"
   ```

### API Errors

- **Rate Limits**: Both providers have rate limits. The system logs errors and continues with rule-based analysis.
- **Invalid Key**: Verify the API key is correct and has proper permissions.
- **Network Issues**: Confirm internet connectivity.

### Debugging

**Enable verbose logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Check database connection**:
```python
from database.db_manager import DatabaseManager
from config import DB_CONFIG

db = DatabaseManager(DB_CONFIG)
result = db.execute_query("SELECT 1", None, fetch=True)
print("Database OK" if result else "Database Error")
```

**Verify data**:
```python
from multi_agent.agents.portfolio_data_agent import PortfolioDataAgent

agent = PortfolioDataAgent()
summary = agent.get_portfolio_summary()
print(summary)
```

### Performance

If the system is slow:
1. Check database query performance
2. Reduce number of holdings analyzed
3. Use parallel workflow for independent analyses
4. Cache portfolio summary data

## Disclaimer

This system provides informational and educational analysis only. It does not constitute professional financial, tax, legal, or investment advice. Always consult with qualified professionals before making financial decisions.
