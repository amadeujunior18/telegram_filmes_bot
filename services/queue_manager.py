import sqlite3
import json
import logging

logger = logging.getLogger("ZumbiBot")

DB_PATH = "queue.db"

def _connect():
    return sqlite3.connect(DB_PATH, timeout=10)

def init_db():
    with _connect() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS download_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                message_id INTEGER,
                info TEXT,
                status TEXT DEFAULT 'pending',
                retries INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Migration segura: adiciona coluna retries em bancos antigos
        try:
            conn.execute("ALTER TABLE download_queue ADD COLUMN retries INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        conn.execute("UPDATE download_queue SET status = 'pending' WHERE status = 'downloading'")
    logger.info("✅ Banco de dados inicializado (WAL mode ativo).")

def add_to_queue(chat_id, message_id, info):
    with _connect() as conn:
        cursor = conn.execute(
            "INSERT INTO download_queue (chat_id, message_id, info) VALUES (?, ?, ?)",
            (chat_id, message_id, json.dumps(info))
        )
        return cursor.lastrowid

def get_next_pending():
    with _connect() as conn:
        cursor = conn.execute(
            "SELECT id, chat_id, message_id, info FROM download_queue WHERE status = 'pending' ORDER BY id ASC LIMIT 1"
        )
        row = cursor.fetchone()
    if row:
        return {"id": row[0], "chat_id": row[1], "message_id": row[2], "info": json.loads(row[3])}
    return None

def update_status(queue_id, status):
    with _connect() as conn:
        conn.execute("UPDATE download_queue SET status = ? WHERE id = ?", (status, queue_id))

def increment_retries(queue_id):
    with _connect() as conn:
        conn.execute("UPDATE download_queue SET retries = retries + 1 WHERE id = ?", (queue_id,))

def get_retry_count(queue_id):
    with _connect() as conn:
        cursor = conn.execute("SELECT retries FROM download_queue WHERE id = ?", (queue_id,))
        row = cursor.fetchone()
    return row[0] if row else 0

def get_queue_stats():
    with _connect() as conn:
        cursor = conn.execute("SELECT status, COUNT(*) FROM download_queue GROUP BY status")
        return dict(cursor.fetchall())

def get_full_queue():
    with _connect() as conn:
        cursor = conn.execute(
            "SELECT id, info FROM download_queue WHERE status = 'downloading' ORDER BY id ASC"
        )
        downloading = [{"id": r[0], "info": json.loads(r[1])} for r in cursor.fetchall()]

        cursor = conn.execute(
            "SELECT id, info FROM download_queue WHERE status = 'pending' ORDER BY id ASC LIMIT 10"
        )
        pending = [{"id": r[0], "info": json.loads(r[1])} for r in cursor.fetchall()]

    return downloading, pending
