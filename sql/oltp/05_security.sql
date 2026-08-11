-- Read-only role template for ETL extraction.
-- Bind a real login/service identity to this group role in deployment automation.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'music_store_etl_reader') THEN
        CREATE ROLE music_store_etl_reader NOLOGIN;
    END IF;
END
$$;

GRANT USAGE ON SCHEMA public TO music_store_etl_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO music_store_etl_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO music_store_etl_reader;
