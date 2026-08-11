from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from .config import Settings
from .db import connect
from .extract import CUSTOMER_SQL, PAYMENT_SQL, PLAYLIST_SQL, PRODUCT_SQL, SALES_SQL, fetch_rows
from .load import (
    stage_rows,
    upsert_customers_scd2,
    upsert_payments,
    upsert_playlist_activity,
    upsert_products,
    upsert_sales,
)
from .quality import (
    assert_no_error_failures,
    persist_quality_results,
    run_quality_checks,
)
from .transform import allocate_order_rows

logger = logging.getLogger(__name__)


class PipelineLockUnavailable(RuntimeError):
    pass


def _get_watermark(conn, entity: str, overlap_minutes: int) -> datetime:
    with conn.cursor() as cur:
        cur.execute("SELECT watermark_ts FROM audit.etl_watermark WHERE entity_name=%s", (entity,))
        row = cur.fetchone()
        watermark = row["watermark_ts"] if row else datetime(1900, 1, 1, tzinfo=timezone.utc)
    return watermark - timedelta(minutes=overlap_minutes)


def _set_watermark(conn, entity: str, rows: list[dict[str, Any]]) -> None:
    timestamps = [r.get("source_updated_at") for r in rows if r.get("source_updated_at")]
    if not timestamps:
        return
    max_ts = max(timestamps)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO audit.etl_watermark(entity_name, watermark_ts, updated_at)
            VALUES (%s,%s,NOW())
            ON CONFLICT (entity_name) DO UPDATE
            SET watermark_ts=GREATEST(audit.etl_watermark.watermark_ts, EXCLUDED.watermark_ts),
                updated_at=NOW()
            """,
            (entity, max_ts),
        )


def _record_metric(conn, run_id: str, name: str, value: int | float) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO audit.pipeline_metric(run_id, metric_name, metric_value) VALUES (%s::uuid,%s,%s)",
            (run_id, name, value),
        )


def _extract_entity(source_conn, warehouse_conn, run_id: str, entity: str, sql: str, key: str,
                    watermark: datetime | None) -> list[dict[str, Any]]:
    started = time.perf_counter()
    rows = fetch_rows(source_conn, sql, watermark)
    stage_rows(warehouse_conn, run_id, entity, rows, key)
    duration_ms = int((time.perf_counter() - started) * 1000)
    logger.info(
        "Extracted entity",
        extra={"run_id": run_id, "entity": entity, "rows": len(rows), "duration_ms": duration_ms},
    )
    _record_metric(warehouse_conn, run_id, f"{entity}.rows_extracted", len(rows))
    _record_metric(warehouse_conn, run_id, f"{entity}.extract_duration_ms", duration_ms)
    return rows


def run_pipeline(settings: Settings) -> str:
    run_id = str(uuid.uuid4())
    pipeline_started = time.perf_counter()

    with connect(settings.warehouse) as warehouse_conn:
        with warehouse_conn.cursor() as cur:
            cur.execute("SELECT pg_try_advisory_lock(hashtext(%s)) AS locked", (settings.pipeline_name,))
            if not cur.fetchone()["locked"]:
                raise PipelineLockUnavailable("Another pipeline run already owns the advisory lock")
            cur.execute(
                "INSERT INTO audit.etl_run(run_id, pipeline_name, status) VALUES (%s::uuid,%s,'running')",
                (run_id, settings.pipeline_name),
            )
        warehouse_conn.commit()

        rows_extracted = 0
        rows_loaded = 0
        quality_results: list[dict[str, Any]] = []
        try:
            with connect(settings.oltp) as source_conn:
                customer_wm = _get_watermark(warehouse_conn, "customer", settings.overlap_minutes)
                sales_wm = _get_watermark(warehouse_conn, "sales", settings.overlap_minutes)
                payment_wm = _get_watermark(warehouse_conn, "payment", settings.overlap_minutes)
                playlist_wm = _get_watermark(warehouse_conn, "playlist_activity", settings.overlap_minutes)

                customers = _extract_entity(
                    source_conn, warehouse_conn, run_id, "customer", CUSTOMER_SQL, "customer_id", customer_wm
                )
                products = _extract_entity(
                    source_conn, warehouse_conn, run_id, "product", PRODUCT_SQL, "product_nk", None
                )
                sales = _extract_entity(
                    source_conn, warehouse_conn, run_id, "sales", SALES_SQL, "order_item_id", sales_wm
                )
                payments = _extract_entity(
                    source_conn, warehouse_conn, run_id, "payment", PAYMENT_SQL, "payment_id", payment_wm
                )
                playlists = _extract_entity(
                    source_conn, warehouse_conn, run_id, "playlist_activity", PLAYLIST_SQL,
                    "activity_nk", playlist_wm
                )

            rows_extracted = sum(map(len, (customers, products, sales, payments, playlists)))

            rows_loaded += upsert_customers_scd2(warehouse_conn, customers)
            rows_loaded += upsert_products(warehouse_conn, products)
            rows_loaded += upsert_sales(warehouse_conn, allocate_order_rows(sales))
            rows_loaded += upsert_payments(warehouse_conn, payments)
            rows_loaded += upsert_playlist_activity(warehouse_conn, playlists)

            _set_watermark(warehouse_conn, "customer", customers)
            _set_watermark(warehouse_conn, "product", products)
            _set_watermark(warehouse_conn, "sales", sales)
            _set_watermark(warehouse_conn, "payment", payments)
            _set_watermark(warehouse_conn, "playlist_activity", playlists)

            quality_results = run_quality_checks(
                warehouse_conn
            )

            assert_no_error_failures(
                quality_results
            )

            persist_quality_results(
                warehouse_conn,
                run_id,
                quality_results,
            )

            with warehouse_conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM staging.raw_record WHERE extracted_at < NOW() - INTERVAL '30 days'"
                )
                cur.execute(
                    """
                    UPDATE audit.etl_run
                    SET ended_at=NOW(), status='success', rows_extracted=%s, rows_loaded=%s
                    WHERE run_id=%s::uuid
                    """,
                    (rows_extracted, rows_loaded, run_id),
                )
                cur.execute("SELECT pg_advisory_unlock(hashtext(%s))", (settings.pipeline_name,))
            _record_metric(
                warehouse_conn, run_id, "pipeline.duration_ms", int((time.perf_counter()-pipeline_started)*1000)
            )
            warehouse_conn.commit()
            logger.info(
                "Pipeline completed successfully",
                extra={"run_id": run_id, "rows": rows_loaded,
                       "duration_ms": int((time.perf_counter()-pipeline_started)*1000)},
            )
            return run_id
        except Exception as exc:
            warehouse_conn.rollback()
            if quality_results:
                persist_quality_results(
                    warehouse_conn,
                    run_id,
                    quality_results,
            )
            with warehouse_conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE audit.etl_run
                    SET ended_at=NOW(), status='failed', rows_extracted=%s, rows_loaded=%s,
                        error_message=%s
                    WHERE run_id=%s::uuid
                    """,
                    (rows_extracted, rows_loaded, str(exc)[:4000], run_id),
                )
                cur.execute("SELECT pg_advisory_unlock(hashtext(%s))", (settings.pipeline_name,))
            warehouse_conn.commit()
            logger.exception("Pipeline failed", extra={"run_id": run_id})
            raise
