from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

CENT = Decimal("0.01")


def money(value: Decimal | int | float | str) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def allocate_order_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Allocate order-level tax and discount to line items, preserving exact order totals.

    Rows may contain multiple orders. The final line in each order absorbs any rounding remainder.
    """
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[int(row["order_id"])].append(dict(row))

    output: list[dict[str, Any]] = []
    for _, order_rows in grouped.items():
        subtotal = money(order_rows[0]["subtotal"])
        tax = money(order_rows[0]["tax_amount"])
        discount = money(order_rows[0]["discount_amount"])
        total = money(order_rows[0]["total_amount"])

        allocated_tax = Decimal("0.00")
        allocated_discount = Decimal("0.00")
        allocated_net = Decimal("0.00")

        for index, row in enumerate(order_rows):
            gross = money(row["gross_amount"])
            is_last = index == len(order_rows) - 1
            if is_last:
                line_tax = tax - allocated_tax
                line_discount = discount - allocated_discount
                line_net = total - allocated_net
            else:
                ratio = (gross / subtotal) if subtotal > 0 else Decimal("0")
                line_tax = money(tax * ratio)
                line_discount = money(discount * ratio)
                line_net = money(gross + line_tax - line_discount)
                allocated_tax += line_tax
                allocated_discount += line_discount
                allocated_net += line_net

            row["gross_amount"] = gross
            row["allocated_tax"] = money(line_tax)
            row["allocated_discount"] = money(line_discount)
            row["net_amount"] = money(line_net)
            output.append(row)

    return output
