import sqlite3
import os

# DBファイルの保存先を指定（data/portal.db）
DB_PATH = os.path.join("data", "portal.db")

# DBに接続する関数（毎回これを使う）
def get_connection():
    return sqlite3.connect(DB_PATH)

# DB初期化（テーブル作成＆カラム追加）
def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # accounts テーブル作成
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            user_id TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    try:
        cursor.execute("ALTER TABLE accounts ADD COLUMN is_admin INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # すでにあれば無視

    # handovers テーブル作成
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS handovers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            detail TEXT DEFAULT '',
            updated_at TEXT NOT NULL,
            updated_by TEXT NOT NULL,
            approved_by TEXT DEFAULT '',
            approver_count INTEGER DEFAULT 0,
            attachment_path TEXT DEFAULT '',
            origin TEXT DEFAULT ''
        )
    """)

    try:
        cursor.execute("ALTER TABLE handovers ADD COLUMN approved_by TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE handovers ADD COLUMN origin TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE daily ADD COLUMN time TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass




    # origins テーブル（発信元マスター）作成
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS origins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            color TEXT DEFAULT '#CCCCCC'
        )
    """)

    # daily テーブル作成（← time カラムを追加）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            updated_at TEXT NOT NULL,
            time TEXT NOT NULL,
            updated_by TEXT NOT NULL,
            detail TEXT DEFAULT '',
            attachment_path TEXT DEFAULT '',
            approved_by TEXT DEFAULT ''
        )
    """)

    conn.commit()
    conn.close()
