# Production Deployment Blueprint

This directory documents how to take the reproducible local stack to a production environment.

## Recommended topology

- OLTP: managed PostgreSQL, Multi-AZ/HA, PITR, private subnet, TLS required
- Warehouse: managed PostgreSQL for moderate scale or a cloud analytical warehouse at larger scale
- Orchestration: managed Airflow or Apache Airflow on Kubernetes using the official Helm chart
- Secrets: cloud secret manager + workload identity; never `.env` files in production
- Raw archive: object storage for immutable extracts/CDC when replay/audit requirements justify it
- BI: Grafana with SSO, RBAC and a production PostgreSQL configuration DB
- Observability: centralized logs, metrics, alerts and on-call routing

## Security controls

- separate DB roles for source read, warehouse write and BI read-only access
- deny public database exposure
- TLS in transit and encryption at rest
- secret rotation
- network policies/security groups
- container image scanning and signed images
- least privilege service accounts
- audit logs

## Reliability controls

- database HA, automated backups and tested restores
- Airflow scheduler/worker scaling appropriate to executor
- retry policy with bounded backoff
- idempotent loads
- advisory/concurrency controls
- DQ blocking rules and warning thresholds
- SLA monitoring for freshness and runtime
- dead-letter/replay strategy for CDC/event-driven extensions

## Deployment workflow

1. Build immutable pipeline and Airflow images.
2. Run unit/integration tests.
3. Apply database migrations with a controlled migration job.
4. Deploy to a non-production namespace/environment.
5. Run smoke ETL and DQ tests.
6. Promote the same image digest to production.
7. Validate marts and dashboards.
8. Monitor error rate, freshness and latency.

## Scaling path

When source volume grows beyond efficient PostgreSQL timestamp extraction:

- PostgreSQL logical replication / Debezium CDC
- Kafka/Kinesis/Pub/Sub transport where needed
- object-storage bronze zone
- Spark/Flink for high-volume processing
- dbt/warehouse-native SQL for transformations
- OpenLineage for lineage capture
