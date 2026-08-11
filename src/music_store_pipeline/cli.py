from __future__ import annotations

import argparse

from .config import load_settings
from .db import ping
from .logging_utils import configure_logging
from .pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Music Store Data Platform ETL")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run", help="Run one idempotent ETL cycle")
    sub.add_parser("health", help="Check OLTP and warehouse connectivity")
    args = parser.parse_args()

    settings = load_settings()
    configure_logging(settings.log_level)

    if args.command == "health":
        ping(settings.oltp)
        ping(settings.warehouse)
        print("OLTP and warehouse connections are healthy")
        return

    run_id = run_pipeline(settings)
    print(f"Pipeline completed: {run_id}")


if __name__ == "__main__":
    main()
