import functools
import sqlite3

from flask import Blueprint, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp = Blueprint("shop", __name__)


@bp.before_app_request
def load_customer():
    customer_id = session.get("customer_id")
    g.customer = None
    if customer_id is not None:
        g.customer = get_db().execute(
            "SELECT customer_id, name, email FROM customers WHERE customer_id = ?", (customer_id,)
        ).fetchone()


def login_required(view):
    @functools.wraps(view)
    def wrapped(**kwargs):
        if g.customer is None:
            flash("Please log in to continue.")
            return redirect(url_for("shop.login", next=request.path))
        return view(**kwargs)
    return wrapped


# ---------- Catalog ----------

@bp.route("/")
def catalog():
    category = request.args.get("category", type=int)
    db = get_db()
    categories = db.execute("SELECT category_id, name FROM categories ORDER BY name").fetchall()
    sql = """SELECT p.product_id, p.name, p.description, p.price, p.stock, c.name AS category
             FROM products p JOIN categories c ON c.category_id = p.category_id"""
    params = ()
    if category:
        sql += " WHERE p.category_id = ?"
        params = (category,)
    products = db.execute(sql + " ORDER BY c.name, p.name", params).fetchall()
    return render_template("catalog.html", products=products, categories=categories, active=category)


# ---------- Account ----------

@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or "@" not in email or len(password) < 8:
            flash("Enter your name, a valid email and a password (at least 8 characters).")
        else:
            try:
                db = get_db()
                db.execute(
                    "INSERT INTO customers (name, email, password_hash) VALUES (?, ?, ?)",
                    (name, email, generate_password_hash(password)),
                )
                db.commit()
            except sqlite3.IntegrityError:
                flash("An account with this email already exists.")
            else:
                flash("Account created. You can log in now.")
                return redirect(url_for("shop.login"))
    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        customer = get_db().execute(
            "SELECT customer_id, password_hash FROM customers WHERE email = ?", (email,)
        ).fetchone()
        if customer and check_password_hash(customer["password_hash"], request.form.get("password", "")):
            cart = session.get("cart", {})
            session.clear()
            session["customer_id"] = customer["customer_id"]
            session["cart"] = cart
            next_url = request.args.get("next", "")
            return redirect(next_url if next_url.startswith("/") and not next_url.startswith("//") else url_for("shop.catalog"))
        flash("Invalid email or password.")
    return render_template("login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("shop.catalog"))


# ---------- Cart ----------

def cart_items():
    """Returns the products in the cart (stored in the session) with current prices from the database."""
    cart = session.get("cart", {})
    if not cart:
        return [], 0.0
    placeholders = ",".join("?" * len(cart))
    rows = get_db().execute(
        f"SELECT product_id, name, price, stock FROM products WHERE product_id IN ({placeholders})",
        [int(pid) for pid in cart],
    ).fetchall()
    items = [{**dict(r), "quantity": cart[str(r["product_id"])],
              "subtotal": round(r["price"] * cart[str(r["product_id"])], 2)} for r in rows]
    return items, round(sum(i["subtotal"] for i in items), 2)


@bp.post("/cart/add/<int:product_id>")
def add_to_cart(product_id):
    product = get_db().execute("SELECT stock FROM products WHERE product_id = ?", (product_id,)).fetchone()
    if product is None:
        abort(404)
    quantity = max(1, request.form.get("quantity", 1, type=int))
    cart = session.get("cart", {})
    new_quantity = cart.get(str(product_id), 0) + quantity
    if new_quantity > product["stock"]:
        flash("We don't have that many in stock.")
    else:
        cart[str(product_id)] = new_quantity
        session["cart"] = cart
        flash("Added to cart.")
    return redirect(url_for("shop.catalog"))


@bp.post("/cart/remove/<int:product_id>")
def remove_from_cart(product_id):
    cart = session.get("cart", {})
    cart.pop(str(product_id), None)
    session["cart"] = cart
    return redirect(url_for("shop.cart"))


@bp.route("/cart")
def cart():
    items, total = cart_items()
    return render_template("cart.html", items=items, total=total)


# ---------- Orders ----------

@bp.post("/checkout")
@login_required
def checkout():
    items, total = cart_items()
    if not items:
        flash("Your cart is empty.")
        return redirect(url_for("shop.cart"))
    db = get_db()
    try:
        with db:  # one transaction: either the whole order is saved or nothing is
            for item in items:
                updated = db.execute(
                    "UPDATE products SET stock = stock - ? WHERE product_id = ? AND stock >= ?",
                    (item["quantity"], item["product_id"], item["quantity"]),
                )
                if updated.rowcount == 0:
                    raise ValueError(item["name"])
            order_id = db.execute(
                "INSERT INTO orders (customer_id, total) VALUES (?, ?)", (g.customer["customer_id"], total)
            ).lastrowid
            db.executemany(
                "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                [(order_id, i["product_id"], i["quantity"], i["price"]) for i in items],
            )
    except ValueError as exc:
        flash(f"\"{exc}\" has just sold out. Please update your cart.")
        return redirect(url_for("shop.cart"))
    session["cart"] = {}
    return redirect(url_for("shop.order_detail", order_id=order_id))


@bp.route("/orders")
@login_required
def orders():
    rows = get_db().execute(
        """SELECT o.order_id, o.created_at, o.total, SUM(oi.quantity) AS items
           FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
           WHERE o.customer_id = ?
           GROUP BY o.order_id ORDER BY o.order_id DESC""",
        (g.customer["customer_id"],),
    ).fetchall()
    return render_template("orders.html", orders=rows)


@bp.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    db = get_db()
    order = db.execute(
        "SELECT order_id, created_at, total FROM orders WHERE order_id = ? AND customer_id = ?",
        (order_id, g.customer["customer_id"]),
    ).fetchone()
    if order is None:
        abort(404)
    items = db.execute(
        """SELECT p.name, oi.quantity, oi.unit_price, ROUND(oi.quantity * oi.unit_price, 2) AS subtotal
           FROM order_items oi JOIN products p ON p.product_id = oi.product_id
           WHERE oi.order_id = ?""",
        (order_id,),
    ).fetchall()
    return render_template("order_detail.html", order=order, items=items)


# ---------- Sales report ----------

@bp.route("/report")
@login_required
def report():
    db = get_db()
    by_category = db.execute(
        """SELECT c.name AS category, COALESCE(SUM(oi.quantity), 0) AS units,
                  ROUND(COALESCE(SUM(oi.quantity * oi.unit_price), 0), 2) AS revenue
           FROM categories c
           LEFT JOIN products p ON p.category_id = c.category_id
           LEFT JOIN order_items oi ON oi.product_id = p.product_id
           GROUP BY c.category_id ORDER BY revenue DESC"""
    ).fetchall()
    top_products = db.execute(
        """SELECT p.name, SUM(oi.quantity) AS units
           FROM order_items oi JOIN products p ON p.product_id = oi.product_id
           GROUP BY p.product_id ORDER BY units DESC LIMIT 5"""
    ).fetchall()
    summary = db.execute(
        "SELECT COUNT(*) AS orders, ROUND(COALESCE(SUM(total), 0), 2) AS revenue, "
        "ROUND(COALESCE(AVG(total), 0), 2) AS avg_order FROM orders"
    ).fetchone()
    return render_template("report.html", by_category=by_category, top_products=top_products, summary=summary)
