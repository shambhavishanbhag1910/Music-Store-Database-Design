-- Project 2: Customer 360 / Retention Analytics

-- RFM segment distribution
SELECT segment, COUNT(*) AS customers,
       ROUND(AVG(monetary),2) AS avg_lifetime_value,
       ROUND(AVG(frequency),2) AS avg_completed_orders,
       ROUND(AVG(recency_days),2) AS avg_recency_days
FROM marts.customer_rfm
GROUP BY segment
ORDER BY customers DESC;

-- High-value at-risk customers
SELECT customer_id, email, recency_days, frequency, monetary, segment
FROM marts.customer_rfm
WHERE segment='At Risk'
ORDER BY monetary DESC
LIMIT 50;

-- Repeat purchase rate
WITH customer_orders AS (
    SELECT customer_key, COUNT(DISTINCT order_id) AS order_count
    FROM warehouse.fact_sales
    WHERE order_status='completed'
    GROUP BY customer_key
)
SELECT
    COUNT(*) AS purchasing_customers,
    COUNT(*) FILTER (WHERE order_count > 1) AS repeat_customers,
    ROUND(100.0 * COUNT(*) FILTER (WHERE order_count > 1) / NULLIF(COUNT(*),0),2)
        AS repeat_purchase_rate_pct
FROM customer_orders;
