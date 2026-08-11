-- Role templates for production-style separation of duties.
-- These are NOLOGIN group roles; real login/service identities should be created by the deployment platform.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'warehouse_etl') THEN
        CREATE ROLE warehouse_etl NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'analytics_readonly') THEN
        CREATE ROLE analytics_readonly NOLOGIN;
    END IF;
END
$$;

GRANT USAGE ON SCHEMA audit, staging, warehouse TO warehouse_etl;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA audit, staging, warehouse TO warehouse_etl;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA audit, staging, warehouse TO warehouse_etl;

GRANT USAGE ON SCHEMA marts TO analytics_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA marts TO analytics_readonly;
GRANT SELECT ON audit.etl_run, audit.dq_result, audit.pipeline_metric TO analytics_readonly;

ALTER DEFAULT PRIVILEGES IN SCHEMA marts GRANT SELECT ON TABLES TO analytics_readonly;
