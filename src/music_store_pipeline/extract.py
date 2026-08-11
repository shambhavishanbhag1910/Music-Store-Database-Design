from __future__ import annotations

from datetime import datetime
from typing import Any

from psycopg import Connection


CUSTOMER_SQL = """
SELECT
    customer_id, first_name, last_name, email, phone_no, city, country,
    registration_date, status::text AS status, created_at, updated_at,
    updated_at AS source_updated_at
FROM customer
WHERE updated_at > %(watermark)s
ORDER BY updated_at, customer_id
"""

PRODUCT_SQL = """
WITH track_products AS (
    SELECT
        'track:' || t.track_id AS product_nk,
        'track'::text AS product_type,
        t.track_id,
        a.album_id,
        t.track_name AS product_name,
        a.album_title,
        pa.artist_name AS primary_artist,
        pa.artist_id AS primary_artist_id,
        pg.genre_name AS primary_genre,
        pg.genre_id AS primary_genre_id,
        mt.media_type_name AS media_type,
        t.unit_price,
        COALESCE(t.release_date, a.release_date) AS release_date,
        t.is_explicit,
        GREATEST(t.updated_at, a.updated_at, COALESCE(pa.updated_at, t.updated_at),
                 COALESCE(pg.updated_at, t.updated_at), mt.updated_at) AS source_updated_at
    FROM track t
    JOIN album a ON a.album_id = t.album_id
    JOIN media_type mt ON mt.media_type_id = t.media_type_id
    LEFT JOIN LATERAL (
        SELECT ar.artist_id, ar.artist_name, ar.updated_at
        FROM track_artist ta
        JOIN artist ar ON ar.artist_id = ta.artist_id
        WHERE ta.track_id = t.track_id
        ORDER BY CASE ta.artist_role WHEN 'primary' THEN 0 ELSE 1 END, ar.artist_id
        LIMIT 1
    ) pa ON TRUE
    LEFT JOIN LATERAL (
        SELECT g.genre_id, g.genre_name, g.updated_at
        FROM track_genre tg
        JOIN genre g ON g.genre_id = tg.genre_id
        WHERE tg.track_id = t.track_id
        ORDER BY g.genre_id
        LIMIT 1
    ) pg ON TRUE
), album_products AS (
    SELECT
        'album:' || a.album_id AS product_nk,
        'album'::text AS product_type,
        NULL::bigint AS track_id,
        a.album_id,
        a.album_title AS product_name,
        a.album_title,
        pa.artist_name AS primary_artist,
        pa.artist_id AS primary_artist_id,
        NULL::varchar AS primary_genre,
        NULL::bigint AS primary_genre_id,
        NULL::varchar AS media_type,
        a.album_price AS unit_price,
        a.release_date,
        NULL::boolean AS is_explicit,
        GREATEST(a.updated_at, COALESCE(pa.updated_at, a.updated_at)) AS source_updated_at
    FROM album a
    LEFT JOIN LATERAL (
        SELECT ar.artist_id, ar.artist_name, ar.updated_at
        FROM album_artist aa
        JOIN artist ar ON ar.artist_id = aa.artist_id
        WHERE aa.album_id = a.album_id
        ORDER BY CASE aa.artist_role WHEN 'primary' THEN 0 ELSE 1 END, ar.artist_id
        LIMIT 1
    ) pa ON TRUE
)
SELECT * FROM track_products
UNION ALL
SELECT * FROM album_products
ORDER BY product_nk
"""

SALES_SQL = """
WITH changed_orders AS (
    SELECT o.order_id
    FROM orders o
    LEFT JOIN order_item oi ON oi.order_id = o.order_id
    GROUP BY o.order_id, o.updated_at
    HAVING GREATEST(o.updated_at, COALESCE(MAX(oi.updated_at), o.updated_at)) > %(watermark)s
)
SELECT
    oi.order_item_id,
    o.order_id,
    o.customer_id,
    o.order_date,
    o.order_status::text AS order_status,
    o.currency,
    o.subtotal,
    o.tax_amount,
    o.discount_amount,
    o.total_amount,
    oi.track_id,
    oi.album_id,
    CASE WHEN oi.track_id IS NOT NULL
         THEN 'track:' || oi.track_id
         ELSE 'album:' || oi.album_id END AS product_nk,
    oi.unit_price,
    oi.quantity,
    oi.line_amount AS gross_amount,
    GREATEST(o.updated_at, oi.updated_at) AS source_updated_at
FROM changed_orders co
JOIN orders o ON o.order_id = co.order_id
JOIN order_item oi ON oi.order_id = o.order_id
ORDER BY o.order_id, oi.order_item_id
"""

PAYMENT_SQL = """
SELECT
    p.payment_id, p.order_id, o.customer_id,
    p.payment_date, p.amount, p.payment_status::text AS payment_status,
    p.payment_mode::text AS payment_mode, p.transaction_reference,
    GREATEST(p.updated_at, o.updated_at) AS source_updated_at
FROM payment p
JOIN orders o ON o.order_id = p.order_id
WHERE GREATEST(p.updated_at, o.updated_at) > %(watermark)s
ORDER BY source_updated_at, p.payment_id
"""

PLAYLIST_SQL = """
SELECT
    p.playlist_id, p.customer_id, pt.track_id, pt.track_position, pt.added_at,
    p.playlist_id || ':' || pt.track_id AS activity_nk,
    'track:' || pt.track_id AS product_nk,
    GREATEST(p.updated_at, pt.updated_at) AS source_updated_at
FROM playlist p
JOIN playlist_track pt ON pt.playlist_id = p.playlist_id
WHERE GREATEST(p.updated_at, pt.updated_at) > %(watermark)s
ORDER BY source_updated_at, p.playlist_id, pt.track_id
"""


def fetch_rows(conn: Connection, sql: str, watermark: datetime | None = None) -> list[dict[str, Any]]:
    params = {"watermark": watermark} if watermark is not None else None
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())
