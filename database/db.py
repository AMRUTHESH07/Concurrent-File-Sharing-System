import sqlite3
import os
from datetime import datetime

DB_PATH = "database/files.db"


def get_connection():
    os.makedirs("database", exist_ok=True)
    return sqlite3.connect(DB_PATH, timeout=10)


def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            filesize INTEGER NOT NULL,
            filepath TEXT NOT NULL,
            uploaded_by TEXT DEFAULT 'anonymous',
            upload_time TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

    print("[DATABASE] Initialized successfully")


def add_file(filename, filesize, filepath, uploaded_by="anonymous"):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO files
        (filename, filesize, filepath, uploaded_by, upload_time)
        VALUES (?, ?, ?, ?, ?)
    """, (
        filename,
        filesize,
        filepath,
        uploaded_by,
        datetime.now().isoformat(timespec="seconds")
    ))

    file_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return file_id


def get_file_by_id(file_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, filename, filesize, filepath, uploaded_by, upload_time
        FROM files
        WHERE id = ?
    """, (file_id,))

    file = cursor.fetchone()
    conn.close()

    return file


def list_files():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, filename, filesize, uploaded_by, upload_time
        FROM files
        ORDER BY id DESC
    """)

    files = cursor.fetchall()
    conn.close()

    return files
