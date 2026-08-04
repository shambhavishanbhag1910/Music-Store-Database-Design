INSERT INTO customer (
    first_name,
    last_name,
    email
)
VALUES (
    'Test',
    'Customer',
    'existing@example.com'
);

INSERT INTO track (
    album_id,
    media_type_id,
    track_name,
    duration_ms,
    unit_price,
    track_number
)
VALUES (
    1,
    1,
    'Invalid Track',
    200000,
    -1.00,
    1
);

INSERT INTO orders (
    customer_id,
    subtotal,
    tax_amount,
    discount_amount,
    total_amount
)
VALUES (
    1,
    10.00,
    1.00,
    0.00,
    15.00
);

INSERT INTO order_item (
    order_id,
    track_id,
    album_id,
    unit_price,
    quantity
)
VALUES (
    1,
    1,
    1,
    1.29,
    1
);