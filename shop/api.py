"""JSON API for the shop's catalog."""
from flask import Blueprint, abort, jsonify, request

from .db import get_db

bp = Blueprint("api", __name__, url_prefix="/api")

PRODUCT_SQL = """SELECT p.product_id, p.name, p.description, p.price, p.stock,
                        c.category_id, c.name AS category
                 FROM products p JOIN categories c ON c.category_id = p.category_id"""


@bp.get("/health")
def health():
    get_db().execute("SELECT 1")
    return jsonify(status="ok")


@bp.get("/categories")
def categories():
    rows = get_db().execute("SELECT category_id, name FROM categories ORDER BY name").fetchall()
    return jsonify([dict(r) for r in rows])


@bp.get("/products")
def products():
    category = request.args.get("category")
    sql, params = PRODUCT_SQL, ()
    if category is not None:
        if not category.isdigit():
            return jsonify(error="The 'category' parameter must be a number"), 400
        sql += " WHERE p.category_id = ?"
        params = (int(category),)
    rows = get_db().execute(sql + " ORDER BY p.product_id", params).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.get("/products/<int:product_id>")
def product(product_id):
    row = get_db().execute(PRODUCT_SQL + " WHERE p.product_id = ?", (product_id,)).fetchone()
    if row is None:
        abort(404)
    return jsonify(dict(row))


@bp.errorhandler(404)
def not_found(_error):
    return jsonify(error="Not found"), 404
