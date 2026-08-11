from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from psycopg import Connection


@dataclass(frozen=True)
class QualityCheck:
    name: str
    severity: str
    sql: str
    details: str


CHECKS = [
    QualityCheck(
        "single_current_customer_version",
        "error",
        """
        SELECT COUNT(*) AS failed_rows
        FROM (
            SELECT customer_id
            FROM warehouse.dim_customer
            WHERE is_current
            GROUP BY customer_id
            HAVING COUNT(*) <> 1
        ) x
        """,
        "Each customer must have exactly one current SCD2 dimension row.",
    ),
    QualityCheck(
        "sales_non_negative",
        "error",
        """
        SELECT COUNT(*) AS failed_rows
        FROM warehouse.fact_sales
        WHERE gross_amount < 0
           OR allocated_discount < 0
           OR allocated_tax < 0
        """,
        "Sales monetary components cannot be negative.",
    ),
    QualityCheck(
        "sales_net_formula",
        "error",
        """
        SELECT COUNT(*) AS failed_rows
        FROM warehouse.fact_sales
        WHERE ABS(
            net_amount
            - (
                gross_amount
                + allocated_tax
                - allocated_discount
            )
        ) > 0.01
        """,
        "Line net amount must reconcile to gross + tax - discount within one cent.",
    ),
    QualityCheck(
        "fact_sales_dimension_integrity",
        "error",
        """
        SELECT COUNT(*) AS failed_rows
        FROM warehouse.fact_sales f
        LEFT JOIN warehouse.dim_customer c
            ON c.customer_key = f.customer_key
        LEFT JOIN warehouse.dim_product p
            ON p.product_key = f.product_key
        LEFT JOIN warehouse.dim_date d
            ON d.date_key = f.order_date_key
        WHERE c.customer_key IS NULL
           OR p.product_key IS NULL
           OR d.date_key IS NULL
        """,
        "Fact sales rows must resolve to all required dimensions.",
    ),
    QualityCheck(
        "payment_positive_amount",
        "error",
        """
        SELECT COUNT(*) AS failed_rows
        FROM warehouse.fact_payment
        WHERE amount <= 0
        """,
        "Payment amount must be positive.",
    ),
]


def run_quality_checks(
    conn: Connection,
) -> list[dict[str, Any]]:
    """
    Execute data-quality checks without persisting the results.

    Persistence is intentionally separated from execution so failed
    DQ evidence can survive a rollback of the warehouse load.
    """

    results: list[dict[str, Any]] = []

    with conn.cursor() as cur:
        for check in CHECKS:
            cur.execute(check.sql)

            row = cur.fetchone()
            failed_rows = int(row["failed_rows"])
            passed = failed_rows == 0

            results.append(
                {
                    "name": check.name,
                    "severity": check.severity,
                    "passed": passed,
                    "failed_rows": failed_rows,
                    "details": check.details,
                }
            )

    return results


def persist_quality_results(
    conn: Connection,
    run_id: str,
    results: list[dict[str, Any]],
) -> None:
    """
    Persist DQ evidence.

    This can be called either inside the successful warehouse
    transaction or after a rollback for a failed ETL run.
    """

    if not results:
        return

    with conn.cursor() as cur:
        for result in results:
            cur.execute(
                """
                INSERT INTO audit.dq_result(
                    run_id,
                    check_name,
                    severity,
                    passed,
                    failed_rows,
                    details
                )
                VALUES (
                    %s::uuid,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    run_id,
                    result["name"],
                    result["severity"],
                    result["passed"],
                    result["failed_rows"],
                    result["details"],
                ),
            )


def assert_no_error_failures(
    results: list[dict[str, Any]],
) -> None:
    failures = [
        result
        for result in results
        if result["severity"] == "error"
        and not result["passed"]
    ]

    if failures:
        names = ", ".join(
            failure["name"]
            for failure in failures
        )

        raise RuntimeError(
            f"Data quality gate failed: {names}"
        )