CREATE OR REPLACE FUNCTION update_modified_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
    table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'customer', 'artist', 'album', 'album_artist', 'genre', 'media_type',
        'track', 'track_genre', 'track_artist', 'playlist', 'playlist_track',
        'orders', 'order_item', 'payment'
    ]
    LOOP
        EXECUTE format(
            'CREATE TRIGGER trg_%I_updated_at BEFORE UPDATE ON %I '
            'FOR EACH ROW EXECUTE FUNCTION update_modified_timestamp()',
            table_name,
            table_name
        );
    END LOOP;
END;
$$;
