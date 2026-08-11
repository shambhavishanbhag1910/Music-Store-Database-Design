from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

from music_store_pipeline.config import load_settings
from music_store_pipeline.db import connect

CENT = Decimal("0.01")

FIRST_NAMES = ["Aarav", "Aditi", "Arjun", "Emma", "Liam", "Maya", "Noah", "Olivia", "Riya", "Sophia", "Vihaan", "Zoe"]
LAST_NAMES = ["Brown", "Davis", "Garcia", "Gupta", "Johnson", "Khan", "Lee", "Patel", "Shah", "Singh", "Smith", "Wilson"]
CITIES = ["Chicago", "Mumbai", "Pune", "Dallas", "Toronto", "London", "Seattle", "Bengaluru", "Austin", "New York"]
COUNTRIES = ["USA", "India", "Canada", "UK"]
ADJECTIVES = ["Electric", "Golden", "Midnight", "Neon", "Silent", "Velvet", "Wild", "Crimson", "Urban", "Cosmic"]
NOUNS = ["Echo", "Pulse", "River", "Signal", "Dreams", "Sky", "Waves", "Road", "Lights", "Theory"]


def money(value: Decimal | float | int) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--customers", type=int, default=500)
    parser.add_argument("--artists", type=int, default=80)
    parser.add_argument("--albums", type=int, default=160)
    parser.add_argument("--tracks", type=int, default=1800)
    parser.add_argument("--orders", type=int, default=4000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    random.seed(args.seed)
    settings = load_settings()

    with connect(settings.oltp) as conn:
        with conn.cursor() as cur:
            if args.reset:
                cur.execute(
                    """
                    TRUNCATE payment, order_item, orders, playlist_track, playlist,
                             track_artist, track_genre, track, album_artist, album,
                             artist, customer RESTART IDENTITY CASCADE
                    """
                )

            cur.execute("SELECT genre_id FROM genre ORDER BY genre_id")
            genre_ids = [r["genre_id"] for r in cur.fetchall()]
            cur.execute("SELECT media_type_id FROM media_type ORDER BY media_type_id")
            media_ids = [r["media_type_id"] for r in cur.fetchall()]
            if not genre_ids or not media_ids:
                raise RuntimeError("Reference seed data is missing. Recreate the OLTP database.")

            artist_ids: list[int] = []
            for i in range(args.artists):
                name = f"{random.choice(ADJECTIVES)} {random.choice(NOUNS)} {i+1}"
                cur.execute(
                    """
                    INSERT INTO artist(artist_name, biography, website_url, debut_year, country)
                    VALUES (%s,%s,%s,%s,%s) RETURNING artist_id
                    """,
                    (
                        name,
                        f"Synthetic portfolio artist {i+1}",
                        f"https://example.com/artists/{i+1}",
                        random.randint(1980, 2025),
                        random.choice(COUNTRIES),
                    ),
                )
                artist_ids.append(cur.fetchone()["artist_id"])

            album_ids: list[int] = []
            album_artist_map: dict[int, int] = {}
            album_release: dict[int, datetime] = {}
            for i in range(args.albums):
                release = datetime.now(timezone.utc) - timedelta(days=random.randint(30, 3650))
                album_type = random.choices(
                    ["album", "ep", "single", "compilation"], weights=[65, 15, 15, 5]
                )[0]
                price = money(random.uniform(5.99, 18.99))
                cur.execute(
                    """
                    INSERT INTO album(album_title, release_date, album_type, album_price)
                    VALUES (%s,%s,%s,%s) RETURNING album_id
                    """,
                    (
                        f"{random.choice(ADJECTIVES)} {random.choice(NOUNS)} Vol. {i+1}",
                        release.date(), album_type, price,
                    ),
                )
                album_id = cur.fetchone()["album_id"]
                album_ids.append(album_id)
                album_release[album_id] = release
                artist_id = random.choice(artist_ids)
                album_artist_map[album_id] = artist_id
                cur.execute(
                    "INSERT INTO album_artist(album_id, artist_id, artist_role) VALUES (%s,%s,'primary')",
                    (album_id, artist_id),
                )

            track_ids: list[int] = []
            track_prices: dict[int, Decimal] = {}
            track_number_by_album = {album_id: 0 for album_id in album_ids}
            for i in range(args.tracks):
                album_id = album_ids[i % len(album_ids)]
                track_number_by_album[album_id] += 1
                price = money(random.choice([0.79, 0.99, 1.09, 1.29, 1.49, 1.99]))
                cur.execute(
                    """
                    INSERT INTO track(
                        album_id, media_type_id, track_name, duration_ms, unit_price,
                        is_explicit, track_number, disc_number, release_date
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,1,%s)
                    RETURNING track_id
                    """,
                    (
                        album_id, random.choice(media_ids),
                        f"Track {i+1} - {random.choice(ADJECTIVES)} {random.choice(NOUNS)}",
                        random.randint(120000, 420000), price, random.random() < 0.12,
                        track_number_by_album[album_id], album_release[album_id].date(),
                    ),
                )
                track_id = cur.fetchone()["track_id"]
                track_ids.append(track_id)
                track_prices[track_id] = price
                primary_artist = album_artist_map[album_id]
                cur.execute(
                    "INSERT INTO track_artist(track_id, artist_id, artist_role) VALUES (%s,%s,'primary')",
                    (track_id, primary_artist),
                )
                if random.random() < 0.2:
                    featured = random.choice(artist_ids)
                    if featured != primary_artist:
                        cur.execute(
                            "INSERT INTO track_artist(track_id, artist_id, artist_role) VALUES (%s,%s,'featured') ON CONFLICT DO NOTHING",
                            (track_id, featured),
                        )
                cur.execute(
                    "INSERT INTO track_genre(track_id, genre_id) VALUES (%s,%s)",
                    (track_id, random.choice(genre_ids)),
                )

            customer_ids: list[int] = []
            for i in range(args.customers):
                first = random.choice(FIRST_NAMES)
                last = random.choice(LAST_NAMES)
                email = f"{first.lower()}.{last.lower()}.{i+1}@example.com"
                registration = (datetime.now(timezone.utc) - timedelta(days=random.randint(30, 900))).date()
                cur.execute(
                    """
                    INSERT INTO customer(first_name,last_name,email,phone_no,city,country,registration_date,status)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING customer_id
                    """,
                    (
                        first, last, email, f"+1-555-{i+1000:04d}", random.choice(CITIES),
                        random.choice(COUNTRIES), registration,
                        random.choices(["active", "inactive", "blocked"], weights=[92, 7, 1])[0],
                    ),
                )
                customer_ids.append(cur.fetchone()["customer_id"])

            playlist_count = max(20, min(args.customers, args.customers // 2))
            for i in range(playlist_count):
                customer_id = random.choice(customer_ids)
                cur.execute(
                    """
                    INSERT INTO playlist(customer_id, playlist_name, playlist_visibility, description)
                    VALUES (%s,%s,%s,%s) RETURNING playlist_id
                    """,
                    (
                        customer_id, f"Playlist {i+1}",
                        random.choice(["private", "public", "unlisted"]),
                        "Synthetic playlist for analytics",
                    ),
                )
                playlist_id = cur.fetchone()["playlist_id"]
                selected_tracks = random.sample(track_ids, k=min(random.randint(5, 20), len(track_ids)))
                for position, track_id in enumerate(selected_tracks, start=1):
                    added_at = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 365))
                    cur.execute(
                        """
                        INSERT INTO playlist_track(playlist_id,track_id,track_position,added_at)
                        VALUES (%s,%s,%s,%s)
                        """,
                        (playlist_id, track_id, position, added_at),
                    )

            cur.execute("SELECT album_id, album_price FROM album")
            album_prices = {r["album_id"]: r["album_price"] for r in cur.fetchall()}

            now = datetime.now(timezone.utc)
            for order_index in range(args.orders):
                customer_id = random.choice(customer_ids)
                order_date = now - timedelta(
                    days=random.randint(0, 365),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59),
                )
                status = random.choices(
                    ["completed", "confirmed", "pending", "cancelled", "refunded"],
                    weights=[80, 5, 4, 7, 4],
                )[0]
                items = []
                for _ in range(random.randint(1, 4)):
                    if random.random() < 0.88:
                        track_id = random.choice(track_ids)
                        items.append((track_id, None, track_prices[track_id], random.choice([1, 1, 1, 2])))
                    else:
                        album_id = random.choice(album_ids)
                        items.append((None, album_id, album_prices[album_id], 1))

                subtotal = money(sum((price * qty for _, _, price, qty in items), Decimal("0")))
                discount_pct = Decimal(str(random.choices([0, 0.05, 0.10], weights=[75, 18, 7])[0]))
                discount = money(subtotal * discount_pct)
                tax = money((subtotal - discount) * Decimal("0.08"))
                total = money(subtotal + tax - discount)

                cur.execute(
                    """
                    INSERT INTO orders(
                        customer_id, order_date, order_status, subtotal, tax_amount,
                        discount_amount, total_amount, currency, created_at, updated_at
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,'USD',%s,%s)
                    RETURNING order_id
                    """,
                    (customer_id, order_date, status, subtotal, tax, discount, total, order_date, order_date),
                )
                order_id = cur.fetchone()["order_id"]
                for track_id, album_id, price, qty in items:
                    cur.execute(
                        """
                        INSERT INTO order_item(order_id,track_id,album_id,unit_price,quantity,created_at,updated_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (order_id, track_id, album_id, price, qty, order_date, order_date),
                    )

                payment_date = order_date + timedelta(minutes=random.randint(1, 60))
                if status == "completed":
                    payment_status = random.choices(["successful", "failed"], weights=[96, 4])[0]
                elif status == "refunded":
                    payment_status = "refunded"
                elif status == "cancelled":
                    payment_status = random.choice(["failed", "refunded"])
                else:
                    payment_status = "pending"

                cur.execute(
                    """
                    INSERT INTO payment(
                        order_id,payment_date,amount,payment_status,payment_mode,
                        transaction_reference,created_at,updated_at
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        order_id, payment_date, total, payment_status,
                        random.choice(["card", "upi", "net_banking", "wallet", "paypal"]),
                        f"TXN-{args.seed}-{order_index+1:08d}", payment_date, payment_date,
                    ),
                )

        conn.commit()

    print(
        f"Generated {args.customers} customers, {args.artists} artists, {args.albums} albums, "
        f"{args.tracks} tracks and {args.orders} orders."
    )


if __name__ == "__main__":
    main()
