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
    aa.artist_role AS album_artist_role,
    g.genre_name,
    mt.media_type_name
FROM track t
JOIN album a ON a.album_id = t.album_id
JOIN album_artist aa ON aa.album_id = a.album_id
JOIN artist ar ON ar.artist_id = aa.artist_id
LEFT JOIN track_genre tg ON tg.track_id = t.track_id
LEFT JOIN genre g ON g.genre_id = tg.genre_id
JOIN media_type mt ON mt.media_type_id = t.media_type_id;

COMMENT ON VIEW vw_music_catalogue IS
'Grain: one row per track x album-artist-role x genre combination. Multi-artist or multi-genre tracks can produce multiple rows.';
