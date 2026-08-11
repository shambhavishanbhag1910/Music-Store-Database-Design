-- Project 4: Playlist Engagement / Recommendation Signals

-- Genres with the most playlist engagement
SELECT genre_name,
       SUM(playlist_adds) AS playlist_adds,
       SUM(unique_customers) AS customer_interactions
FROM marts.playlist_engagement
GROUP BY genre_name
ORDER BY playlist_adds DESC;

-- Artists with high playlist engagement relative to completed sales
WITH engagement AS (
    SELECT artist_name, SUM(playlist_adds) AS playlist_adds
    FROM marts.playlist_engagement
    GROUP BY artist_name
), sales AS (
    SELECT artist_name, units_sold, revenue
    FROM marts.artist_performance
)
SELECT e.artist_name, e.playlist_adds,
       COALESCE(s.units_sold,0) AS units_sold,
       COALESCE(s.revenue,0) AS revenue,
       ROUND(e.playlist_adds::numeric / NULLIF(s.units_sold,0),2) AS engagement_to_sales_ratio
FROM engagement e
LEFT JOIN sales s USING(artist_name)
ORDER BY engagement_to_sales_ratio DESC NULLS LAST
LIMIT 25;
