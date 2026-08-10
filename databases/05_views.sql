CREATE OR REPLACE VIEW vw_music_catalogue AS
SELECT
    t.track_id,
    t.track_name,
    t.track_number,
    t.disc_number,
    t.duration_ms,
    t.unit_price,
    t.is_explicit,
    a.album_id,
    a.album_title,
    a.album_type,
    ar.artist_id,
    ar.artist_name,
    g.genre_name,
    mt.media_type_name
FROM track t
JOIN album a
    ON t.album_id = a.album_id
JOIN album_artist aa
    ON a.album_id = aa.album_id
JOIN artist ar
    ON aa.artist_id = ar.artist_id
LEFT JOIN track_genre tg
    ON t.track_id = tg.track_id
LEFT JOIN genre g
    ON tg.genre_id = g.genre_id
JOIN media_type mt
    ON t.media_type_id = mt.media_type_id;


CREATE OR REPLACE VIEW vw_customer_playlists AS
SELECT
    c.customer_id,
    c.first_name,
    c.last_name,
    p.playlist_id,
    p.playlist_name,
    p.playlist_visibility,
    pt.track_position,
    t.track_id,
    t.track_name
FROM customer c
JOIN playlist p
    ON c.customer_id = p.customer_id
JOIN playlist_track pt
    ON p.playlist_id = pt.playlist_id
JOIN track t
    ON pt.track_id = t.track_id;