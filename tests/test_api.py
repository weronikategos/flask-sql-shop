from shop.db import get_db
from shop.demo_data import generate


def test_health(client):
    assert client.get("/api/health").get_json() == {"status": "ok"}


def test_products_list(client):
    products = client.get("/api/products").get_json()
    assert len(products) == 11
    assert {"product_id", "name", "price", "stock", "category"} <= products[0].keys()


def test_products_filtered_by_category(client):
    products = client.get("/api/products?category=2").get_json()
    assert products and all(p["category"] == "Tea" for p in products)


def test_products_bad_category(client):
    assert client.get("/api/products?category=abc").status_code == 400


def test_product_not_found(client):
    response = client.get("/api/products/999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Not found"}


def test_demo_data_totals_match_items(app):
    with app.app_context():
        generate(customers=3, orders=20)
        db = get_db()
        assert db.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 20
        mismatched = db.execute(
            """SELECT COUNT(*) FROM orders o
               WHERE ABS(o.total - (SELECT SUM(quantity * unit_price) FROM order_items oi
                                    WHERE oi.order_id = o.order_id)) > 0.01"""
        ).fetchone()[0]
        assert mismatched == 0
