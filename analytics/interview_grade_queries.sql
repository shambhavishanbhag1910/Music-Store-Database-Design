-- 1. Executive KPIs
SELECT * FROM marts.kpi_overview;

-- 2. Last 30 days revenue trend
SELECT full_date, completed_orders, units_sold, revenue, customers
FROM marts.daily_sales
WHERE full_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY full_date;

-- 3. Monthly revenue with month-over-month growth
WITH monthly AS (
    SELECT year, month, month_name, revenue
    FROM marts.monthly_sales
    WHERE revenue > 0
), growth AS (
    SELECT *, LAG(revenue) OVER (ORDER BY year, month) AS prior_revenue
    FROM monthly
)
SELECT *,
       ROUND(100.0 * (revenue - prior_revenue) / NULLIF(prior_revenue, 0), 2) AS mom_growth_pct
FROM growth
ORDER BY year, month;

-- 4. Top genres
SELECT * FROM marts.genre_performance
ORDER BY revenue DESC
LIMIT 10;

-- 5. Top artists
SELECT * FROM marts.artist_performance
ORDER BY revenue DESC
LIMIT 10;

-- 6. Customer lifetime value
SELECT customer_id, first_name, last_name, country, completed_orders, lifetime_value, avg_order_value
FROM marts.customer_value
ORDER BY lifetime_value DESC
LIMIT 25;

-- 7. RFM customer segmentation
SELECT segment, COUNT(*) AS customers, ROUND(AVG(monetary), 2) AS avg_monetary
FROM marts.customer_rfm
GROUP BY segment
ORDER BY customers DESC;

-- 8. Payment failure hotspots
SELECT payment_mode,
       SUM(payment_attempts) AS attempts,
       SUM(failed_payments) AS failures,
       ROUND(100.0 * SUM(failed_payments) / NULLIF(SUM(payment_attempts), 0), 2) AS failure_rate_pct
FROM marts.payment_performance
GROUP BY payment_mode
ORDER BY failure_rate_pct DESC;

-- 9. Playlist engagement by genre
SELECT genre_name, SUM(playlist_adds) AS playlist_adds, SUM(unique_customers) AS customer_interactions
FROM marts.playlist_engagement
GROUP BY genre_name
ORDER BY playlist_adds DESC
LIMIT 10;

-- 10. Repeat purchase rate
WITH customer_orders AS (
    SELECT customer_key, COUNT(DISTINCT order_id) AS orders
    FROM warehouse.fact_sales
    WHERE order_status='completed'
    GROUP BY customer_key
)
SELECT
    COUNT(*) FILTER (WHERE orders > 1) AS repeat_customers,
    COUNT(*) AS purchasing_customers,
    ROUND(100.0 * COUNT(*) FILTER (WHERE orders > 1) / NULLIF(COUNT(*), 0), 2) AS repeat_rate_pct
FROM customer_orders;

-- 11. Country revenue contribution
SELECT c.country,
       COUNT(DISTINCT f.order_id) AS orders,
       SUM(f.net_amount)::NUMERIC(18,2) AS revenue
FROM warehouse.fact_sales f
JOIN warehouse.dim_customer c ON c.customer_key=f.customer_key
WHERE f.order_status='completed'
GROUP BY c.country
ORDER BY revenue DESC;

-- 12. Product affinity: tracks commonly purchased in the same order
WITH track_orders AS (
    SELECT DISTINCT order_id, product_key
    FROM warehouse.fact_sales f
    JOIN warehouse.dim_product p USING(product_key)
    WHERE f.order_status='completed' AND p.product_type='track'
)
SELECT p1.product_name AS track_a,
       p2.product_name AS track_b,
       COUNT(*) AS orders_together
FROM track_orders a
JOIN track_orders b ON a.order_id=b.order_id AND a.product_key < b.product_key
JOIN warehouse.dim_product p1 ON p1.product_key=a.product_key
JOIN warehouse.dim_product p2 ON p2.product_key=b.product_key
GROUP BY p1.product_name, p2.product_name
ORDER BY orders_together DESC
LIMIT 20;

-- 13. Customer cohort by first purchase month
WITH first_purchase AS (
    SELECT customer_key, DATE_TRUNC('month', MIN(order_ts))::date AS cohort_month
    FROM warehouse.fact_sales
    WHERE order_status='completed'
    GROUP BY customer_key
), activity AS (
    SELECT DISTINCT customer_key, DATE_TRUNC('month', order_ts)::date AS activity_month
    FROM warehouse.fact_sales
    WHERE order_status='completed'
)
SELECT f.cohort_month,
       a.activity_month,
       ((EXTRACT(YEAR FROM a.activity_month) - EXTRACT(YEAR FROM f.cohort_month)) * 12
        + EXTRACT(MONTH FROM a.activity_month) - EXTRACT(MONTH FROM f.cohort_month))::int AS month_number,
       COUNT(DISTINCT a.customer_key) AS active_customers
FROM first_purchase f
JOIN activity a USING(customer_key)
GROUP BY f.cohort_month, a.activity_month
ORDER BY f.cohort_month, a.activity_month;

-- 14. ETL run reliability
SELECT
    DATE_TRUNC('day', started_at)::date AS run_date,
    COUNT(*) AS runs,
    COUNT(*) FILTER (WHERE status='success') AS successful_runs,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status='success') / NULLIF(COUNT(*),0), 2) AS success_rate_pct,
    AVG(EXTRACT(EPOCH FROM (ended_at-started_at)))::NUMERIC(12,2) AS avg_duration_seconds
FROM audit.etl_run
GROUP BY DATE_TRUNC('day', started_at)
ORDER BY run_date DESC;

-- 15. Failed data-quality checks
SELECT r.started_at, d.check_name, d.severity, d.failed_rows, d.details
FROM audit.dq_result d
JOIN audit.etl_run r ON r.run_id=d.run_id
WHERE NOT d.passed
ORDER BY r.started_at DESC, d.severity DESC;
