import pytest

from shop import create_app
from shop.db import init_db


@pytest.fixture
def app(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db"), "SECRET_KEY": "test"})
    with app.app_context():
        init_db()
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def logged_in(client):
    client.post("/register", data={"name": "Ala", "email": "ala@example.com", "password": "secretpass"})
    client.post("/login", data={"email": "ala@example.com", "password": "secretpass"})
    return client
