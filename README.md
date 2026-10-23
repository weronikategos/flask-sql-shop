# Flask SQL Shop

![tests](https://github.com/weronikategos/flask-sql-shop/actions/workflows/tests.yml/badge.svg)

An online coffee and tea shop built with **Flask**, a hand-designed **SQLite** database and plain SQL (no ORM).

## Features
- product catalog with category filters
- sign-up and login (passwords are hashed, never stored in plain text)
- session-based shopping cart
- checkout in **a single transaction**: stock goes down only if the whole order is saved
- order history (customers can see only their own orders)
- sales report: revenue by category, best-selling products, average order value
- **JSON REST API** for the catalog
- demo data generator: 40 customers and 400 orders spread over 2026 (`flask --app shop demo-data`)

## Database schema
```
categories (category_id PK, name)
products   (product_id PK, category_id FK, name, description, price, stock)
customers  (customer_id PK, name, email UNIQUE, password_hash, created_at)
orders     (order_id PK, customer_id FK, total, created_at)
order_items(order_id FK, product_id FK, quantity, unit_price)  PK (order_id, product_id)
```
The full definition with constraints (CHECK, FOREIGN KEY) and indexes is in [`shop/schema.sql`](shop/schema.sql), and the report queries are in [`shop/routes.py`](shop/routes.py).

## API
| Endpoint | Returns |
|---|---|
| `GET /api/health` | `{"status": "ok"}` |
| `GET /api/categories` | all categories |
| `GET /api/products` | all products; `?category=<id>` filters by category (400 if it's not a number) |
| `GET /api/products/<id>` | one product, or `{"error": "Not found"}` with 404 |

## Tech stack
Python, Flask, SQLite, SQL (JOIN, GROUP BY, aggregates, transactions), Jinja2, REST API, pytest, Docker, GitHub Actions

## How to run
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
flask --app shop init-db     # creates the database with sample products
flask --app shop demo-data   # optional: sample customers and orders for the report
flask --app shop run         # open http://127.0.0.1:5000
python -m pytest             # 15 tests: catalog, login, checkout, stock, report, API
```
Demo login (after `demo-data`): `anna1@example.com` / `demo-pass-123`

## Docker
```bash
docker compose up -d --build   # shop at http://localhost:8000, with demo data
docker compose down            # stop it (the data stays in the shop-data volume)
```
The image runs the app with `gunicorn`. On the first start it creates the database and demo data ([`docker-entrypoint.sh`](docker-entrypoint.sh)).

## CI
On every push GitHub Actions ([`.github/workflows/tests.yml`](.github/workflows/tests.yml)) runs the tests, builds the Docker image and checks that the running container responds.

## What I would add next
- Stripe test payments
- an admin panel for managing products
- a PostgreSQL version
