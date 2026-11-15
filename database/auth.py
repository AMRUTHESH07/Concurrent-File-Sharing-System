import sqlite3
import os
import hashlib
import secrets
import hmac

DB_PATH = "database/files.db"


def register_user(username, password):
    if not username or not password:
        return False, "Username and password cannot be empty"

    if len(password) < 8:
        return False, "Password must contain at least 8 characters"

    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        200000
    )

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO users (username, salt, password_hash)
            VALUES (?, ?, ?)
        """, (username, salt.hex(), password_hash.hex()))

        conn.commit()
        return True, "Registration successful"

    except sqlite3.IntegrityError:
        return False, "Username already exists"

    finally:
        conn.close()


def login_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT salt, password_hash
        FROM users
        WHERE username = ?
    """, (username,))

    user = cursor.fetchone()
    conn.close()

    if user is None:
        return False

    salt = bytes.fromhex(user[0])

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        200000
    )

    return hmac.compare_digest(
        password_hash.hex(),
        user[1]
    )


def initialize_auth_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            salt TEXT NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

    print("[AUTH] User database initialized")
