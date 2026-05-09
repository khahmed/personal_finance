-- Update script to add monthly aggregation view
-- This addresses the issue where multiple statements on different days
-- in the same month create artificial dips in portfolio value trends

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
