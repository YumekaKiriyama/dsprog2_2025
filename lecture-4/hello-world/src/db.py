import sqlite3

DB_NAME = "weather.db"

def get_conn():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS weather_forecast (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area_code TEXT,
        date TEXT,
        weather_code TEXT,
        weather_text TEXT,
        min_temp INTEGER,
        max_temp INTEGER,
        fetched_at TEXT,
        UNIQUE(area_code, date)
    )
    """)

    conn.commit()
    conn.close()
