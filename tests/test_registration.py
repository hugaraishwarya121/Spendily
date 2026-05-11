import sqlite3

import pytest
from flask import session
from werkzeug.security import check_password_hash

_VALID = {"name": "Alice", "email": "alice@example.com", "password": "securepass"}


# ------------------------------------------------------------------ #
# GET behaviour                                                        #
# ------------------------------------------------------------------ #

def test_register_get_renders_form(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert b"Create your account" in response.data


def test_register_redirects_if_logged_in(logged_in_client):
    response = logged_in_client.get("/register", follow_redirects=False)
    assert response.status_code == 302
    assert response.location.endswith("/profile")


# ------------------------------------------------------------------ #
# Validation failures                                                  #
# ------------------------------------------------------------------ #

def test_register_missing_fields(client):
    response = client.post("/register", data={"name": "", "email": "", "password": ""})
    assert response.status_code == 200
    assert b"All fields are required." in response.data


def test_register_short_password(client):
    response = client.post(
        "/register",
        data={"name": "Alice", "email": "alice@example.com", "password": "short"},
    )
    assert response.status_code == 200
    assert b"at least 8 characters" in response.data


def test_register_duplicate_email(client, initialized_db):
    conn = sqlite3.connect(str(initialized_db))
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Existing", "alice@example.com", "somehash"),
    )
    conn.commit()
    conn.close()

    response = client.post("/register", data=_VALID)
    assert response.status_code == 200
    assert b"already exists" in response.data


# ------------------------------------------------------------------ #
# Success path                                                         #
# ------------------------------------------------------------------ #

def test_register_success_creates_user(client, initialized_db):
    client.post("/register", data=_VALID)
    conn = sqlite3.connect(str(initialized_db))
    row = conn.execute(
        "SELECT name FROM users WHERE email = ?", ("alice@example.com",)
    ).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == "Alice"


def test_register_success_hashes_password(client, initialized_db):
    client.post("/register", data=_VALID)
    conn = sqlite3.connect(str(initialized_db))
    row = conn.execute(
        "SELECT password_hash FROM users WHERE email = ?", ("alice@example.com",)
    ).fetchone()
    conn.close()
    stored_hash = row[0]
    assert stored_hash != "securepass"
    assert check_password_hash(stored_hash, "securepass")


def test_register_success_sets_session(client):
    with client:
        client.post("/register", data=_VALID, follow_redirects=False)
        assert session.get("user_id") is not None
        assert isinstance(session["user_id"], int)
        assert session.get("user_name") == "Alice"


def test_register_success_redirects(client):
    response = client.post("/register", data=_VALID, follow_redirects=False)
    assert response.status_code == 302
    assert response.location.endswith("/profile")
