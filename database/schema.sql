-- Portfolio Holdings Database Schema
-- This schema stores financial holdings data extracted from PDF statements

-- Create database (run this manually if needed)
-- CREATE DATABASE portfolio_db;

-- Table to store financial institutions
CREATE TABLE IF NOT EXISTS institutions (
    institution_id SERIAL PRIMARY KEY,
    institution_name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table to store accounts
CREATE TABLE IF NOT EXISTS accounts (
    account_id SERIAL PRIMARY KEY,
    institution_id INTEGER REFERENCES institutions(institution_id),
    account_number VARCHAR(50) NOT NULL,
    account_type VARCHAR(50) NOT NULL,  -- RRSP, TFSA, LIRA, etc.
    account_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(institution_id, account_number)
);

-- Table to store statement metadata
CREATE TABLE IF NOT EXISTS statements (
    statement_id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(account_id),
    statement_date DATE NOT NULL,
    statement_period_start DATE,
    statement_period_end DATE,
    total_value DECIMAL(15, 2),
    file_path VARCHAR(500),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id, statement_date)
);

-- Table to store asset types
CREATE TABLE IF NOT EXISTS asset_types (
    asset_type_id SERIAL PRIMARY KEY,
    asset_type_name VARCHAR(50) UNIQUE NOT NULL,  -- Stock, ETF, Mutual Fund, Bond, etc.
    asset_category VARCHAR(50) NOT NULL,  -- Equity, Fixed Income, Balanced, Cash, Alternative
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table to store securities/holdings
CREATE TABLE IF NOT EXISTS securities (
    security_id SERIAL PRIMARY KEY,
    symbol VARCHAR(50),
    security_name VARCHAR(255) NOT NULL,
    asset_type_id INTEGER REFERENCES asset_types(asset_type_id),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, security_name)
);

-- Table to store holdings at a specific point in time
CREATE TABLE IF NOT EXISTS holdings (
    holding_id SERIAL PRIMARY KEY,
    statement_id INTEGER REFERENCES statements(statement_id),
    account_id INTEGER REFERENCES accounts(account_id),
    security_id INTEGER REFERENCES securities(security_id),
    quantity DECIMAL(15, 5),
    price DECIMAL(15, 4),
    book_value DECIMAL(15, 2),
    market_value DECIMAL(15, 2),
    holding_date DATE NOT NULL,
    currency VARCHAR(3) DEFAULT 'CAD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(statement_id, security_id)
);

-- Table to store cash balances
CREATE TABLE IF NOT EXISTS cash_balances (
    cash_balance_id SERIAL PRIMARY KEY,
    statement_id INTEGER REFERENCES statements(statement_id),
    account_id INTEGER REFERENCES accounts(account_id),
    balance_date DATE NOT NULL,
    cash_amount DECIMAL(15, 2),
    currency VARCHAR(3) DEFAULT 'CAD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table to store account performance metrics
CREATE TABLE IF NOT EXISTS account_performance (
    performance_id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(account_id),
    performance_date DATE NOT NULL,
    return_1m DECIMAL(5, 2),
    return_3m DECIMAL(5, 2),
    return_6m DECIMAL(5, 2),
    return_ytd DECIMAL(5, 2),
    return_1y DECIMAL(5, 2),
    return_3y DECIMAL(5, 2),
    return_5y DECIMAL(5, 2),
    return_inception DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id, performance_date)
);

-- Create indexes for better query performance
CREATE INDEX idx_holdings_account_date ON holdings(account_id, holding_date);
CREATE INDEX idx_holdings_security ON holdings(security_id);
CREATE INDEX idx_statements_account ON statements(account_id);
CREATE INDEX idx_statements_date ON statements(statement_date);
CREATE INDEX idx_accounts_institution ON accounts(institution_id);
CREATE INDEX idx_cash_balances_account_date ON cash_balances(account_id, balance_date);

-- Views for common queries

-- View: Latest holdings by account
CREATE OR REPLACE VIEW v_latest_holdings AS
SELECT
    a.account_number,
    a.account_type,
    i.institution_name,
    s.statement_date,
    sec.security_name,
    sec.symbol,
    at.asset_category,
    at.asset_type_name,
    h.quantity,
    h.price,
    h.book_value,
    h.market_value,
    h.currency,
    CASE
        WHEN h.book_value > 0 THEN ((h.market_value - h.book_value) / h.book_value * 100)
        ELSE 0
    END as gain_loss_pct
FROM holdings h
JOIN statements s ON h.statement_id = s.statement_id
JOIN accounts a ON h.account_id = a.account_id
JOIN institutions i ON a.institution_id = i.institution_id
JOIN securities sec ON h.security_id = sec.security_id
JOIN asset_types at ON sec.asset_type_id = at.asset_type_id
WHERE s.statement_date = (
    SELECT MAX(s2.statement_date)
    FROM statements s2
    WHERE s2.account_id = a.account_id
);

-- View: Portfolio allocation by asset category
CREATE OR REPLACE VIEW v_portfolio_allocation AS
SELECT
    i.institution_name,
    a.account_number,
    a.account_type,
    at.asset_category,
    s.statement_date,
    SUM(h.market_value) as total_value,
    COUNT(DISTINCT h.security_id) as num_holdings
FROM holdings h
JOIN statements s ON h.statement_id = s.statement_id
JOIN accounts a ON h.account_id = a.account_id
JOIN institutions i ON a.institution_id = i.institution_id
JOIN securities sec ON h.security_id = sec.security_id
JOIN asset_types at ON sec.asset_type_id = at.asset_type_id
GROUP BY i.institution_name, a.account_number, a.account_type, at.asset_category, s.statement_date;

-- View: Portfolio value over time (by exact date)
CREATE OR REPLACE VIEW v_portfolio_value_trend AS
SELECT
    s.statement_date,
    i.institution_name,
    a.account_number,
    a.account_type,
    SUM(h.market_value) as total_holdings_value,
    COALESCE(cb.cash_amount, 0) as cash_balance,
    SUM(h.market_value) + COALESCE(cb.cash_amount, 0) as total_account_value
FROM statements s
JOIN accounts a ON s.account_id = a.account_id
JOIN institutions i ON a.institution_id = i.institution_id
LEFT JOIN holdings h ON s.statement_id = h.statement_id
LEFT JOIN cash_balances cb ON s.statement_id = cb.statement_id
GROUP BY s.statement_date, i.institution_name, a.account_number, a.account_type, cb.cash_amount
ORDER BY s.statement_date;

-- View: Portfolio value over time aggregated by month
-- This view uses the latest statement in each month for each account
-- and aggregates across all accounts/institutions to avoid artificial dips
-- when different accounts have statements on different days of the same month
CREATE OR REPLACE VIEW v_portfolio_value_trend_monthly AS
WITH latest_statement_per_month AS (
    -- For each account, get the latest statement date in each year-month
    SELECT
        account_id,
        DATE_TRUNC('month', statement_date)::DATE as month_date,
        MAX(statement_date) as latest_statement_date
    FROM statements
    GROUP BY account_id, DATE_TRUNC('month', statement_date)
),
monthly_account_values AS (
    -- Get the holdings and cash for the latest statement in each month
    SELECT
        DATE_TRUNC('month', s.statement_date)::DATE as month_date,
        i.institution_name,
        a.account_number,
        a.account_type,
        SUM(h.market_value) as total_holdings_value,
        COALESCE(MAX(cb.cash_amount), 0) as cash_balance
    FROM statements s
    JOIN accounts a ON s.account_id = a.account_id
    JOIN institutions i ON a.institution_id = i.institution_id
    JOIN latest_statement_per_month lspm
        ON s.account_id = lspm.account_id
        AND s.statement_date = lspm.latest_statement_date
    LEFT JOIN holdings h ON s.statement_id = h.statement_id
    LEFT JOIN cash_balances cb ON s.statement_id = cb.statement_id
    GROUP BY DATE_TRUNC('month', s.statement_date), i.institution_name, a.account_number, a.account_type
)
SELECT
    month_date as statement_date,
    institution_name,
    account_number,
    account_type,
    total_holdings_value,
    cash_balance,
    total_holdings_value + cash_balance as total_account_value
FROM monthly_account_values
ORDER BY month_date, institution_name, account_number;

-- Insert initial asset types
INSERT INTO asset_types (asset_type_name, asset_category) VALUES
    ('Stock', 'Equity'),
    ('ETF', 'Equity'),
    ('Mutual Fund - Equity', 'Equity'),
    ('Mutual Fund - Balanced', 'Balanced'),
    ('Mutual Fund - Fixed Income', 'Fixed Income'),
    ('Bond', 'Fixed Income'),
    ('GIC', 'Fixed Income'),
    ('Money Market', 'Cash'),
    ('Cash', 'Cash'),
    ('Index Fund - Canadian Equity', 'Equity'),
    ('Index Fund - US Equity', 'Equity'),
    ('Index Fund - International Equity', 'Equity'),
    ('Index Fund - Global Equity', 'Equity'),
    ('Index Fund - Fixed Income', 'Fixed Income'),
    ('Index Fund - Balanced', 'Balanced'),
    ('Private Equity', 'Alternative'),
    ('Exempt Market Security', 'Alternative')
ON CONFLICT (asset_type_name) DO NOTHING;

-- Insert institutions
INSERT INTO institutions (institution_name) VALUES
    ('SunLife'),
    ('ScotiaBank'),
    ('Olympia')
ON CONFLICT (institution_name) DO NOTHING;

-- ═══════════════════════════════════════════════════════════════════════════
-- Multi-Agent Self-Evolution Schema
-- Tables that back the self-evolving multi-agent system (multi_agent/).
-- ═══════════════════════════════════════════════════════════════════════════

-- Versioned agent configurations. Each row is one immutable snapshot; only
-- the row with is_active=TRUE for a given agent_name is loaded at runtime.
CREATE TABLE IF NOT EXISTS agent_configs (
    id              SERIAL PRIMARY KEY,
    agent_name      VARCHAR(100) NOT NULL,
    version         INTEGER NOT NULL DEFAULT 1,
    is_active       BOOLEAN DEFAULT TRUE,

    -- Prompt fields (evolve via MetaEvolutionAgent)
    role            TEXT,
    goal            TEXT,
    backstory       TEXT,
    system_prompts  TEXT DEFAULT '{}',   -- JSON stored as text for portability

    -- Business rule thresholds (evolve via MetaEvolutionAgent)
    business_rules  TEXT DEFAULT '{}',   -- JSON stored as text for portability

    -- LLM settings
    model           VARCHAR(100) DEFAULT 'deepseek-chat',
    temperature     FLOAT DEFAULT 0.3,

    -- Audit trail
    evolution_reason TEXT,
    parent_version   INTEGER,
    created_at       TIMESTAMP DEFAULT NOW(),

    UNIQUE(agent_name, version)
);

-- Per-session interaction log used by MetaEvolutionAgent to decide when/what to evolve
CREATE TABLE IF NOT EXISTS agent_interactions (
    id              SERIAL PRIMARY KEY,
    session_id      VARCHAR(100),
    agent_name      VARCHAR(100),
    config_version  INTEGER DEFAULT 1,
    user_feedback   VARCHAR(20),          -- 'accepted', 'rejected', 'modified', or NULL
    output_summary  TEXT DEFAULT '{}',    -- JSON: key metrics from that run
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_configs_name_active ON agent_configs(agent_name, is_active);
CREATE INDEX IF NOT EXISTS idx_agent_interactions_agent  ON agent_interactions(agent_name, created_at);
CREATE INDEX IF NOT EXISTS idx_agent_interactions_session ON agent_interactions(session_id);

-- ─── Seed default agent configurations ─────────────────────────────────────
-- These mirror the hardcoded values in the Python agents so that version 1 in
-- the DB is identical to what the code produced before this feature was added.

INSERT INTO agent_configs (
    agent_name, version, is_active, role, goal, backstory,
    system_prompts, business_rules, model, temperature, evolution_reason
) VALUES (
    'PortfolioDataAgent', 1, TRUE,
    'Data Specialist and Context Provider',
    'Retrieve, aggregate, and provide accurate portfolio data to other agents',
    'You are an expert data analyst specializing in financial portfolio data. You have deep knowledge of SQL and database systems. You ensure data accuracy and provide comprehensive portfolio context including holdings, allocation, and metrics. You always validate data before sharing it with other agents.',
    '{"general": "You are a financial data specialist providing accurate portfolio data."}',
    '{"max_holdings_per_request": 1000}',
    'deepseek-chat', 0.1,
    'Initial seed from hardcoded defaults'
) ON CONFLICT (agent_name, version) DO NOTHING;

INSERT INTO agent_configs (
    agent_name, version, is_active, role, goal, backstory,
    system_prompts, business_rules, model, temperature, evolution_reason
) VALUES (
    'TaxAdvisorAgent', 1, TRUE,
    'Tax Optimization Specialist',
    'Analyze portfolio for tax-efficient strategies and minimize tax liability',
    'You are a Canadian tax expert specializing in investment tax optimization. You have deep knowledge of RRSP, TFSA, LIRA, and non-registered account tax treatment. You understand capital gains taxation, tax-loss harvesting, and withdrawal strategies. You always consider the client''s tax bracket and provincial tax rates in your recommendations.',
    '{"tax": "You are a Canadian tax expert specializing in investment tax optimization. Analyze the portfolio data and provide tax optimization recommendations. Focus on capital gains, tax-loss harvesting, and account type optimization. Be specific and actionable.", "general": "You are a financial advisor."}',
    '{"inclusion_rate": 0.5, "default_tax_rate": 0.30, "min_loss_threshold": 100.0, "max_tlh_recommendations": 10, "max_priority_recommendations": 5}',
    'deepseek-chat', 0.2,
    'Initial seed from hardcoded defaults'
) ON CONFLICT (agent_name, version) DO NOTHING;

INSERT INTO agent_configs (
    agent_name, version, is_active, role, goal, backstory,
    system_prompts, business_rules, model, temperature, evolution_reason
) VALUES (
    'EstatePlannerAgent', 1, TRUE,
    'Estate Planning Specialist',
    'Optimize estate structure, minimize probate fees, and recommend suitable products',
    'You are an estate planning expert specializing in Canadian estate law. You understand probate fees, beneficiary designations, and tax-efficient estate transfer. You recommend products and account structures that minimize estate costs and taxes. You consider the client''s age, family situation, and legacy goals in your recommendations.',
    '{"estate": "You are an estate planning expert specializing in Canadian estate law. Analyze the portfolio structure and provide estate planning recommendations. Focus on probate minimization, beneficiary designations, and product recommendations. Be specific and actionable.", "general": "You are a financial advisor."}',
    '{"equity_threshold_pct": 50, "fixed_income_threshold_pct": 20, "equity_etf_allocation_pct": 20.0, "bond_etf_allocation_pct": 15.0, "default_province": "ON"}',
    'deepseek-chat', 0.3,
    'Initial seed from hardcoded defaults'
) ON CONFLICT (agent_name, version) DO NOTHING;

INSERT INTO agent_configs (
    agent_name, version, is_active, role, goal, backstory,
    system_prompts, business_rules, model, temperature, evolution_reason
) VALUES (
    'InvestmentAnalystAgent', 1, TRUE,
    'Securities Research and Portfolio Optimization Specialist',
    'Analyze securities, identify opportunities, and provide buy/sell recommendations',
    'You are an investment analyst with expertise in security analysis and portfolio optimization. You analyze individual securities, assess portfolio concentration, and provide actionable recommendations. You consider risk-adjusted returns, diversification, and market conditions in your analysis. You always provide clear rationale for your recommendations with confidence levels.',
    '{"investment": "You are an investment analyst. Analyze the portfolio holdings and provide investment recommendations. Focus on diversification, risk management, and rebalancing opportunities. Be specific and actionable.", "general": "You are a financial advisor."}',
    '{"overweight_threshold_pct": 10.0, "underweight_threshold_pct": 1.0, "underweight_min_value": 1000.0, "target_allocation_pct": 8.0, "health_score_base": 7.0, "health_score_many_holdings_bonus": 1.0, "health_score_few_holdings_penalty": 1.0, "health_score_high_concentration_penalty": 1.5, "health_score_low_concentration_bonus": 0.5, "many_holdings_threshold": 20, "few_holdings_threshold": 5, "high_concentration_threshold": 20.0, "low_concentration_threshold": 10.0, "max_rebalancing_actions": 5, "high_risk_overweight_count": 3, "high_urgency_overweight_count": 2}',
    'deepseek-chat', 0.3,
    'Initial seed from hardcoded defaults'
) ON CONFLICT (agent_name, version) DO NOTHING;

INSERT INTO agent_configs (
    agent_name, version, is_active, role, goal, backstory,
    system_prompts, business_rules, model, temperature, evolution_reason
) VALUES (
    'MetaEvolutionAgent', 1, TRUE,
    'Agent Evolution Specialist',
    'Monitor agent performance and evolve agent configurations based on interaction patterns',
    'You are an AI meta-agent responsible for continuously improving other financial advisory agents. You evaluate the quality of agent outputs, identify patterns in user feedback, and propose targeted improvements to agent prompts and business rules. You are conservative: you only propose changes when there is clear evidence of improvement, and you always preserve version history for rollback.',
    '{"meta": "You are a meta-agent evaluating the quality of financial advisory outputs. Your goal is to identify specific, actionable improvements to agent prompts and business rules. Be precise, conservative, and evidence-based."}',
    '{"min_interactions_before_evolution": 3, "min_confidence_to_evolve": 0.7, "max_versions_per_agent": 10, "evolution_cooldown_hours": 24}',
    'deepseek-chat', 0.2,
    'Initial seed from hardcoded defaults'
) ON CONFLICT (agent_name, version) DO NOTHING;
