USE bluestock_mf;

-- 1. Total Number of Available Schemes
SELECT COUNT(*) AS total_funds FROM dim_fund;

-- 2. Latest Net Asset Value (NAV) for Each Fund
SELECT f.scheme_name, n.date, n.nav
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
WHERE (n.amfi_code, n.date) IN (
    SELECT amfi_code, MAX(date) FROM fact_nav GROUP BY amfi_code
);

-- 3. Highest NAV Ever Recorded for Each Scheme
SELECT f.scheme_name, MAX(n.nav) AS peak_nav
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
GROUP BY f.scheme_name;

-- 4. Average NAV per Fund for the Most Recent Month
SELECT f.scheme_name, AVG(n.nav) AS avg_nav_latest_month
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
WHERE n.date >= DATE_SUB((SELECT MAX(date) FROM fact_nav), INTERVAL 1 MONTH)
GROUP BY f.scheme_name;

-- 5. Volatility Analysis (Min vs Max NAV variation)
SELECT f.scheme_name, MIN(n.nav) AS min_nav, MAX(n.nav) AS max_nav,
       (MAX(n.nav) - MIN(n.nav)) AS absolute_variance
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
GROUP BY f.scheme_name;

-- 6. Count of Recorded Daily NAV Entries per Scheme
SELECT f.scheme_name, COUNT(*) AS data_points_tracked
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
GROUP BY f.scheme_name;

-- 7. Identify Gaps or Missing Trading Dates (Should return 0 due to forward-fill)
SELECT COUNT(*) AS total_missing_or_null_navs 
FROM fact_nav 
WHERE nav IS NULL;

-- 8. Top 3 Mutual Funds with the Highest Starting NAV in History
SELECT f.scheme_name, n.date, n.nav
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
WHERE (n.amfi_code, n.date) IN (
    SELECT amfi_code, MIN(date) FROM fact_nav GROUP BY amfi_code
)
ORDER BY n.nav DESC
LIMIT 3;

-- 9. Complete Portfolio Summary Breakdown by Scheme Risk Tier
SELECT f.risk_grade, COUNT(DISTINCT f.amfi_code) AS unique_schemes, COUNT(n.nav_id) AS total_historical_records
FROM dim_fund f
LEFT JOIN fact_nav n ON f.amfi_code = n.amfi_code
GROUP BY f.risk_grade;

-- 10. Sequential Growth Check: Comparing Latest NAV against its 30-Day Prior Value
WITH Latest AS (
    SELECT amfi_code, nav AS latest_nav 
    FROM fact_nav 
    WHERE (amfi_code, date) IN (SELECT amfi_code, MAX(date) FROM fact_nav GROUP BY amfi_code)
),
Prior30 AS (
    SELECT amfi_code, nav AS prior_nav 
    FROM fact_nav 
    WHERE (amfi_code, date) IN (SELECT amfi_code, DATE_SUB(MAX(date), INTERVAL 30 DAY) FROM fact_nav GROUP BY amfi_code)
)
SELECT f.scheme_name, l.latest_nav, p.prior_nav,
       ROUND(((l.latest_nav - p.prior_nav) / p.prior_nav) * 100, 2) AS percentage_growth_30d
FROM dim_fund f
JOIN Latest l ON f.amfi_code = l.amfi_code
JOIN Prior30 p ON f.amfi_code = p.amfi_code;