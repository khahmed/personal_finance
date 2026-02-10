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
