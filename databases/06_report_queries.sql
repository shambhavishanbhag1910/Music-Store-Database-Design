SELECT
    t.track_name,
    SUM(oi.quantity) AS units_sold,
    SUM(oi.quantity * oi.unit_price) AS revenue
FROM order_item oi
JOIN track t
    ON oi.track_id = t.track_id
JOIN orders o
    ON oi.order_id = o.order_id
WHERE o.order_status = 'completed'
GROUP BY t.track_id, t.track_name
ORDER BY units_sold DESC;