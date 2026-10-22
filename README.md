# Flask SQL Shop

An online coffee and tea shop built with **Flask**, a hand-designed **SQLite** database and plain SQL (no ORM).

## Features
- product catalog with category filters
- sign-up and login (passwords are hashed, never stored in plain text)
- session-based shopping cart
- checkout in **a single transaction**: stock goes down only if the whole order is saved
- order history (customers can see only their own orders)
- sales report: revenue by category, best-selling products, average order value

## Database schema
```
categories (category_id PK, name)
products   (product_id PK, category_id FK, name, description, price, stock)
customers  (customer_id PK, name, email UNIQUE, password_hash, created_at)
orders     (order_id PK, customer_id FK, total, created_at)
order_items(order_id FK, product_id FK, quantity, unit_price)  PK (order_id, product_id)
```
The full definition with constraints (CHECK, FOREIGN KEY) and indexes is in [`shop/schema.sql`](shop/schema.sql), and the report queries are in [`shop/routes.py`](shop/routes.py).

## Tech stack
Python, Flask, SQLite, SQL (JOIN, GROUP BY, aggregates, transactions), Jinja2, pytest

## How to run
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
flask --app shop init-db     # creates the database with sample products
flask --app shop run         # open http://127.0.0.1:5000
python -m pytest             # 9 tests: catalog, login, checkout, stock, report
```

## What I would add next
- Stripe test payments
- an admin panel for managing products
- a PostgreSQL version and cloud deployment
