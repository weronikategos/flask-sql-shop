import sqlite3
from pathlib import Path

import click
from flask import current_app, g

HERE = Path(__file__).parent


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(with_sample_data=True):
    db = get_db()
    db.executescript((HERE / "schema.sql").read_text(encoding="utf-8"))
    if with_sample_data:
        db.executescript((HERE / "seed.sql").read_text(encoding="utf-8"))


@click.command("init-db")
def init_db_command():
    """Recreates the tables and fills them with sample products."""
    init_db()
    click.echo("Database is ready.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
