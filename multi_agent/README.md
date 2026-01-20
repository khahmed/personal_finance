# Multi-Agent Financial Advisory System

This directory contains the implementation of the multi-agent financial advisory system as specified in `MULTI_AGENT_SPECIFICATION.md`.

## Structure

```
multi_agent/
├── agents/              # Core advisory agents
│   ├── base_agent.py
│   ├── portfolio_data_agent.py
│   ├── tax_advisor_agent.py
│   ├── estate_planner_agent.py
│   └── investment_analyst_agent.py
├── flows/              # Workflow orchestration
│   ├── financial_advisory_flow.py
│   └── workflow_orchestrator.py
├── tools/              # Agent tools
│   ├── database_tools.py
│   └── analysis_tools.py
├── schemas/            # Data schemas
│   ├── messages.py
│   ├── agent_outputs.py
│   └── workflow_state.py
├── sub_agents/         # Specialized sub-agents
└── config/             # Configuration files
    └── agent_config.yaml
```

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Optional: LLM Setup (for Enhanced Analysis)

The system supports LLM-enhanced analysis using Anthropic Claude or DeepSeek:

```bash
# For DeepSeek (recommended - cost-effective)
export DEEPSEEK_API_KEY="your-api-key"

# OR for Anthropic Claude
export ANTHROPIC_API_KEY="your-api-key"
```

See [LLM_SETUP.md](LLM_SETUP.md) for detailed configuration.

### Basic Usage

```python
from multi_agent.flows.financial_advisory_flow import FinancialAdvisoryFlow

# Initialize flow
flow = FinancialAdvisoryFlow()

# Set user context
user_context = {
    "tax_bracket": "mid",
    "tax_rate": 0.30,
    "province": "ON",
    "age": 55,
    "risk_profile": "moderate"
}

# Get comprehensive review
results = flow.get_comprehensive_review(user_context)
```

### Run Example

```bash
python -m multi_agent.main
```

## Agents

### Portfolio Data Agent
- Retrieves portfolio data from PostgreSQL
- Calculates portfolio metrics
- Provides data context to other agents

### Tax Advisor Agent
- Analyzes tax optimization opportunities
- Identifies tax-loss harvesting
- Recommends withdrawal strategies

### Estate Planner Agent
- Analyzes estate structure
- Calculates probate fees
- Recommends products and account optimization

### Investment Analyst Agent
- Analyzes securities
- Identifies concentration risk
- Provides buy/sell recommendations

## Workflows

### Sequential Workflow
Agents execute in sequence, each building on previous results.

### Parallel Workflow
Analysis agents execute in parallel for faster results.

## Configuration

Edit `config/agent_config.yaml` to customize agent behavior, models, and tools.

## Documentation

- [INSTALLATION.md](INSTALLATION.md) - Detailed installation guide
- [LLM_SETUP.md](LLM_SETUP.md) - LLM integration setup (Anthropic/DeepSeek)
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Troubleshooting guide
- [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md) - Implementation details

## Disclaimer

This system provides informational and educational analysis only. It does not constitute professional financial, tax, legal, or investment advice. Always consult with qualified professionals before making financial decisions.

