import pytest


@pytest.fixture()
def db_path(tmp_path, monkeypatch):
    path = tmp_path / "test_spendly.db"
    monkeypatch.setattr("database.db._DB_PATH", str(path))
    return path


@pytest.fixture()
def initialized_db(db_path):
    from database.db import init_db
    init_db()
    return db_path


@pytest.fixture()
def seeded_db(initialized_db):
    from database.db import seed_db
    seed_db()
    return initialized_db


@pytest.fixture()
def app_instance():
    from app import app
    app.testing = True
    return app


@pytest.fixture()
def client(app_instance, initialized_db):
    return app_instance.test_client()


@pytest.fixture()
def logged_in_client(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Test User"
    return client
