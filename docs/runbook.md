# Operations Runbook

## Pipeline failed

1. Open Airflow task logs and capture `run_id`.
2. Query `audit.etl_run` for the error message.
3. Query `audit.dq_result` for failed data-quality checks.
4. Confirm OLTP and warehouse health.
5. Fix the source/configuration issue.
6. Rerun the DAG. The pipeline is designed to be idempotent and uses overlap extraction.

## Pipeline appears stuck

Check whether an advisory lock remains held by another active session. Airflow also limits the DAG to one active run. Do not manually unlock until confirming the owning run is dead.

## Dashboard is empty

1. Confirm `make seed` was run.
2. Confirm at least one ETL run succeeded.
3. Query `marts.kpi_overview` directly.
4. Verify Grafana datasource health and warehouse credentials.

## Reset local environment

`make reset` removes Docker volumes and recreates databases from SQL initialization files. Then run `make seed` and `make etl`.

## Recovery objective for a real deployment

Define RPO/RTO with the business, enable managed database backups/PITR, test restore procedures, and persist raw extracts outside the warehouse if replayability requirements demand it.
