import sqlite3
import json
import os
import logging

logger = logging.getLogger("ZumbiBot")

DB_PATH = "queue.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS download_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            message_id INTEGER,
            info TEXT,
            status TEXT DEFAULT 'pending', -- pending, downloading, completed, failed
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Se o bot reiniciou, resetamos o que estava 'downloading' para 'pending'
    cursor.execute("UPDATE download_queue SET status = 'pending' WHERE status = 'downloading'")
    conn.commit()
    conn.close()

def add_to_queue(chat_id, message_id, info):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO download_queue (chat_id, message_id, info) VALUES (?, ?, ?)",
        (chat_id, message_id, json.dumps(info))
    )
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id

def get_next_pending():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, chat_id, message_id, info FROM download_queue WHERE status = 'pending' ORDER BY id ASC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "chat_id": row[1], "message_id": row[2], "info": json.loads(row[3])}
    return None

def update_status(queue_id, status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE download_queue SET status = ? WHERE id = ?", (status, queue_id))
    conn.commit()
    conn.close()

def get_queue_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT status, COUNT(*) FROM download_queue GROUP BY status")
    stats = dict(cursor.fetchall())
    conn.close()
    return stats

def get_full_queue():
    """Retorna itens atualmente baixando e os pendentes na fila."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Itens baixando agora
    cursor.execute("SELECT id, info FROM download_queue WHERE status = 'downloading' ORDER BY id ASC")
    downloading = [{"id": r[0], "info": json.loads(r[1])} for r in cursor.fetchall()]
    
    # Próximos 10 itens na fila
    cursor.execute("SELECT id, info FROM download_queue WHERE status = 'pending' ORDER BY id ASC LIMIT 10")
    pending = [{"id": r[0], "info": json.loads(r[1])} for r in cursor.fetchall()]
    
    conn.close()
    return downloading, pending
