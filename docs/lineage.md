# Data Lineage

```text
OLTP.customer
  -> staging.raw_record(entity=customer)
  -> warehouse.dim_customer (SCD2)
  -> marts.customer_value
  -> marts.customer_rfm
  -> Grafana / analytical SQL

OLTP.orders + OLTP.order_item
  -> staging.raw_record(entity=sales)
  -> tax/discount allocation
  -> warehouse.fact_sales
  -> marts.daily_sales / monthly_sales / genre_performance / artist_performance
  -> Grafana

OLTP.payment + OLTP.orders
  -> staging.raw_record(entity=payment)
  -> warehouse.fact_payment
  -> marts.payment_performance

OLTP.playlist + OLTP.playlist_track
  -> staging.raw_record(entity=playlist_activity)
  -> warehouse.fact_playlist_activity
  -> marts.playlist_engagement

OLTP.track/album/artist/genre/media_type relationships
  -> staging.raw_record(entity=product)
  -> warehouse.dim_product + dim_artist + dim_genre
  -> sales and playlist analytics
```

Every pipeline run also writes to `audit.etl_run`, `audit.etl_watermark`, `audit.pipeline_metric` and `audit.dq_result`.
