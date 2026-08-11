from __future__ import annotations

import subprocess

import pendulum
from airflow.sdk import dag, task


@dag(
    dag_id="music_store_data_platform",
    schedule="0 * * * *",
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=["music-store", "data-engineering", "analytics"],
    default_args={"retries": 3, "retry_delay": pendulum.duration(minutes=5)},
)
def music_store_data_platform():
    @task(execution_timeout=pendulum.duration(minutes=30))
    def run_incremental_etl() -> None:
        subprocess.run(["music-store-etl", "run"], check=True)

    run_incremental_etl()


music_store_data_platform()
