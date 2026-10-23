"""Generates sample customers and orders so the sales report has realistic data to show."""
import random
from datetime import datetime, timedelta

import click
from werkzeug.security import generate_password_hash

from .db import get_db

DEMO_PASSWORD = "demo-pass-123"
FIRST_NAMES = ["Anna", "Piotr", "Kasia", "Tomek", "Ola", "Marek", "Ewa", "Kuba", "Zosia", "Adam",
               "Magda", "Pawel", "Julia", "Bartek", "Natalia"]


def generate(customers=40, orders=400, seed=42):
    rng = random.Random(seed)  # fixed seed, so every run creates the same data
    db = get_db()
    products = db.execute("SELECT product_id, price FROM products").fetchall()
    password = generate_password_hash(DEMO_PASSWORD)
    start = datetime(2026, 1, 1)

    signups = []  # (customer_id, day the account was created)
    for i in range(customers):
        name = FIRST_NAMES[i % len(FIRST_NAMES)]
        signup_day = rng.randint(0, 200)
        customer_id = db.execute(
            "INSERT INTO customers (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (name, f"{name.lower()}{i + 1}@example.com", password,
             (start + timedelta(days=signup_day)).strftime("%Y-%m-%d %H:%M:%S")),
        ).lastrowid
        signups.append((customer_id, signup_day))

    for _ in range(orders):
        customer_id, signup_day = rng.choice(signups)
        # Triangular distribution: more orders towards the end of the period, so the shop "grows".
        # A customer can only order after signing up.
        day = max(signup_day, int(rng.triangular(0, 272, 272)))
        created = start + timedelta(days=day, hours=rng.randint(8, 21), minutes=rng.randint(0, 59))
        items = [(p["product_id"], rng.randint(1, 3), p["price"])
                 for p in rng.sample(products, rng.randint(1, 3))]
        total = round(sum(quantity * price for _, quantity, price in items), 2)
        order_id = db.execute(
            "INSERT INTO orders (customer_id, total, created_at) VALUES (?, ?, ?)",
            (customer_id, total, created.strftime("%Y-%m-%d %H:%M:%S")),
        ).lastrowid
        db.executemany(
            "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
            [(order_id, product_id, quantity, price) for product_id, quantity, price in items],
        )
    db.commit()


@click.command("demo-data")
@click.option("--orders", default=400, help="How many orders to generate.")
def demo_data_command(orders):
    """Adds sample customers and orders (run it after init-db)."""
    generate(orders=orders)
    click.echo(f"Added {orders} sample orders. Demo login: anna1@example.com / {DEMO_PASSWORD}")
