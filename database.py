import sqlite3
from datetime import datetime, timedelta

DB_PATH = "users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, name TEXT, username TEXT, plan TEXT DEFAULT 'free', premium_until TEXT, daily_count INTEGER DEFAULT 0, total_ask INTEGER DEFAULT 0, last_reset TEXT, mode TEXT DEFAULT 'fusion', refer_by INTEGER, refer_count INTEGER DEFAULT 0, banned INTEGER DEFAULT 0, joined_at TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS payments (payment_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, user_name TEXT, plan TEXT, duration TEXT, amount INTEGER, method TEXT, trx_id TEXT, screenshot TEXT, status TEXT DEFAULT 'pending', timestamp TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, question TEXT, answer TEXT, mode TEXT, timestamp TEXT)")
    conn.commit()
    conn.close()

def get_conn():
    return sqlite3.connect(DB_PATH)

def get_user(user_id):
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def create_user(user_id, name, username="", refer_by=None):
    conn = get_conn()
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("INSERT OR IGNORE INTO users (user_id, name, username, plan, daily_count, total_ask, last_reset, mode, refer_by, joined_at) VALUES (?, ?, ?, 'free', 0, 0, ?, 'fusion', ?, ?)", (user_id, name, username, now, refer_by, now))
    conn.commit()
    conn.close()
    if refer_by:
        update_refer_count(refer_by)

def update_user(user_id, **kwargs):
    if not kwargs:
        return
    conn = get_conn()
    c = conn.cursor()
    fields = ", ".join([k + "=?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [user_id]
    c.execute("UPDATE users SET " + fields + " WHE
