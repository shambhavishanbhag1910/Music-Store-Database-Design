-- Project 1: Sales Performance Analytics
-- Goal: revenue trend, growth, mix and product contribution.

-- Monthly sales trend and MoM growth
WITH monthly AS (
    SELECT year, month, month_name, revenue, completed_orders
    FROM marts.monthly_sales
    WHERE revenue > 0
), calc AS (
    SELECT *, LAG(revenue) OVER (ORDER BY year, month) AS previous_month_revenue
    FROM monthly
)
SELECT *,
       ROUND(100.0 * (revenue - previous_month_revenue) / NULLIF(previous_month_revenue, 0), 2)
           AS mom_growth_pct
FROM calc
ORDER BY year, month;

-- Revenue concentration by genre
SELECT genre_name, revenue,
       ROUND(100.0 * revenue / NULLIF(SUM(revenue) OVER (), 0), 2) AS revenue_share_pct
FROM marts.genre_performance
ORDER BY revenue DESC;

-- Top products by completed revenue
SELECT p.product_type, p.product_name, p.primary_artist, p.primary_genre,
       SUM(f.quantity) AS units_sold,
       SUM(f.net_amount)::NUMERIC(18,2) AS revenue
FROM warehouse.fact_sales f
JOIN warehouse.dim_product p ON p.product_key=f.product_key
WHERE f.order_status='completed'
GROUP BY p.product_type, p.product_name, p.primary_artist, p.primary_genre
ORDER BY revenue DESC
LIMIT 25;
