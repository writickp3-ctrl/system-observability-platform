import sqlite3
import os
from src.logger import get_logger

logger = get_logger(__name__)

DB_PATH = os.environ.get('DB_PATH', 'logs.db')


def connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """Create logs table if it doesn't exist."""
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT    NOT NULL,
                level     TEXT    NOT NULL,
                message   TEXT    NOT NULL
            )
        """)
        conn.commit()
        conn.close()
        logger.info("Database initialised at %s", DB_PATH)
    except Exception as exc:
        logger.error("DB init failed: %s", exc)
        raise


def insert_log(timestamp: str, level: str, message: str) -> None:
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO logs (timestamp, level, message) VALUES (?, ?, ?)",
            (timestamp, level, message)
        )
        conn.commit()
        conn.close()
        logger.debug("Inserted log | level=%s | msg=%s", level, message[:60])
    except Exception as exc:
        logger.error("Insert failed: %s", exc)
        raise


def fetch_logs() -> list:
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT id, timestamp, level, message FROM logs ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception as exc:
        logger.error("Fetch failed: %s", exc)
        return []


def fetch_log_count() -> int:
    try:
        conn = connect()
        cur = conn.cursor()
        count = cur.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0


def clear_logs() -> None:
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM logs")
        conn.commit()
        conn.close()
        logger.info("Logs cleared")
    except Exception as exc:
        logger.error("Clear failed: %s", exc)
