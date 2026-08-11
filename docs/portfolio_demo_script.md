# 7-Minute Portfolio Demo Script

1. **Problem (30 sec):** normalized music-store transactions are excellent for operations but not ideal for historical BI and ML-ready analytics.
2. **OLTP design (60 sec):** show ERD, constraints, junction tables, indexes, update timestamps and order-item product rule.
3. **Pipeline (90 sec):** explain watermark + overlap, raw staging, idempotency, advisory lock and Airflow retries.
4. **Warehouse (90 sec):** explain star schema, fact grain, SCD2 customer history and exact tax/discount allocation.
5. **Quality/observability (60 sec):** show `audit.etl_run`, `audit.dq_result`, watermarks and structured logs.
6. **Analytics (60 sec):** show Grafana KPIs, trends, genre/artist rankings and RFM segmentation.
7. **Production path (30 sec):** local Compose is reproducible; real production uses managed PostgreSQL, secrets, private networking, Kubernetes/managed Airflow, backups and centralized monitoring.
