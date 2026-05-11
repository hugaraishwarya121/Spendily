import sqlite3

import pytest
from werkzeug.security import check_password_hash


# ------------------------------------------------------------------ #
# get_db()                                                            #
# ------------------------------------------------------------------ #

def test_get_db_returns_connection(initialized_db):
    from database.db import get_db
    conn = get_db()
    assert isinstance(conn, sqlite3.Connection)
    conn.close()


def test_get_db_row_factory_is_sqlite_row(initialized_db):
    from database.db import get_db
    conn = get_db()
    assert conn.row_factory is sqlite3.Row
    conn.close()


def test_get_db_foreign_keys_enabled(initialized_db):
    from database.db import get_db
    conn = get_db()
    row = conn.execute("PRAGMA foreign_keys").fetchone()
    assert row[0] == 1
    conn.close()


def test_get_db_returns_independent_connections(initialized_db):
    from database.db import get_db
    conn1 = get_db()
    conn2 = get_db()
    assert conn1 is not conn2
    conn1.close()
    conn2.close()


# ------------------------------------------------------------------ #
# init_db()                                                           #
# ------------------------------------------------------------------ #

def test_init_db_creates_users_table(db_path):
    from database.db import init_db
    init_db()
    conn = sqlite3.connect(str(db_path))
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
    ).fetchone()
    conn.close()
    assert row is not None


def test_init_db_creates_expenses_table(db_path):
    from database.db import init_db
    init_db()
    conn = sqlite3.connect(str(db_path))
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='expenses'"
    ).fetchone()
    conn.close()
    assert row is not None


def test_init_db_users_table_columns(db_path):
    from database.db import init_db
    init_db()
    conn = sqlite3.connect(str(db_path))
    cols = {row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
    conn.close()
    assert {"id", "name", "email", "password_hash", "created_at"} <= cols


def test_init_db_expenses_table_columns(db_path):
    from database.db import init_db
    init_db()
    conn = sqlite3.connect(str(db_path))
    cols = {row[1] for row in conn.execute("PRAGMA table_info(expenses)").fetchall()}
    conn.close()
    assert {"id", "user_id", "amount", "category", "date", "description", "created_at"} <= cols


def test_init_db_is_idempotent(db_path):
    from database.db import init_db
    init_db()
    init_db()  # second call must not raise


def test_init_db_foreign_key_constraint_on_expenses(db_path):
    from database.db import init_db
    init_db()
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)",
            (9999, 10.0, "Food", "2026-01-01"),
        )
        conn.commit()
    conn.close()


def test_init_db_email_unique_constraint(db_path):
    from database.db import init_db
    init_db()
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("User One", "dup@test.com", "hash1"),
    )
    conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("User Two", "dup@test.com", "hash2"),
        )
        conn.commit()
    conn.close()


# ------------------------------------------------------------------ #
# seed_db()                                                           #
# ------------------------------------------------------------------ #

def test_seed_db_creates_demo_user(seeded_db):
    conn = sqlite3.connect(str(seeded_db))
    rows = conn.execute(
        "SELECT * FROM users WHERE email = 'demo@spendly.com'"
    ).fetchall()
    conn.close()
    assert len(rows) == 1


def test_seed_db_demo_user_fields(seeded_db):
    conn = sqlite3.connect(str(seeded_db))
    row = conn.execute(
        "SELECT name, email FROM users WHERE email = 'demo@spendly.com'"
    ).fetchone()
    conn.close()
    assert row[0] == "Demo User"
    assert row[1] == "demo@spendly.com"


def test_seed_db_password_is_hashed(seeded_db):
    conn = sqlite3.connect(str(seeded_db))
    row = conn.execute(
        "SELECT password_hash FROM users WHERE email = 'demo@spendly.com'"
    ).fetchone()
    conn.close()
    password_hash = row[0]
    assert password_hash != "demo123"
    assert check_password_hash(password_hash, "demo123")


def test_seed_db_creates_eight_expenses(seeded_db):
    conn = sqlite3.connect(str(seeded_db))
    count = conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
    conn.close()
    assert count == 8


def test_seed_db_expenses_belong_to_demo_user(seeded_db):
    conn = sqlite3.connect(str(seeded_db))
    user_id = conn.execute(
        "SELECT id FROM users WHERE email = 'demo@spendly.com'"
    ).fetchone()[0]
    distinct_user_ids = [
        row[0] for row in conn.execute("SELECT DISTINCT user_id FROM expenses").fetchall()
    ]
    conn.close()
    assert distinct_user_ids == [user_id]


def test_seed_db_expense_amounts(seeded_db):
    conn = sqlite3.connect(str(seeded_db))
    amounts = {row[0] for row in conn.execute("SELECT amount FROM expenses").fetchall()}
    conn.close()
    assert amounts == {12.50, 35.00, 120.00, 45.00, 18.00, 60.00, 9.99, 22.00}


def test_seed_db_expense_categories(seeded_db):
    conn = sqlite3.connect(str(seeded_db))
    categories = {
        row[0] for row in conn.execute("SELECT DISTINCT category FROM expenses").fetchall()
    }
    conn.close()
    assert categories == {"Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"}


def test_seed_db_is_idempotent(seeded_db):
    from database.db import seed_db
    seed_db()  # called a second time
    conn = sqlite3.connect(str(seeded_db))
    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    expense_count = conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
    conn.close()
    assert user_count == 1
    assert expense_count == 8


def test_seed_db_requires_initialized_db(db_path):
    from database.db import seed_db
    with pytest.raises(sqlite3.OperationalError):
        seed_db()
