import sqlite3

def get_db():
    conn = sqlite3.connect("cart.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store TEXT,
            title TEXT,
            price REAL,
            url TEXT
        )
    """)
    return conn
