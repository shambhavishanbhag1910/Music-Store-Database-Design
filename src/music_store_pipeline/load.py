from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Iterable

from psycopg import Connection


def _hash_customer(row: dict[str, Any]) -> str:
    values = [
        row.get("first_name"), row.get("last_name"), row.get("email"),
        row.get("city"), row.get("country"), row.get("status"),
        row.get("registration_date"),
    ]
    return hashlib.sha256("|".join("" if v is None else str(v) for v in values).encode()).hexdigest()


def _json_payload(row: dict[str, Any]) -> str:
    return json.dumps(row, default=str, sort_keys=True)


def stage_rows(
    conn: Connection,
    batch_id: str,
    entity_name: str,
    rows: Iterable[dict[str, Any]],
    key_field: str,
) -> int:
    count = 0
    with conn.cursor() as cur:
        for row in rows:
            cur.execute(
                """
                INSERT INTO staging.raw_record
                    (batch_id, entity_name, natural_key, payload, source_updated_at)
                VALUES (%s::uuid, %s, %s, %s::jsonb, %s)
                ON CONFLICT (batch_id, entity_name, natural_key) DO NOTHING
                """,
                (
                    batch_id,
                    entity_name,
                    str(row[key_field]),
                    _json_payload(row),
                    row.get("source_updated_at"),
                ),
            )
            count += cur.rowcount
    return count


def upsert_customers_scd2(conn: Connection, rows: list[dict[str, Any]]) -> int:
    loaded = 0
    with conn.cursor() as cur:
        for row in rows:
            customer_id = int(row["customer_id"])
            record_hash = _hash_customer(row)
            source_ts = row["source_updated_at"]
            cur.execute(
                """
                SELECT customer_key, record_hash, effective_from
                FROM warehouse.dim_customer
                WHERE customer_id = %s AND is_current
                FOR UPDATE
                """,
                (customer_id,),
            )
            current = cur.fetchone()
            if current and current["record_hash"] == record_hash:
                cur.execute(
                    """
                    UPDATE warehouse.dim_customer
                    SET source_updated_at = GREATEST(source_updated_at, %s), loaded_at = NOW()
                    WHERE customer_key = %s
                    """,
                    (source_ts, current["customer_key"]),
                )
                continue

            effective_from = datetime(1900, 1, 1, tzinfo=timezone.utc) if not current else source_ts
            if current and source_ts <= current["effective_from"]:
                cur.execute(
                    """
                    UPDATE warehouse.dim_customer
                    SET first_name=%s, last_name=%s, email=%s, city=%s, country=%s,
                        status=%s, registration_date=%s, record_hash=%s,
                        source_updated_at=%s, loaded_at=NOW()
                    WHERE customer_key=%s
                    """,
                    (
                        row["first_name"], row["last_name"], row["email"], row.get("city"),
                        row.get("country"), row["status"], row["registration_date"], record_hash,
                        source_ts, current["customer_key"],
                    ),
                )
                loaded += 1
                continue

            if current:
                cur.execute(
                    """
                    UPDATE warehouse.dim_customer
                    SET effective_to=%s, is_current=FALSE, loaded_at=NOW()
                    WHERE customer_key=%s
                    """,
                    (source_ts, current["customer_key"]),
                )

            cur.execute(
                """
                INSERT INTO warehouse.dim_customer (
                    customer_id, first_name, last_name, email, city, country, status,
                    registration_date, effective_from, record_hash, source_updated_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    customer_id, row["first_name"], row["last_name"], row["email"],
                    row.get("city"), row.get("country"), row["status"], row["registration_date"],
                    effective_from, record_hash, source_ts,
                ),
            )
            loaded += 1
    return loaded


def upsert_products(conn: Connection, rows: list[dict[str, Any]]) -> int:
    loaded = 0
    with conn.cursor() as cur:
        for row in rows:
            if row.get("primary_artist_id") is not None:
                cur.execute(
                    """
                    INSERT INTO warehouse.dim_artist(artist_id, artist_name, source_updated_at)
                    VALUES (%s,%s,%s)
                    ON CONFLICT (artist_id) DO UPDATE
                    SET artist_name=EXCLUDED.artist_name,
                        source_updated_at=EXCLUDED.source_updated_at,
                        loaded_at=NOW()
                    """,
                    (row["primary_artist_id"], row.get("primary_artist") or "Unknown", row["source_updated_at"]),
                )
            if row.get("primary_genre_id") is not None:
                cur.execute(
                    """
                    INSERT INTO warehouse.dim_genre(genre_id, genre_name, source_updated_at)
                    VALUES (%s,%s,%s)
                    ON CONFLICT (genre_id) DO UPDATE
                    SET genre_name=EXCLUDED.genre_name,
                        source_updated_at=EXCLUDED.source_updated_at,
                        loaded_at=NOW()
                    """,
                    (row["primary_genre_id"], row.get("primary_genre") or "Unknown", row["source_updated_at"]),
                )
            cur.execute(
                """
                INSERT INTO warehouse.dim_product (
                    product_nk, product_type, track_id, album_id, product_name, album_title,
                    primary_artist, primary_artist_id, primary_genre, primary_genre_id,
                    media_type, unit_price, release_date, is_explicit, source_updated_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (product_nk) DO UPDATE SET
                    product_name=EXCLUDED.product_name,
                    album_title=EXCLUDED.album_title,
                    primary_artist=EXCLUDED.primary_artist,
                    primary_artist_id=EXCLUDED.primary_artist_id,
                    primary_genre=EXCLUDED.primary_genre,
                    primary_genre_id=EXCLUDED.primary_genre_id,
                    media_type=EXCLUDED.media_type,
                    unit_price=EXCLUDED.unit_price,
                    release_date=EXCLUDED.release_date,
                    is_explicit=EXCLUDED.is_explicit,
                    source_updated_at=EXCLUDED.source_updated_at,
                    loaded_at=NOW()
                """,
                (
                    row["product_nk"], row["product_type"], row.get("track_id"), row.get("album_id"),
                    row["product_name"], row.get("album_title"), row.get("primary_artist"),
                    row.get("primary_artist_id"), row.get("primary_genre"), row.get("primary_genre_id"),
                    row.get("media_type"), row["unit_price"], row.get("release_date"),
                    row.get("is_explicit"), row["source_updated_at"],
                ),
            )
            loaded += 1
    return loaded


def ensure_date(conn: Connection, value: datetime) -> int:
    date_value = value.date()
    date_key = int(date_value.strftime("%Y%m%d"))
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO warehouse.dim_date (
                date_key, full_date, day_of_month, day_of_week, day_name, week_of_year,
                month, month_name, quarter, year, is_weekend
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (date_key) DO NOTHING
            """,
            (
                date_key, date_value, date_value.day, date_value.isoweekday(),
                date_value.strftime("%A"), date_value.isocalendar().week, date_value.month,
                date_value.strftime("%B"), ((date_value.month - 1) // 3) + 1,
                date_value.year, date_value.isoweekday() >= 6,
            ),
        )
    return date_key


def customer_key_as_of(conn: Connection, customer_id: int, event_ts: datetime) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT customer_key
            FROM warehouse.dim_customer
            WHERE customer_id=%s AND %s >= effective_from AND %s < effective_to
            ORDER BY effective_from DESC
            LIMIT 1
            """,
            (customer_id, event_ts, event_ts),
        )
        row = cur.fetchone()
        if not row:
            cur.execute(
                "SELECT customer_key FROM warehouse.dim_customer WHERE customer_id=%s AND is_current",
                (customer_id,),
            )
            row = cur.fetchone()
        if not row:
            raise RuntimeError(f"No customer dimension row for customer_id={customer_id}")
        return int(row["customer_key"])


def product_key(conn: Connection, product_nk: str) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT product_key FROM warehouse.dim_product WHERE product_nk=%s", (product_nk,))
        row = cur.fetchone()
        if not row:
            raise RuntimeError(f"No product dimension row for {product_nk}")
        return int(row["product_key"])


def upsert_sales(conn: Connection, rows: list[dict[str, Any]]) -> int:
    loaded = 0
    with conn.cursor() as cur:
        for row in rows:
            customer_key = customer_key_as_of(conn, int(row["customer_id"]), row["order_date"])
            prod_key = product_key(conn, row["product_nk"])
            date_key = ensure_date(conn, row["order_date"])
            cur.execute(
                """
                INSERT INTO warehouse.fact_sales (
                    order_item_id, order_id, customer_key, product_key, order_date_key,
                    order_ts, order_status, currency, quantity, unit_price, gross_amount,
                    allocated_discount, allocated_tax, net_amount, source_updated_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (order_item_id) DO UPDATE SET
                    customer_key=EXCLUDED.customer_key,
                    product_key=EXCLUDED.product_key,
                    order_date_key=EXCLUDED.order_date_key,
                    order_ts=EXCLUDED.order_ts,
                    order_status=EXCLUDED.order_status,
                    currency=EXCLUDED.currency,
                    quantity=EXCLUDED.quantity,
                    unit_price=EXCLUDED.unit_price,
                    gross_amount=EXCLUDED.gross_amount,
                    allocated_discount=EXCLUDED.allocated_discount,
                    allocated_tax=EXCLUDED.allocated_tax,
                    net_amount=EXCLUDED.net_amount,
                    source_updated_at=EXCLUDED.source_updated_at,
                    loaded_at=NOW()
                """,
                (
                    row["order_item_id"], row["order_id"], customer_key, prod_key, date_key,
                    row["order_date"], row["order_status"], row["currency"], row["quantity"],
                    row["unit_price"], row["gross_amount"], row["allocated_discount"],
                    row["allocated_tax"], row["net_amount"], row["source_updated_at"],
                ),
            )
            loaded += 1
    return loaded


def upsert_payments(conn: Connection, rows: list[dict[str, Any]]) -> int:
    loaded = 0
    with conn.cursor() as cur:
        for row in rows:
            customer_key = customer_key_as_of(conn, int(row["customer_id"]), row["payment_date"])
            date_key = ensure_date(conn, row["payment_date"])
            cur.execute(
                """
                INSERT INTO warehouse.fact_payment (
                    payment_id, order_id, customer_key, payment_date_key, payment_ts,
                    amount, payment_status, payment_mode, transaction_reference, source_updated_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (payment_id) DO UPDATE SET
                    customer_key=EXCLUDED.customer_key,
                    payment_date_key=EXCLUDED.payment_date_key,
                    payment_ts=EXCLUDED.payment_ts,
                    amount=EXCLUDED.amount,
                    payment_status=EXCLUDED.payment_status,
                    payment_mode=EXCLUDED.payment_mode,
                    transaction_reference=EXCLUDED.transaction_reference,
                    source_updated_at=EXCLUDED.source_updated_at,
                    loaded_at=NOW()
                """,
                (
                    row["payment_id"], row["order_id"], customer_key, date_key, row["payment_date"],
                    row["amount"], row["payment_status"], row["payment_mode"],
                    row.get("transaction_reference"), row["source_updated_at"],
                ),
            )
            loaded += 1
    return loaded


def upsert_playlist_activity(conn: Connection, rows: list[dict[str, Any]]) -> int:
    loaded = 0
    with conn.cursor() as cur:
        for row in rows:
            customer_key = customer_key_as_of(conn, int(row["customer_id"]), row["added_at"])
            prod_key = product_key(conn, row["product_nk"])
            date_key = ensure_date(conn, row["added_at"])
            cur.execute(
                """
                INSERT INTO warehouse.fact_playlist_activity (
                    playlist_id, track_id, customer_key, product_key, added_date_key,
                    track_position, added_at, source_updated_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (playlist_id, track_id) DO UPDATE SET
                    customer_key=EXCLUDED.customer_key,
                    product_key=EXCLUDED.product_key,
                    added_date_key=EXCLUDED.added_date_key,
                    track_position=EXCLUDED.track_position,
                    added_at=EXCLUDED.added_at,
                    source_updated_at=EXCLUDED.source_updated_at,
                    loaded_at=NOW()
                """,
                (
                    row["playlist_id"], row["track_id"], customer_key, prod_key, date_key,
                    row["track_position"], row["added_at"], row["source_updated_at"],
                ),
            )
            loaded += 1
    return loaded
