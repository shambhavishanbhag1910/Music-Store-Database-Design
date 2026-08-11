from decimal import Decimal

from music_store_pipeline.transform import allocate_order_rows


def test_allocation_reconciles_exact_order_total():
    rows = [
        {
            "order_id": 1,
            "order_item_id": 1,
            "gross_amount": Decimal("1.00"),
            "subtotal": Decimal("3.00"),
            "tax_amount": Decimal("0.24"),
            "discount_amount": Decimal("0.30"),
            "total_amount": Decimal("2.94"),
        },
        {
            "order_id": 1,
            "order_item_id": 2,
            "gross_amount": Decimal("2.00"),
            "subtotal": Decimal("3.00"),
            "tax_amount": Decimal("0.24"),
            "discount_amount": Decimal("0.30"),
            "total_amount": Decimal("2.94"),
        },
    ]
    result = allocate_order_rows(rows)
    assert sum(r["allocated_tax"] for r in result) == Decimal("0.24")
    assert sum(r["allocated_discount"] for r in result) == Decimal("0.30")
    assert sum(r["net_amount"] for r in result) == Decimal("2.94")


def test_single_line_receives_entire_order_total():
    rows = [
        {
            "order_id": 1,
            "order_item_id": 1,
            "gross_amount": Decimal("10.00"),
            "subtotal": Decimal("10.00"),
            "tax_amount": Decimal("0.72"),
            "discount_amount": Decimal("1.00"),
            "total_amount": Decimal("9.72"),
        }
    ]
    result = allocate_order_rows(rows)
    assert result[0]["net_amount"] == Decimal("9.72")
    assert result[0]["allocated_tax"] == Decimal("0.72")
    assert result[0]["allocated_discount"] == Decimal("1.00")
