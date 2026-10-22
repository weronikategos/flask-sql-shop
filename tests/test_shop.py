from shop.db import get_db


def stock(app, product_id):
    with app.app_context():
        return get_db().execute("SELECT stock FROM products WHERE product_id = ?", (product_id,)).fetchone()[0]


def test_catalog_lists_products(client):
    page = client.get("/").get_data(as_text=True)
    assert "Brazil whole bean coffee" in page
    assert "Hand coffee grinder" in page


def test_catalog_filters_by_category(client):
    page = client.get("/?category=2").get_data(as_text=True)
    assert "Sencha green tea" in page
    assert "Hand coffee grinder" not in page


def test_register_rejects_duplicate_email(client):
    data = {"name": "Ala", "email": "ala@example.com", "password": "secretpass"}
    client.post("/register", data=data)
    page = client.post("/register", data=data, follow_redirects=True).get_data(as_text=True)
    assert "already exists" in page


def test_wrong_password(client):
    client.post("/register", data={"name": "Ala", "email": "ala@example.com", "password": "secretpass"})
    page = client.post("/login", data={"email": "ala@example.com", "password": "wrong"}).get_data(as_text=True)
    assert "Invalid email or password" in page


def test_checkout_requires_login(client):
    client.post("/cart/add/1", data={"quantity": 1})
    response = client.post("/checkout")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_full_order_flow_updates_stock_and_report(app, logged_in):
    logged_in.post("/cart/add/1", data={"quantity": 2})
    logged_in.post("/cart/add/6", data={"quantity": 1})
    response = logged_in.post("/checkout", follow_redirects=True)
    page = response.get_data(as_text=True)
    assert "Order #1" in page
    assert "168.98" in page  # 2 x 39.99 + 89.00
    assert stock(app, 1) == 23
    assert stock(app, 6) == 9

    report = logged_in.get("/report").get_data(as_text=True)
    assert "Coffee" in report and "79.98" in report


def test_cannot_add_more_than_stock(app, client):
    page = client.post("/cart/add/7", data={"quantity": 99}, follow_redirects=True).get_data(as_text=True)
    assert "have that many in stock" in page


def test_other_customers_order_is_hidden(app, logged_in):
    logged_in.post("/cart/add/1", data={"quantity": 1})
    logged_in.post("/checkout")
    logged_in.get("/logout")
    logged_in.post("/register", data={"name": "Ola", "email": "ola@example.com", "password": "otherpass1"})
    logged_in.post("/login", data={"email": "ola@example.com", "password": "otherpass1"})
    assert logged_in.get("/orders/1").status_code == 404
