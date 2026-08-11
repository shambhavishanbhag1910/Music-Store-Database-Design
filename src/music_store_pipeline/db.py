from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg import Connection
from psycopg.rows import dict_row

from .config import DatabaseConfig


@contextmanager
def connect(config: DatabaseConfig) -> Iterator[Connection]:
    conn = psycopg.connect(config.dsn, row_factory=dict_row, autocommit=False)
    try:
        yield conn
    finally:
        conn.close()


def ping(config: DatabaseConfig) -> None:
    with connect(config) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 AS ok")
            row = cur.fetchone()
            if not row or row["ok"] != 1:
                raise RuntimeError("Database health check failed")
