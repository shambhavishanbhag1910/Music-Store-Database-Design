from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    dbname: str
    user: str
    password: str

    @property
    def dsn(self) -> str:
        return (
            f"host={self.host} port={self.port} dbname={self.dbname} "
            f"user={self.user} password={self.password}"
        )


@dataclass(frozen=True)
class Settings:
    oltp: DatabaseConfig
    warehouse: DatabaseConfig
    pipeline_name: str
    overlap_minutes: int
    log_level: str


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Required environment variable {name} is not set")
    return value


def load_settings() -> Settings:
    return Settings(
        oltp=DatabaseConfig(
            host=os.getenv("OLTP_HOST", "localhost"),
            port=int(os.getenv("OLTP_PORT", "5432")),
            dbname=os.getenv("OLTP_DB", "music_store"),
            user=_required("OLTP_USER"),
            password=_required("OLTP_PASSWORD"),
        ),
        warehouse=DatabaseConfig(
            host=os.getenv("WAREHOUSE_HOST", "localhost"),
            port=int(os.getenv("WAREHOUSE_PORT", "5433")),
            dbname=os.getenv("WAREHOUSE_DB", "music_warehouse"),
            user=_required("WAREHOUSE_USER"),
            password=_required("WAREHOUSE_PASSWORD"),
        ),
        pipeline_name=os.getenv("PIPELINE_NAME", "music_store_hourly"),
        overlap_minutes=int(os.getenv("EXTRACT_OVERLAP_MINUTES", "5")),
        log_level=os.getenv("PIPELINE_LOG_LEVEL", "INFO"),
    )
