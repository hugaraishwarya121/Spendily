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
