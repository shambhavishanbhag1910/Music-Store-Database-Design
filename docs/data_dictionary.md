# Data Dictionary Summary

## OLTP

| Table | Grain | Key fields | Purpose |
|---|---|---|---|
| `customer` | one customer | `customer_id`, `email` | customer identity, geography and status |
| `artist` | one artist | `artist_id` | artist master |
| `album` | one album | `album_id` | album master and price |
| `album_artist` | one album/artist/role | composite PK | many-to-many album credits |
| `genre` | one genre | `genre_id`, `genre_name` | genre reference |
| `media_type` | one format | `media_type_id` | file/media format reference |
| `track` | one track | `track_id`, `(album_id, disc_number, track_number)` | track catalogue |
| `track_genre` | one track/genre pair | composite PK | track classification |
| `track_artist` | one track/artist/role | composite PK | track credits |
| `playlist` | one playlist | `playlist_id` | customer playlist header |
| `playlist_track` | one playlist/track pair | composite PK | playlist membership and position |
| `orders` | one order | `order_id` | order header and monetary totals |
| `order_item` | one purchased line | `order_item_id` | track or album order line |
| `payment` | one payment attempt/transaction | `payment_id` | amount, method, status and transaction reference |

## Warehouse

| Table | Grain | Type | Key analytical fields |
|---|---|---|---|
| `dim_date` | one calendar date | dimension | day/week/month/quarter/year |
| `dim_customer` | one customer version | SCD2 dimension | geography, status, effective dates |
| `dim_product` | one track or album | SCD1 dimension | artist, genre, media, price |
| `dim_artist` | one primary artist | dimension | artist natural ID/name |
| `dim_genre` | one primary genre | dimension | genre natural ID/name |
| `fact_sales` | one order item | fact | quantity, gross, discount, tax, net |
| `fact_payment` | one payment | fact | amount, status, mode |
| `fact_playlist_activity` | one playlist/track relation | factless/activity fact | position and added timestamp |

## Audit and staging

| Table | Purpose |
|---|---|
| `staging.raw_record` | append-only raw payload by batch/entity/natural key |
| `audit.etl_watermark` | persisted incremental high-water marks |
| `audit.etl_run` | run status, duration context and row counts |
| `audit.dq_result` | data-quality result per run/check |
| `audit.pipeline_metric` | operational pipeline metrics |
