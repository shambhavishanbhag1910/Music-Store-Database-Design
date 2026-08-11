# Architecture Decisions

## ADR-001: Separate OLTP and analytical databases

The operational database is optimized for normalized transactional integrity. The warehouse is optimized for historical analysis, stable fact grain and reusable marts. Grafana is intentionally connected to the warehouse, not OLTP.

## ADR-002: Incremental timestamp watermarks with overlap

For the portfolio implementation, source `updated_at` timestamps are the change signal. Each entity stores its high watermark in `audit.etl_watermark`. Extraction subtracts a small overlap period and targets are idempotently upserted.

At higher scale, replace timestamp polling with CDC where latency, delete capture or source load justifies it.

## ADR-003: SCD2 customer dimension

Customer city/country/status can change and those historical attributes may matter for past sales analysis. Customer therefore uses SCD2. Product uses a simpler SCD1 upsert in this release because catalogue correction is treated as current-state enrichment.

## ADR-004: Generic raw JSONB staging

Raw payload staging reduces source/target coupling and keeps replay/debug evidence. For very high volume, move raw immutable records to object storage and use warehouse-native external tables/lakehouse formats.

## ADR-005: Data-quality gate in the pipeline transaction

Error-level DQ failures roll back warehouse changes and mark the run failed. Warning-level checks are recorded without blocking the load.

## ADR-006: Local Compose, production Kubernetes/managed orchestration

Docker Compose maximizes recruiter/interviewer reproducibility. Production deployment is deliberately separated and documented to avoid presenting a development topology as secure/HA production infrastructure.
