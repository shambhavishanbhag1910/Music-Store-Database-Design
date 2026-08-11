# Data Model and Grain

## OLTP

The OLTP schema contains 14 core tables with normalized catalogue, customer, playlist, order and payment domains. It uses PostgreSQL ENUMs, identity keys, many-to-many junctions, FK actions, checks, indexes and automatic `updated_at` triggers.

Key production-oriented corrections versus the initial design include:

- no duplicate email unique index
- `TIMESTAMPTZ` for event timestamps
- `order_item.updated_at` for incremental capture
- `artist_role` included in artist junction primary keys
- generated `line_amount`
- updated timestamps on reference/junction tables
- documented catalogue-view grain

## Warehouse

### `dim_customer`

SCD2. One current row per source customer. Historical facts resolve the version active at event time.

### `dim_product`

One row per track or album with natural key `track:<id>` / `album:<id>`. Contains denormalized analytical attributes such as primary artist, primary genre and media type.

### `fact_sales`

Grain: one row per `order_item`.

Measures: quantity, unit price, gross, allocated discount, allocated tax and net amount.

### `fact_payment`

Grain: one row per source payment.

Useful for payment success/failure, mode performance and refund analysis.

### `fact_playlist_activity`

Grain: one row per playlist-track relationship.

Useful for engagement and recommendation-oriented analytics.
