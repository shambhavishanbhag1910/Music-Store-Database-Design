CREATE OR REPLACE VIEW marts.kpi_overview AS
SELECT
    COALESCE(SUM(CASE WHEN order_status = 'completed' THEN net_amount ELSE 0 END), 0)::NUMERIC(18,2) AS completed_revenue,
    COUNT(DISTINCT CASE WHEN order_status = 'completed' THEN order_id END) AS completed_orders,
    COUNT(DISTINCT customer_key) AS purchasing_customers,
    ROUND(
        COALESCE(SUM(CASE WHEN order_status = 'completed' THEN net_amount ELSE 0 END), 0)
        / NULLIF(COUNT(DISTINCT CASE WHEN order_status = 'completed' THEN order_id END), 0),
        2
    ) AS average_order_value
FROM warehouse.fact_sales;

CREATE OR REPLACE VIEW marts.daily_sales AS
SELECT
    d.full_date,
    COUNT(DISTINCT f.order_id) FILTER (WHERE f.order_status = 'completed') AS completed_orders,
    SUM(f.quantity) FILTER (WHERE f.order_status = 'completed') AS units_sold,
    COALESCE(SUM(f.net_amount) FILTER (WHERE f.order_status = 'completed'), 0)::NUMERIC(18,2) AS revenue,
    COUNT(DISTINCT f.customer_key) FILTER (WHERE f.order_status = 'completed') AS customers
FROM warehouse.dim_date d
LEFT JOIN warehouse.fact_sales f ON f.order_date_key = d.date_key
GROUP BY d.full_date;

CREATE OR REPLACE VIEW marts.monthly_sales AS
SELECT
    d.year,
    d.month,
    d.month_name,
    COUNT(DISTINCT f.order_id) FILTER (WHERE f.order_status = 'completed') AS completed_orders,
    COALESCE(SUM(f.net_amount) FILTER (WHERE f.order_status = 'completed'), 0)::NUMERIC(18,2) AS revenue,
    COALESCE(SUM(f.gross_amount) FILTER (WHERE f.order_status = 'completed'), 0)::NUMERIC(18,2) AS gross_revenue,
    COALESCE(SUM(f.allocated_discount) FILTER (WHERE f.order_status = 'completed'), 0)::NUMERIC(18,2) AS discounts,
    COALESCE(SUM(f.allocated_tax) FILTER (WHERE f.order_status = 'completed'), 0)::NUMERIC(18,2) AS tax
FROM warehouse.dim_date d
LEFT JOIN warehouse.fact_sales f ON f.order_date_key = d.date_key
GROUP BY d.year, d.month, d.month_name;

CREATE OR REPLACE VIEW marts.genre_performance AS
SELECT
    COALESCE(p.primary_genre, 'Unknown') AS genre_name,
    COUNT(DISTINCT f.order_id) FILTER (WHERE f.order_status = 'completed') AS completed_orders,
    SUM(f.quantity) FILTER (WHERE f.order_status = 'completed') AS units_sold,
    COALESCE(SUM(f.net_amount) FILTER (WHERE f.order_status = 'completed'), 0)::NUMERIC(18,2) AS revenue
FROM warehouse.fact_sales f
JOIN warehouse.dim_product p ON p.product_key = f.product_key
GROUP BY COALESCE(p.primary_genre, 'Unknown');

CREATE OR REPLACE VIEW marts.artist_performance AS
SELECT
    COALESCE(p.primary_artist, 'Unknown') AS artist_name,
    COUNT(DISTINCT f.order_id) FILTER (WHERE f.order_status = 'completed') AS completed_orders,
    SUM(f.quantity) FILTER (WHERE f.order_status = 'completed') AS units_sold,
    COALESCE(SUM(f.net_amount) FILTER (WHERE f.order_status = 'completed'), 0)::NUMERIC(18,2) AS revenue
FROM warehouse.fact_sales f
JOIN warehouse.dim_product p ON p.product_key = f.product_key
GROUP BY COALESCE(p.primary_artist, 'Unknown');

CREATE OR REPLACE VIEW marts.customer_value AS
SELECT
    c.customer_key,
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    c.country,
    MIN(f.order_ts) FILTER (WHERE f.order_status = 'completed') AS first_purchase_at,
    MAX(f.order_ts) FILTER (WHERE f.order_status = 'completed') AS last_purchase_at,
    COUNT(DISTINCT f.order_id) FILTER (WHERE f.order_status = 'completed') AS completed_orders,
    COALESCE(SUM(f.net_amount) FILTER (WHERE f.order_status = 'completed'), 0)::NUMERIC(18,2) AS lifetime_value,
    ROUND(
        COALESCE(SUM(f.net_amount) FILTER (WHERE f.order_status = 'completed'), 0)
        / NULLIF(COUNT(DISTINCT f.order_id) FILTER (WHERE f.order_status = 'completed'), 0),
        2
    ) AS avg_order_value
FROM warehouse.dim_customer c
LEFT JOIN warehouse.fact_sales f ON f.customer_key = c.customer_key
WHERE c.is_current
GROUP BY c.customer_key, c.customer_id, c.first_name, c.last_name, c.email, c.country;

CREATE OR REPLACE VIEW marts.payment_performance AS
SELECT
    d.full_date,
    p.payment_mode,
    COUNT(*) AS payment_attempts,
    COUNT(*) FILTER (WHERE p.payment_status = 'successful') AS successful_payments,
    COUNT(*) FILTER (WHERE p.payment_status = 'failed') AS failed_payments,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE p.payment_status = 'successful') / NULLIF(COUNT(*), 0),
        2
    ) AS success_rate_pct,
    COALESCE(SUM(p.amount) FILTER (WHERE p.payment_status = 'successful'), 0)::NUMERIC(18,2) AS successful_amount
FROM warehouse.fact_payment p
JOIN warehouse.dim_date d ON d.date_key = p.payment_date_key
GROUP BY d.full_date, p.payment_mode;

CREATE OR REPLACE VIEW marts.playlist_engagement AS
SELECT
    p.primary_genre AS genre_name,
    p.primary_artist AS artist_name,
    COUNT(*) AS playlist_adds,
    COUNT(DISTINCT a.customer_key) AS unique_customers
FROM warehouse.fact_playlist_activity a
JOIN warehouse.dim_product p ON p.product_key = a.product_key
GROUP BY p.primary_genre, p.primary_artist;

CREATE OR REPLACE VIEW marts.customer_rfm AS
WITH base AS (
    SELECT
        c.customer_key,
        c.customer_id,
        c.email,
        MAX(f.order_ts::date) FILTER (WHERE f.order_status = 'completed') AS last_purchase_date,
        COUNT(DISTINCT f.order_id) FILTER (WHERE f.order_status = 'completed') AS frequency,
        COALESCE(SUM(f.net_amount) FILTER (WHERE f.order_status = 'completed'), 0) AS monetary
    FROM warehouse.dim_customer c
    LEFT JOIN warehouse.fact_sales f ON f.customer_key = c.customer_key
    WHERE c.is_current
    GROUP BY c.customer_key, c.customer_id, c.email
), scored AS (
    SELECT
        *,
        (CURRENT_DATE - last_purchase_date) AS recency_days,
        6 - NTILE(5) OVER (ORDER BY last_purchase_date NULLS FIRST) AS r_score,
        NTILE(5) OVER (ORDER BY frequency) AS f_score,
        NTILE(5) OVER (ORDER BY monetary) AS m_score
    FROM base
)
SELECT
    *,
    CONCAT(r_score, f_score, m_score) AS rfm_code,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 4 THEN 'Loyal Customers'
        WHEN r_score >= 4 AND f_score <= 2 THEN 'Promising'
        WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
        WHEN frequency = 0 THEN 'No Purchases'
        ELSE 'Regular'
    END AS segment
FROM scored;
