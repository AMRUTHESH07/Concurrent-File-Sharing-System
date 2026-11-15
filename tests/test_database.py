import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from database import auth, db


@pytest.fixture
def test_database(tmp_path, monkeypatch):
    test_db_path = str(tmp_path / "test_files.db")

    monkeypatch.setattr(auth, "DB_PATH", test_db_path)
    monkeypatch.setattr(db, "DB_PATH", test_db_path)

    auth.initialize_auth_database()
    db.initialize_database()

    return test_db_path


# 1. Test user registration
def test_user_registration(test_database):
    success, message = auth.register_user("alice", "Password123")

    assert success is True
    assert message == "Registration successful"


# 2. Test duplicate username
def test_duplicate_username(test_database):
    auth.register_user("alice", "Password123")

    success, message = auth.register_user("alice", "AnotherPass123")

    assert success is False
    assert message == "Username already exists"


# 3. Test password validation
def test_password_validation(test_database):
    success, message = auth.register_user("alice", "short")

    assert success is False
    assert message == "Password must contain at least 8 characters"


# 4. Test login authentication
def test_correct_and_incorrect_login(test_database):
    auth.register_user("alice", "Password123")

    assert auth.login_user("alice", "Password123") is True
    assert auth.login_user("alice", "WrongPassword") is False
    assert auth.login_user("unknown", "Password123") is False


# 5. Test password hashing
def test_password_is_not_stored_as_plaintext(test_database):
    auth.register_user("alice", "Password123")

    conn = sqlite3.connect(test_database)
    user = conn.execute(
        "SELECT salt, password_hash FROM users WHERE username = ?",
        ("alice",)
    ).fetchone()
    conn.close()

    assert user is not None
    assert user[0] != "Password123"
    assert user[1] != "Password123"
    assert len(bytes.fromhex(user[0])) == 16


# 6. Test file metadata insertion and retrieval
def test_file_metadata_insert_and_retrieve(test_database):
    file_id = db.add_file(
        "example.txt",
        1024,
        "storage/uploaded_files/example.txt",
        "alice"
    )

    result = db.get_file_by_id(file_id)

    assert result is not None
    assert result[0] == file_id
    assert result[1] == "example.txt"
    assert result[2] == 1024
    assert result[4] == "alice"


# 7. Test file listing
def test_list_files(test_database):
    db.add_file("first.txt", 100, "/tmp/first.txt", "alice")
    db.add_file("second.txt", 200, "/tmp/second.txt", "bob")

    files = db.list_files()

    assert len(files) == 2
    assert files[0][1] == "second.txt"
    assert files[1][1] == "first.txt"


# 8. Test concurrent database insertions
def test_concurrent_file_insertions(test_database):
    def insert_file(number):
        return db.add_file(
            f"concurrent_{number}.txt",
            1024,
            f"/tmp/concurrent_{number}.txt",
            "alice"
        )

    with ThreadPoolExecutor(max_workers=10) as executor:
        file_ids = list(executor.map(insert_file, range(20)))

    assert len(file_ids) == 20
    assert len(set(file_ids)) == 20
    assert len(db.list_files()) == 20
