# Multi-Agent Financial Advisory System Specification

**Version:** 1.0
**Date:** 2026-01-07
**Status:** Draft
**Framework:** CrewAI
**Protocol Standards:** MCP (Model Context Protocol), A2A (Agent-to-Agent Protocol)

---

## 1. Executive Summary

This specification defines a multi-agent AI system for comprehensive financial portfolio analysis and advisory services. The system analyzes data from a PostgreSQL database containing holdings, statements, securities, and account information to provide tax-efficient strategies, estate planning recommendations, and investment analysis.

### 1.1 System Purpose

Provide automated, intelligent financial advisory services across three core domains:
- **Tax Optimization**: Analyze portfolio for tax-efficient asset disposal strategies
- **Estate Planning**: Recommend optimal product allocation and succession planning
- **Investment Analysis**: Research securities and provide buy/sell recommendations

### 1.2 Design Philosophy

Following 2025-2026 best practices for multi-agent systems:
- **Hybrid Coordinator-Worker Pattern**: Central orchestrator with specialized domain agents
- **Event-Driven Communication**: Standardized JSON message exchange between agents
- **Modular Architecture**: Independent agents with clear role boundaries
- **Interoperability**: MCP-compliant data source connections
- **Safety-First**: Human-in-the-loop for critical financial decisions

---

## 2. System Architecture

### 2.1 Architecture Pattern

**Pattern Type:** Hybrid Coordinator-Worker with Collaborative Peer Groups

```
┌─────────────────────────────────────────────────────────────┐
│                    Financial Advisory Flow                   │
│                   (CrewAI Flow Controller)                   │
└───────────────┬─────────────────────────────────────────────┘
                │
                ├─── State Management
                ├─── Event Routing
                └─── Workflow Orchestration
                │
    ┌───────────┴──────────┬──────────────┬─────────────────┐
    │                      │              │                 │
┌───▼────────────┐  ┌──────▼─────┐  ┌────▼──────────┐  ┌──▼─────────────┐
│ Portfolio      │  │ Tax        │  │ Estate        │  │ Investment     │
│ Data Agent     │  │ Advisor    │  │ Planner       │  │ Analyst        │
│                │  │ Agent      │  │ Agent         │  │ Agent          │
└────┬───────────┘  └──────┬─────┘  └────┬──────────┘  └──┬─────────────┘
     │                     │              │                │
     │  ┌──────────────────┴──────────────┴────────────────┤
     │  │                                                   │
     └──►  Sub-Agents and Tools Layer                     │
          ├─ Data Retrieval Tools (MCP-compliant)         │
          ├─ Tax Calculator Sub-Agent                     │
          ├─ Market Research Sub-Agent                    │
          ├─ Risk Assessment Sub-Agent                    │
          └─ Regulatory Compliance Sub-Agent              │
                                                           │
                    ┌──────────────────────────────────────┘
                    │
        ┌───────────▼────────────┐
        │  PostgreSQL Database   │
        │  (via MCP Connection)  │
        └────────────────────────┘
```

### 2.2 Component Layers

#### Layer 1: Flow Controller
- **Purpose**: Orchestrate multi-agent workflows, manage state, handle events
- **Technology**: CrewAI Flows
- **Responsibilities**:
  - User request interpretation
  - Agent task delegation
  - Response aggregation
  - Error handling and recovery
  - Audit trail generation

#### Layer 2: Core Advisory Agents
- **Purpose**: Specialized domain expertise and analysis
- **Pattern**: Collaborative agents with defined roles
- **Communication**: Event-driven, JSON-based messaging

#### Layer 3: Sub-Agents and Tools
- **Purpose**: Focused task execution and data retrieval
- **Pattern**: Worker agents and tool integrations
- **Standards**: MCP for data connections

---

## 3. Agent Specifications

### 3.1 Portfolio Data Agent

**Role:** Data Specialist and Context Provider
**Type:** Core Infrastructure Agent
**Priority:** Critical Path (Required for all workflows)

#### Responsibilities
1. Query PostgreSQL database for portfolio holdings, statements, and account data
2. Aggregate and normalize data across multiple institutions and account types
3. Calculate current portfolio metrics (allocation, concentration, diversification)
4. Provide data context to other agents
5. Maintain data consistency and validation

#### Capabilities
- Execute complex SQL queries via database/db_manager.py
- Leverage existing portfolio_analyzer.py methods
- Calculate real-time portfolio statistics
- Historical data retrieval and trend analysis
- Account-level and portfolio-level aggregation

#### Inputs
- User query context (account filters, date ranges, specific securities)
- Agent data requests (from Tax, Estate, Investment agents)

#### Outputs
```json
{
  "portfolio_summary": {
    "total_value": float,
    "num_accounts": int,
    "num_securities": int,
    "total_gain_loss": float,
    "total_gain_loss_pct": float,
    "by_institution": {},
    "by_asset_category": {}
  },
  "holdings": [
    {
      "security_name": string,
      "symbol": string,
      "account_type": string,
      "institution": string,
      "quantity": float,
      "price": float,
      "book_value": float,
      "market_value": float,
      "gain_loss": float,
      "gain_loss_pct": float,
      "asset_category": string,
      "holding_date": date
    }
  ],
  "allocation": {},
  "concentration_metrics": {},
  "diversification_metrics": {}
}
```

#### Tools and Integrations
- **Database Connection**: MCP-compliant PostgreSQL connector
- **Analyzer Methods**: PortfolioAnalyzer class methods
- **Data Validation**: SQL injection prevention, type checking

#### Performance Requirements
- Query response time: < 2 seconds for standard queries
- Support for concurrent data requests from multiple agents
- Caching strategy for frequently accessed data

---

### 3.2 Tax Advisor Agent

**Role:** Tax Optimization Specialist
**Type:** Domain Expert Agent
**Expertise:** Canadian tax law (RRSP, TFSA, LIRA, taxable accounts)

#### Responsibilities
1. Analyze capital gains/losses across all holdings
2. Recommend tax-efficient asset disposal strategies
3. Identify tax-loss harvesting opportunities
4. Optimize withdrawals across registered and non-registered accounts
5. Calculate tax implications of proposed transactions
6. Consider account type tax treatment (RRSP, TFSA, LIRA, non-registered)

#### Canadian Tax Context
- **RRSP (Registered Retirement Savings Plan)**: Tax-deferred growth, taxed on withdrawal
- **TFSA (Tax-Free Savings Account)**: Tax-free growth and withdrawals
- **LIRA (Locked-In Retirement Account)**: Restricted access, tax-deferred
- **Non-Registered**: Capital gains taxed at 50% inclusion rate

#### Capabilities
- Capital gains/loss calculation per security and account
- Tax bracket optimization for withdrawals
- Multi-year tax planning scenarios
- Superficial loss rule detection (30-day rule)
- Foreign withholding tax analysis

#### Inputs
- Portfolio holdings with book values and market values
- User's tax situation (income level, province, tax bracket)
- Planned withdrawal amounts and timing
- Historical transaction data

#### Outputs
```json
{
  "tax_optimization_report": {
    "summary": {
      "total_unrealized_gains": float,
      "total_unrealized_losses": float,
      "estimated_tax_liability": float,
      "potential_tax_savings": float
    },
    "recommendations": [
      {
        "priority": string,
        "action": string,
        "security": string,
        "account": string,
        "rationale": string,
        "tax_impact": float,
        "timing": string
      }
    ],
    "tax_loss_harvesting": [
      {
        "security": string,
        "unrealized_loss": float,
        "tax_benefit": float,
        "superficial_loss_warning": boolean
      }
    ],
    "withdrawal_strategy": {
      "account_order": [],
      "estimated_tax_by_account": {}
    }
  }
}
```

#### Sub-Agents
1. **Tax Calculator Sub-Agent**
   - Calculate federal and provincial tax
   - Apply current tax brackets and rates
   - Consider OAS clawback implications

2. **Regulatory Compliance Sub-Agent**
   - Verify superficial loss rules
   - Check contribution room (RRSP, TFSA)
   - Validate LIRA withdrawal restrictions

#### Tools and Integrations
- CRA tax bracket data (via API or static reference)
- Provincial tax rate tables
- Tax calculation libraries
- Date-based rule engines for timing

#### Decision Criteria
- Minimize overall tax liability
- Preserve TFSA contribution room
- Optimize RRSP deduction timing
- Balance current vs. future tax rates
- Consider estate tax implications

#### Constraints and Limitations
- Requires user input for income and tax bracket
- Cannot provide personalized tax advice (requires CPA disclaimer)
- Tax laws subject to annual changes
- Provincial variations in tax treatment

---

### 3.3 Estate Planner Agent

**Role:** Estate Planning Specialist
**Type:** Domain Expert Agent
**Expertise:** Estate planning, product recommendations, beneficiary optimization

#### Responsibilities
1. Analyze current account structure and beneficiary designations
2. Recommend optimal product types for estate efficiency
3. Suggest account type rebalancing for succession planning
4. Identify probate-minimization opportunities
5. Recommend insurance and annuity products where appropriate
6. Consider age, family situation, and legacy goals

#### Capabilities
- Account structure analysis across institutions
- Beneficiary designation optimization
- Product suitability assessment
- Estate value projection and tax estimation
- Probate fee calculation by province
- Insurance needs analysis

#### Inputs
- Complete portfolio holdings and account types
- User demographic information (age, marital status, dependents)
- Current beneficiary designations (if available)
- Estate planning goals and legacy intentions
- Expected future contributions/withdrawals

#### Outputs
```json
{
  "estate_planning_report": {
    "summary": {
      "total_estate_value": float,
      "estimated_probate_fees": float,
      "estate_tax_estimate": float,
      "accounts_with_beneficiaries": int,
      "accounts_without_beneficiaries": int
    },
    "recommendations": [
      {
        "priority": string,
        "category": string,
        "action": string,
        "rationale": string,
        "estate_benefit": string,
        "implementation_steps": []
      }
    ],
    "product_recommendations": [
      {
        "product_type": string,
        "allocation_percentage": float,
        "account_type": string,
        "rationale": string,
        "risk_level": string,
        "tax_treatment": string
      }
    ],
    "account_structure_optimization": {
      "current_structure": {},
      "recommended_structure": {},
      "rebalancing_steps": []
    }
  }
}
```

#### Product Recommendation Categories
1. **Cash/GIC**: Emergency fund, short-term needs, capital preservation
2. **Fixed Income**: Bond funds, ETFs for income generation
3. **Balanced Funds**: Risk-adjusted growth for moderate investors
4. **Equity Funds/ETFs**: Long-term growth, diversification
5. **Index Funds**: Low-cost passive investing
6. **Alternative Investments**: Real estate, private equity (if suitable)
7. **Insurance Products**: Life insurance, annuities for income security

#### Sub-Agents
1. **Product Research Sub-Agent**
   - Research fund performance, fees, and characteristics
   - Compare similar products across institutions
   - Analyze MER (Management Expense Ratio)

2. **Risk Assessment Sub-Agent**
   - Calculate portfolio risk metrics
   - Assess suitability based on user profile
   - Stress testing and scenario analysis

#### Tools and Integrations
- Probate fee calculators by province
- Product database (mutual funds, ETFs, insurance)
- Risk profiling questionnaires
- Mortality tables and life expectancy data

#### Decision Criteria
- Minimize probate fees and estate taxes
- Ensure adequate liquidity for estate settlement
- Match product risk to user risk tolerance
- Optimize for beneficiary tax treatment
- Consider investment time horizon
- Balance growth vs. income needs

#### Constraints and Limitations
- Cannot act as licensed financial advisor (disclosure required)
- Product recommendations are educational, not personalized advice
- Must consider provincial estate law variations
- Insurance recommendations require user medical/insurability context

---

### 3.4 Investment Analyst Agent

**Role:** Securities Research and Portfolio Optimization Specialist
**Type:** Domain Expert Agent
**Expertise:** Security analysis, market research, buy/sell recommendations

#### Responsibilities
1. Analyze individual securities in the portfolio
2. Research market trends and sector performance
3. Provide buy/sell/hold recommendations with rationale
4. Identify overweight/underweight positions
5. Assess portfolio concentration risk
6. Monitor security-specific news and events
7. Compare holdings against benchmark indices

#### Capabilities
- Security-level fundamental and technical analysis
- Market data retrieval and trend analysis
- Sector and industry comparison
- Portfolio optimization modeling
- Rebalancing recommendations
- Risk-adjusted performance metrics

#### Inputs
- Current portfolio holdings and allocation
- Historical performance data
- User investment objectives and risk tolerance
- Market data (prices, volumes, fundamentals)
- News and analyst reports for securities

#### Outputs
```json
{
  "investment_analysis_report": {
    "summary": {
      "portfolio_health_score": float,
      "overweight_positions": [],
      "underweight_positions": [],
      "concentration_risk_level": string,
      "rebalancing_urgency": string
    },
    "security_recommendations": [
      {
        "security_name": string,
        "symbol": string,
        "current_allocation_pct": float,
        "recommendation": string,
        "action": string,
        "target_allocation_pct": float,
        "rationale": string,
        "risk_factors": [],
        "confidence_level": string,
        "timeframe": string
      }
    ],
    "sector_analysis": {
      "current_exposure": {},
      "benchmark_exposure": {},
      "recommendations": []
    },
    "rebalancing_plan": [
      {
        "security": string,
        "action": string,
        "quantity": float,
        "estimated_value": float,
        "reason": string
      }
    ],
    "market_context": {
      "market_conditions": string,
      "relevant_trends": [],
      "risk_warnings": []
    }
  }
}
```

#### Sub-Agents
1. **Market Research Sub-Agent**
   - Fetch real-time and historical market data
   - Access financial APIs (Alpha Vantage, Yahoo Finance, etc.)
   - Parse and summarize financial news
   - Analyst consensus and ratings aggregation

2. **Risk Assessment Sub-Agent**
   - Calculate beta, volatility, Sharpe ratio
   - Correlation analysis between holdings
   - Drawdown analysis
   - Value-at-Risk (VaR) calculations

3. **Sector Analysis Sub-Agent**
   - Classify securities by sector/industry
   - Compare sector weights to benchmarks
   - Identify sector rotation opportunities

#### Tools and Integrations
- **Market Data APIs**:
  - Alpha Vantage (free tier available)
  - Yahoo Finance API
  - Financial Modeling Prep
- **News Aggregation**:
  - NewsAPI
  - Financial news RSS feeds
- **Analysis Libraries**:
  - pandas, numpy for quantitative analysis
  - yfinance for historical data
  - Portfolio optimization libraries

#### Decision Criteria
- Risk-adjusted returns (Sharpe, Sortino ratios)
- Correlation with existing holdings (diversification)
- Valuation metrics (P/E, P/B, dividend yield)
- Technical indicators (moving averages, RSI, momentum)
- Analyst consensus and price targets
- Sector/industry trends
- Company fundamentals (revenue growth, profitability)

#### Recommendation Framework
- **Strong Buy**: High conviction, undervalued, positive momentum
- **Buy**: Attractive valuation, fits portfolio strategy
- **Hold**: Fair value, no immediate action needed
- **Reduce**: Overweight position, rebalancing needed
- **Sell**: Overvalued, deteriorating fundamentals, risk factors

#### Constraints and Limitations
- Not a registered investment advisor (disclosure required)
- Historical performance does not guarantee future results
- Market data may have delays (depends on data source)
- Cannot execute trades (recommendation only)
- Requires external API keys for comprehensive analysis

---

## 4. Agent Interaction Patterns

### 4.1 Communication Protocol

All agents communicate via standardized JSON messages using event-driven patterns.

#### Message Structure
```json
{
  "message_id": "uuid",
  "timestamp": "ISO-8601",
  "from_agent": "agent_name",
  "to_agent": "agent_name",
  "message_type": "request|response|event|error",
  "priority": "high|medium|low",
  "payload": {
    "action": "string",
    "data": {},
    "context": {}
  },
  "correlation_id": "uuid",
  "metadata": {
    "user_session": "string",
    "workflow_id": "string"
  }
}
```

#### Message Types
1. **Request**: Agent requesting data or analysis from another agent
2. **Response**: Agent responding to a request
3. **Event**: Notification of state change or completed action
4. **Error**: Error condition requiring handling

### 4.2 Workflow Patterns

#### Pattern 1: Sequential Analysis
User requests comprehensive financial review.

```
Flow Controller
    → Portfolio Data Agent (gather data)
    → Tax Advisor Agent (analyze with context)
    → Estate Planner Agent (analyze with context + tax insights)
    → Investment Analyst Agent (analyze with full context)
    → Flow Controller (aggregate and present)
```

#### Pattern 2: Parallel Analysis
User requests multi-domain analysis with independent tasks.

```
Flow Controller
    → Portfolio Data Agent (gather data)
    → [Parallel Execution]
        ├─ Tax Advisor Agent
        ├─ Estate Planner Agent
        └─ Investment Analyst Agent
    → Flow Controller (aggregate and reconcile)
```

#### Pattern 3: Collaborative Refinement
Agents iterate and refine each other's recommendations.

```
Flow Controller
    → Portfolio Data Agent
    → Tax Advisor Agent (initial analysis)
    ─→ Estate Planner Agent (considers tax implications)
    ─→ Investment Analyst Agent (considers tax + estate)
    ─→ Tax Advisor Agent (refines based on investment changes)
    → Flow Controller (final integrated report)
```

#### Pattern 4: Sub-Agent Delegation
Core agent delegates specific tasks to specialized sub-agents.

```
Investment Analyst Agent
    → Market Research Sub-Agent (fetch data)
    → Risk Assessment Sub-Agent (calculate metrics)
    → Sector Analysis Sub-Agent (compare allocations)
    ← [Aggregate results]
    → Generate recommendations
```

### 4.3 Coordination Rules

1. **Data Access**: All agents must request data through Portfolio Data Agent (no direct DB access)
2. **Context Sharing**: Agents share relevant insights via shared context object
3. **Conflict Resolution**: Flow Controller adjudicates conflicts between agent recommendations
4. **Human-in-Loop**: Critical financial decisions require user approval before execution
5. **Audit Trail**: All agent interactions logged for traceability and compliance

### 4.4 State Management

Flow Controller maintains shared state across workflow:

```python
workflow_state = {
    "session_id": "uuid",
    "user_context": {
        "user_id": "string",
        "risk_profile": "string",
        "tax_bracket": "string",
        "age": int,
        "goals": []
    },
    "data_cache": {
        "portfolio_summary": {},
        "holdings": [],
        "allocation": {}
    },
    "agent_outputs": {
        "tax_advisor": {},
        "estate_planner": {},
        "investment_analyst": {}
    },
    "workflow_status": "in_progress|completed|error",
    "created_at": "timestamp",
    "updated_at": "timestamp"
}
```

---

## 5. Data Integration

### 5.1 Database Schema Mapping

#### Key Tables
- **institutions**: Financial institution master data
- **accounts**: User accounts by institution (RRSP, TFSA, LIRA, etc.)
- **statements**: Statement metadata with dates and total values
- **securities**: Master list of holdings (stocks, ETFs, funds, GICs)
- **asset_types**: Asset classification (Equity, Fixed Income, Balanced, etc.)
- **holdings**: Point-in-time holdings with quantity, price, book/market value
- **cash_balances**: Cash positions by account and date
- **account_performance**: Historical return metrics

#### Key Views
- **v_latest_holdings**: Current holdings with gain/loss calculations
- **v_portfolio_allocation**: Allocation by asset category and account
- **v_portfolio_value_trend**: Historical portfolio value (monthly aggregation)

### 5.2 MCP Integration

Implement Model Context Protocol for standardized data source connections:

```python
# MCP Connection Configuration
mcp_config = {
    "connection_type": "postgresql",
    "connection_string": "postgresql://user:pass@localhost/portfolio_db",
    "authentication": {
        "method": "credentials",
        "credentials_file": ".env"
    },
    "capabilities": {
        "query_execution": True,
        "transaction_support": False,  # Read-only
        "streaming": False
    },
    "security": {
        "read_only": True,
        "allowed_operations": ["SELECT"],
        "query_validation": True,
        "sql_injection_prevention": True
    }
}
```

### 5.3 Data Access Patterns

#### Pattern 1: Portfolio Data Agent as Facade
```python
# All agents request data through Portfolio Data Agent
request = {
    "action": "get_holdings",
    "filters": {
        "account_type": "RRSP",
        "institution": "SunLife"
    }
}
response = portfolio_data_agent.handle_request(request)
```

#### Pattern 2: Cached Data Sharing
```python
# Flow Controller caches frequently accessed data
if "portfolio_summary" not in workflow_state["data_cache"]:
    workflow_state["data_cache"]["portfolio_summary"] = \
        portfolio_data_agent.get_portfolio_summary()

# Agents access cached data
summary = workflow_state["data_cache"]["portfolio_summary"]
```

### 5.4 External Data Sources

#### Market Data (Investment Analyst Agent)
- **Alpha Vantage API**: Real-time and historical prices
- **Yahoo Finance**: Dividend data, fundamentals
- **NewsAPI**: Financial news aggregation

#### Tax Reference Data (Tax Advisor Agent)
- **CRA Tax Brackets**: Federal and provincial rates
- **RRSP/TFSA Limits**: Annual contribution limits
- **OAS Clawback Thresholds**: Income thresholds

#### Product Information (Estate Planner Agent)
- **Fund Database**: Mutual fund and ETF information
- **Insurance Providers**: Product comparison data

---

## 6. Implementation Requirements

### 6.1 Technology Stack

#### Framework
- **CrewAI**: Multi-agent orchestration framework
- **Python 3.11+**: Core development language
- **LangChain**: LLM integration and tool management

#### LLM Providers
- **Primary**: DeepSeek (cost-effective)
- **Alternatives**: OpenAI GPT-4, Anthropic Claude
- **Fallback**: Rule-based logic for critical paths

#### Database
- **PostgreSQL**: Existing schema (see database/schema.sql)
- **Connection Pooling**: Via psycopg2 or asyncpg
- **ORM**: Raw SQL through db_manager.py (existing pattern)

#### APIs and Services
- **Market Data**: Alpha Vantage, Yahoo Finance
- **News**: NewsAPI or similar
- **Tax Data**: Static reference tables or CRA API

### 6.2 Project Structure

```
personal_finance/
├── multi_agent/
│   ├── __init__.py
│   ├── flows/
│   │   ├── __init__.py
│   │   ├── financial_advisory_flow.py
│   │   └── workflow_orchestrator.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py
│   │   ├── portfolio_data_agent.py
│   │   ├── tax_advisor_agent.py
│   │   ├── estate_planner_agent.py
│   │   └── investment_analyst_agent.py
│   ├── sub_agents/
│   │   ├── __init__.py
│   │   ├── tax_calculator.py
│   │   ├── market_research.py
│   │   ├── risk_assessment.py
│   │   ├── product_research.py
│   │   └── regulatory_compliance.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── database_tools.py
│   │   ├── market_data_tools.py
│   │   ├── tax_tools.py
│   │   └── analysis_tools.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── messages.py
│   │   ├── agent_outputs.py
│   │   └── workflow_state.py
│   └── config/
│       ├── __init__.py
│       ├── agent_config.yaml
│       └── mcp_config.yaml
├── tests/
│   └── multi_agent/
│       ├── test_agents.py
│       ├── test_flows.py
│       └── test_integration.py
├── requirements_multi_agent.txt
└── docs/
    └── multi_agent/
        ├── API.md
        ├── WORKFLOWS.md
        └── EXAMPLES.md
```

### 6.3 Configuration Files

#### agent_config.yaml
```yaml
agents:
  portfolio_data:
    model: "deepseek-chat"
    temperature: 0.1
    max_iterations: 3
    tools:
      - database_query
      - portfolio_analyzer

  tax_advisor:
    model: "deepseek-chat"
    temperature: 0.2
    max_iterations: 5
    tools:
      - tax_calculator
      - cra_data
    knowledge_base: "tax_laws/canadian_tax.md"

  estate_planner:
    model: "deepseek-chat"
    temperature: 0.3
    max_iterations: 5
    tools:
      - product_database
      - probate_calculator
    knowledge_base: "estate_planning/strategies.md"

  investment_analyst:
    model: "deepseek-chat"
    temperature: 0.3
    max_iterations: 5
    tools:
      - market_data
      - risk_calculator
      - news_aggregator
    knowledge_base: "investment/strategies.md"

sub_agents:
  market_research:
    model: "deepseek-chat"
    temperature: 0.1
    tools:
      - alpha_vantage
      - yahoo_finance

  risk_assessment:
    model: "deepseek-chat"
    temperature: 0.1
    tools:
      - portfolio_stats
      - risk_metrics
```

#### mcp_config.yaml
```yaml
mcp_connections:
  postgresql:
    provider: "postgresql"
    connection:
      host: "${DB_HOST}"
      port: 5432
      database: "${DB_NAME}"
      user: "${DB_USER}"
      password: "${DB_PASSWORD}"
    security:
      read_only: true
      allowed_operations:
        - SELECT
      query_timeout: 30

  alpha_vantage:
    provider: "http"
    base_url: "https://www.alphavantage.co/query"
    authentication:
      type: "api_key"
      key: "${ALPHA_VANTAGE_KEY}"
    rate_limiting:
      requests_per_minute: 5
```

### 6.4 Development Phases

#### Phase 1: Foundation (Weeks 1-2)
- [ ] Set up CrewAI framework and dependencies
- [ ] Implement base agent class with common functionality
- [ ] Create MCP database connection layer
- [ ] Implement Portfolio Data Agent
- [ ] Create basic Flow Controller
- [ ] Unit tests for data retrieval

#### Phase 2: Tax Advisor Agent (Weeks 3-4)
- [ ] Implement Tax Advisor Agent core logic
- [ ] Build Tax Calculator Sub-Agent
- [ ] Create Regulatory Compliance Sub-Agent
- [ ] Develop tax optimization algorithms
- [ ] Integration tests with Portfolio Data Agent
- [ ] Documentation and examples

#### Phase 3: Estate Planner Agent (Weeks 5-6)
- [ ] Implement Estate Planner Agent core logic
- [ ] Build Product Research Sub-Agent
- [ ] Build Risk Assessment Sub-Agent
- [ ] Create product recommendation engine
- [ ] Integration tests with Portfolio Data Agent
- [ ] Documentation and examples

#### Phase 4: Investment Analyst Agent (Weeks 7-8)
- [ ] Implement Investment Analyst Agent core logic
- [ ] Build Market Research Sub-Agent
- [ ] Integrate market data APIs (Alpha Vantage, Yahoo Finance)
- [ ] Build Sector Analysis Sub-Agent
- [ ] Create recommendation engine
- [ ] Integration tests
- [ ] Documentation and examples

#### Phase 5: Workflow Integration (Weeks 9-10)
- [ ] Implement sequential workflow pattern
- [ ] Implement parallel execution pattern
- [ ] Implement collaborative refinement pattern
- [ ] Build conflict resolution logic
- [ ] Create unified reporting system
- [ ] End-to-end integration tests

#### Phase 6: UI and Reporting (Weeks 11-12)
- [ ] Extend web/app.py with multi-agent endpoints
- [ ] Create interactive query interface
- [ ] Build comprehensive report generation
- [ ] Add data visualization for recommendations
- [ ] User feedback and refinement loop
- [ ] Performance optimization

#### Phase 7: Testing and Documentation (Weeks 13-14)
- [ ] Comprehensive test coverage (unit, integration, E2E)
- [ ] Load testing and performance benchmarking
- [ ] Security audit and vulnerability testing
- [ ] Complete API documentation
- [ ] User guide and examples
- [ ] Deployment guide

---

## 7. Safety and Compliance

### 7.1 Disclaimers

All agent outputs must include appropriate disclaimers:

```
IMPORTANT DISCLAIMER:
This analysis is provided for informational and educational purposes only.
It does not constitute professional financial, tax, legal, or investment
advice. Always consult with a qualified professional (CPA, CFP, attorney)
before making financial decisions. Past performance does not guarantee
future results. Investments involve risk, including possible loss of principal.
```

### 7.2 Human-in-the-Loop Controls

Critical actions require user approval:
- [ ] Any transaction exceeding $10,000
- [ ] Asset sales with tax implications
- [ ] Account type changes (e.g., RRSP to RRIF conversion)
- [ ] Beneficiary designation changes
- [ ] Insurance product recommendations

### 7.3 Data Privacy and Security

#### Data Handling
- [ ] No PII stored in logs or temporary files
- [ ] Database credentials in .env (gitignored)
- [ ] API keys encrypted at rest
- [ ] All connections use TLS/SSL

#### Access Controls
- [ ] Read-only database access for agents
- [ ] Query validation and SQL injection prevention
- [ ] Rate limiting on external API calls
- [ ] Session-based authentication for web interface

#### Audit Trail
- [ ] Log all agent decisions and recommendations
- [ ] Timestamp and correlation ID for all operations
- [ ] User approval/rejection tracking
- [ ] Data access audit log

### 7.4 Error Handling

#### Agent-Level Errors
- [ ] Graceful degradation if sub-agent fails
- [ ] Retry logic with exponential backoff
- [ ] Fallback to rule-based logic if LLM unavailable
- [ ] Clear error messages to user

#### System-Level Errors
- [ ] Database connection pooling and recovery
- [ ] API timeout handling
- [ ] Circuit breaker pattern for external services
- [ ] Comprehensive error logging

---

## 8. Testing Strategy

### 8.1 Unit Testing

Each agent and sub-agent must have:
- [ ] Isolated tests with mocked dependencies
- [ ] Test coverage > 80%
- [ ] Edge case and boundary testing
- [ ] Performance benchmarks

### 8.2 Integration Testing

Workflow patterns tested end-to-end:
- [ ] Sequential analysis workflow
- [ ] Parallel execution workflow
- [ ] Collaborative refinement workflow
- [ ] Sub-agent delegation patterns
- [ ] Database integration
- [ ] External API integration

### 8.3 Validation Testing

Financial logic validation:
- [ ] Tax calculation accuracy (compare to manual calculations)
- [ ] Portfolio metrics verification (cross-check with portfolio_analyzer.py)
- [ ] Recommendation consistency across multiple runs
- [ ] Edge cases (empty portfolio, single holding, etc.)

### 8.4 User Acceptance Testing

Real-world scenarios:
- [ ] Comprehensive financial review for sample portfolio
- [ ] Tax optimization for year-end planning
- [ ] Estate planning for different age groups
- [ ] Investment recommendations in various market conditions

---

## 9. Performance Metrics

### 9.1 Agent Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Response Time (simple query) | < 5 seconds | 95th percentile |
| Response Time (complex analysis) | < 30 seconds | 95th percentile |
| Accuracy (tax calculations) | > 99% | Manual validation |
| Recommendation Consistency | > 90% | Multiple runs |
| API Success Rate | > 99.5% | Over 1000 requests |

### 9.2 System Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Database Query Time | < 2 seconds | Average |
| Concurrent Users Supported | > 10 | Load testing |
| Memory Usage (per workflow) | < 500 MB | Peak usage |
| API Rate Limiting Compliance | 100% | No exceeded limits |

### 9.3 Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test Coverage | > 80% | pytest-cov |
| Code Quality (Pylint) | > 8.0/10 | Linting score |
| Documentation Coverage | 100% | All public APIs |
| User Satisfaction | > 4.0/5.0 | Feedback surveys |

---

## 10. Future Enhancements

### 10.1 Additional Agents (Phase 2)

#### Retirement Planning Agent
- Calculate retirement income needs
- Optimize RRSP/RRIF conversion timing
- Model longevity risk and drawdown strategies

#### Insurance Advisor Agent
- Analyze life insurance needs
- Recommend disability and critical illness coverage
- Compare insurance products across providers

#### Cash Flow Optimizer Agent
- Analyze income and expenses
- Recommend savings strategies
- Optimize debt repayment

### 10.2 Advanced Features

#### Scenario Modeling
- Monte Carlo simulations for retirement planning
- Market stress testing
- What-if analysis for major life events

#### Automated Rebalancing
- Generate trade lists for rebalancing
- Optimize for tax efficiency
- Schedule periodic reviews

#### Benchmark Comparison
- Compare portfolio to target allocation
- Track against market indices
- Performance attribution analysis

### 10.3 Integration Enhancements

#### Brokerage Integration
- Read-only API connections to brokerages
- Real-time portfolio sync
- Transaction history import

#### CRA MyAccount Integration
- Retrieve RRSP contribution room
- Access NOA (Notice of Assessment)
- Validate tax calculations

#### External Research Integration
- Morningstar ratings
- S&P credit ratings
- Analyst consensus data

---

## 11. Glossary

### Financial Terms

- **RRSP (Registered Retirement Savings Plan)**: Tax-deferred retirement account
- **TFSA (Tax-Free Savings Account)**: Tax-free growth and withdrawal account
- **LIRA (Locked-In Retirement Account)**: Restricted pension account
- **GIC (Guaranteed Investment Certificate)**: Fixed-rate savings product
- **MER (Management Expense Ratio)**: Annual fund management fee
- **Probate**: Legal process of validating a will
- **Superficial Loss**: Loss disallowed due to repurchase within 30 days
- **OAS (Old Age Security)**: Government pension program

### Technical Terms

- **MCP (Model Context Protocol)**: Standard for AI-data source connections
- **A2A (Agent-to-Agent Protocol)**: Standard for inter-agent communication
- **CrewAI**: Multi-agent orchestration framework
- **Flow**: Workflow controller in CrewAI
- **Crew**: Team of agents collaborating on tasks
- **Human-in-the-Loop**: Manual approval for critical decisions

---

## 12. References and Resources

### Standards and Protocols
1. [Anthropic Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
2. [Google Agent-to-Agent Protocol (A2A)](https://a2a.dev/)
3. [CrewAI Documentation](https://docs.crewai.com/)

### Financial Regulations
1. [Canada Revenue Agency (CRA)](https://www.canada.ca/en/revenue-agency.html)
2. [MFDA Rules and Regulations](https://mfda.ca/)
3. [OSC Investor Protection](https://www.osc.ca/)

### Technical Resources
1. [DeepLearning.AI: Multi AI Agent Systems with CrewAI](https://www.deeplearning.ai/short-courses/multi-ai-agent-systems-with-crewai/)
2. [Multi-Agent System Design Patterns (Google)](https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/)
3. [Event-Driven Multi-Agent Systems](https://www.confluent.io/blog/event-driven-multi-agent-systems/)

### APIs and Data Sources
1. [Alpha Vantage API](https://www.alphavantage.co/)
2. [Yahoo Finance API](https://finance.yahoo.com/)
3. [NewsAPI](https://newsapi.org/)

---

## 13. Appendices

### Appendix A: Sample Agent Interaction

```python
# User Query: "What's the most tax-efficient way to withdraw $50,000?"

# Step 1: Flow Controller receives query
flow_controller.process_query(
    query="What's the most tax-efficient way to withdraw $50,000?",
    user_context={
        "tax_bracket": "mid",
        "province": "ON",
        "age": 55
    }
)

# Step 2: Flow delegates to Portfolio Data Agent
portfolio_data = portfolio_data_agent.get_portfolio_summary()
accounts = portfolio_data_agent.get_accounts_with_balances()

# Step 3: Tax Advisor Agent analyzes
tax_analysis = tax_advisor_agent.analyze_withdrawal_strategy(
    amount=50000,
    accounts=accounts,
    user_context=user_context
)

# Output:
{
  "recommended_strategy": [
    {
      "account": "TFSA - SunLife",
      "amount": 30000,
      "tax_impact": 0,
      "rationale": "Tax-free withdrawal, no impact on taxable income"
    },
    {
      "account": "Non-Registered - ScotiaBank",
      "amount": 20000,
      "tax_impact": 5000,
      "rationale": "Only capital gains taxed at 50% inclusion rate"
    }
  ],
  "total_tax_estimated": 5000,
  "net_after_tax": 45000,
  "alternatives": [...]
}
```

### Appendix B: Sample Comprehensive Report

```json
{
  "report_id": "uuid",
  "generated_at": "2026-01-07T14:30:00Z",
  "user_id": "user123",
  "report_type": "comprehensive_financial_review",

  "portfolio_summary": {
    "total_value": 825000.00,
    "num_accounts": 5,
    "num_securities": 32,
    "allocation": {
      "Equity": 60.5,
      "Fixed Income": 25.3,
      "Balanced": 10.2,
      "Cash": 4.0
    }
  },

  "tax_analysis": {
    "unrealized_gains": 125000.00,
    "unrealized_losses": 8500.00,
    "estimated_tax_liability": 31250.00,
    "key_recommendations": [
      "Harvest losses in XYZ Fund to offset gains ($2,125 tax savings)",
      "Defer RRSP withdrawals until lower tax bracket",
      "Prioritize TFSA withdrawals for tax-free access"
    ]
  },

  "estate_planning": {
    "estimated_probate_fees": 16500.00,
    "recommendations": [
      "Designate beneficiaries on RRSP accounts (avoid probate)",
      "Consider increasing TFSA allocation for tax-free estate transfer",
      "Review life insurance needs (estimated gap: $250,000)"
    ]
  },

  "investment_analysis": {
    "portfolio_health_score": 7.8,
    "concentration_risk": "Moderate",
    "key_recommendations": [
      "Reduce overweight position in ABC Inc (12% → 8%)",
      "Increase international equity exposure (15% → 20%)",
      "Consider rebalancing: Equity is 5% over target"
    ]
  },

  "action_items": [
    {
      "priority": "High",
      "action": "Tax-loss harvesting on XYZ Fund",
      "deadline": "2026-12-31",
      "estimated_benefit": "$2,125 tax savings"
    },
    {
      "priority": "Medium",
      "action": "Designate RRSP beneficiaries",
      "deadline": "2026-03-31",
      "estimated_benefit": "$8,000 probate savings"
    },
    {
      "priority": "Medium",
      "action": "Rebalance portfolio allocation",
      "deadline": "2026-02-28",
      "estimated_benefit": "Risk reduction"
    }
  ]
}
```

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-07 | System | Initial specification |

**Approval Required From:**
- [ ] Technical Lead
- [ ] Product Owner
- [ ] Compliance Officer
- [ ] Security Reviewer

**Next Steps:**
1. Review and feedback from stakeholders
2. Technical feasibility assessment
3. Budget and timeline approval
4. Begin Phase 1 implementation
