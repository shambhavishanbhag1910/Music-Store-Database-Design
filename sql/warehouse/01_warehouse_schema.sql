BEGIN;

CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS warehouse;
CREATE SCHEMA IF NOT EXISTS marts;

CREATE TABLE audit.etl_run (
    run_id UUID PRIMARY KEY,
    pipeline_name TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    status TEXT NOT NULL CHECK (status IN ('running', 'success', 'failed')),
    rows_extracted BIGINT NOT NULL DEFAULT 0,
    rows_loaded BIGINT NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE audit.etl_watermark (
    entity_name TEXT PRIMARY KEY,
    watermark_ts TIMESTAMPTZ NOT NULL DEFAULT '1900-01-01 00:00:00+00',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE audit.dq_result (
    dq_result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES audit.etl_run(run_id) ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'error')),
    passed BOOLEAN NOT NULL,
    failed_rows BIGINT NOT NULL DEFAULT 0,
    details TEXT,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE audit.pipeline_metric (
    metric_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES audit.etl_run(run_id) ON DELETE CASCADE,
    metric_name TEXT NOT NULL,
    metric_value NUMERIC(20,4) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE staging.raw_record (
    batch_id UUID NOT NULL,
    entity_name TEXT NOT NULL,
    natural_key TEXT NOT NULL,
    payload JSONB NOT NULL,
    source_updated_at TIMESTAMPTZ,
    extracted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (batch_id, entity_name, natural_key)
);
CREATE INDEX idx_raw_record_entity_extracted
    ON staging.raw_record(entity_name, extracted_at DESC);
CREATE INDEX idx_raw_record_source_updated
    ON staging.raw_record(entity_name, source_updated_at DESC);

CREATE TABLE warehouse.dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    day_of_month SMALLINT NOT NULL,
    day_of_week SMALLINT NOT NULL,
    day_name VARCHAR(10) NOT NULL,
    week_of_year SMALLINT NOT NULL,
    month SMALLINT NOT NULL,
    month_name VARCHAR(10) NOT NULL,
    quarter SMALLINT NOT NULL,
    year SMALLINT NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

CREATE TABLE warehouse.dim_customer (
    customer_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    country VARCHAR(100),
    status VARCHAR(30) NOT NULL,
    registration_date DATE NOT NULL,
    effective_from TIMESTAMPTZ NOT NULL,
    effective_to TIMESTAMPTZ NOT NULL DEFAULT '9999-12-31 23:59:59+00',
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    record_hash CHAR(64) NOT NULL,
    source_updated_at TIMESTAMPTZ NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_dim_customer_effective_dates CHECK (effective_to > effective_from),
    CONSTRAINT uq_dim_customer_version UNIQUE (customer_id, effective_from)
);
CREATE UNIQUE INDEX uq_dim_customer_current
    ON warehouse.dim_customer(customer_id)
    WHERE is_current;
CREATE INDEX idx_dim_customer_asof
    ON warehouse.dim_customer(customer_id, effective_from, effective_to);

CREATE TABLE warehouse.dim_artist (
    artist_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    artist_id BIGINT NOT NULL UNIQUE,
    artist_name VARCHAR(255) NOT NULL,
    country VARCHAR(100),
    status VARCHAR(30),
    source_updated_at TIMESTAMPTZ,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE warehouse.dim_genre (
    genre_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    genre_id BIGINT NOT NULL UNIQUE,
    genre_name VARCHAR(100) NOT NULL,
    source_updated_at TIMESTAMPTZ,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE warehouse.dim_product (
    product_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_nk TEXT NOT NULL UNIQUE,
    product_type VARCHAR(10) NOT NULL CHECK (product_type IN ('track', 'album')),
    track_id BIGINT,
    album_id BIGINT,
    product_name VARCHAR(255) NOT NULL,
    album_title VARCHAR(255),
    primary_artist VARCHAR(255),
    primary_artist_id BIGINT,
    primary_genre VARCHAR(100),
    primary_genre_id BIGINT,
    media_type VARCHAR(100),
    unit_price NUMERIC(12,2) NOT NULL DEFAULT 0,
    release_date DATE,
    is_explicit BOOLEAN,
    source_updated_at TIMESTAMPTZ,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_dim_product_key CHECK (
        (product_type = 'track' AND track_id IS NOT NULL)
        OR
        (product_type = 'album' AND album_id IS NOT NULL)
    )
);
CREATE INDEX idx_dim_product_artist ON warehouse.dim_product(primary_artist_id);
CREATE INDEX idx_dim_product_genre ON warehouse.dim_product(primary_genre_id);

CREATE TABLE warehouse.fact_sales (
    order_item_id BIGINT PRIMARY KEY,
    order_id BIGINT NOT NULL,
    customer_key BIGINT NOT NULL REFERENCES warehouse.dim_customer(customer_key),
    product_key BIGINT NOT NULL REFERENCES warehouse.dim_product(product_key),
    order_date_key INTEGER NOT NULL REFERENCES warehouse.dim_date(date_key),
    order_ts TIMESTAMPTZ NOT NULL,
    order_status VARCHAR(30) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
    gross_amount NUMERIC(14,2) NOT NULL CHECK (gross_amount >= 0),
    allocated_discount NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (allocated_discount >= 0),
    allocated_tax NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (allocated_tax >= 0),
    net_amount NUMERIC(14,2) NOT NULL,
    source_updated_at TIMESTAMPTZ NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_fact_sales_date ON warehouse.fact_sales(order_date_key);
CREATE INDEX idx_fact_sales_customer ON warehouse.fact_sales(customer_key);
CREATE INDEX idx_fact_sales_product ON warehouse.fact_sales(product_key);
CREATE INDEX idx_fact_sales_order ON warehouse.fact_sales(order_id);

CREATE TABLE warehouse.fact_payment (
    payment_id BIGINT PRIMARY KEY,
    order_id BIGINT NOT NULL,
    customer_key BIGINT NOT NULL REFERENCES warehouse.dim_customer(customer_key),
    payment_date_key INTEGER NOT NULL REFERENCES warehouse.dim_date(date_key),
    payment_ts TIMESTAMPTZ NOT NULL,
    amount NUMERIC(14,2) NOT NULL CHECK (amount > 0),
    payment_status VARCHAR(30) NOT NULL,
    payment_mode VARCHAR(30) NOT NULL,
    transaction_reference VARCHAR(150),
    source_updated_at TIMESTAMPTZ NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_fact_payment_date ON warehouse.fact_payment(payment_date_key);
CREATE INDEX idx_fact_payment_customer ON warehouse.fact_payment(customer_key);
CREATE INDEX idx_fact_payment_order ON warehouse.fact_payment(order_id);

CREATE TABLE warehouse.fact_playlist_activity (
    playlist_id BIGINT NOT NULL,
    track_id BIGINT NOT NULL,
    customer_key BIGINT NOT NULL REFERENCES warehouse.dim_customer(customer_key),
    product_key BIGINT NOT NULL REFERENCES warehouse.dim_product(product_key),
    added_date_key INTEGER NOT NULL REFERENCES warehouse.dim_date(date_key),
    track_position INTEGER NOT NULL CHECK (track_position > 0),
    added_at TIMESTAMPTZ NOT NULL,
    source_updated_at TIMESTAMPTZ NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (playlist_id, track_id)
);

INSERT INTO audit.etl_watermark(entity_name)
VALUES ('customer'), ('product'), ('sales'), ('payment'), ('playlist_activity')
ON CONFLICT DO NOTHING;

COMMIT;
