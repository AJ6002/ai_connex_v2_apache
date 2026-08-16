import os
import sqlite3
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scratch", "aiconnex_offline.db"))

def get_sqlite_connection() -> sqlite3.Connection:
    """Connects to local SQLite database with Foreign Keys enabled."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    # MANDATORY: Enable Foreign Key constraint enforcement in SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.row_factory = sqlite3.Row
    return conn

def init_sqlite_db():
    """Initializes relational tables with Foreign Keys."""
    with get_sqlite_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Datasets Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                row_count INTEGER DEFAULT 0,
                col_count INTEGER DEFAULT 0,
                compiled_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. Model Experiments Table (With Foreign Key to Datasets)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER NOT NULL,
                model_id TEXT NOT NULL,
                family_name TEXT NOT NULL,
                r2_score REAL DEFAULT 0.0,
                mae REAL DEFAULT 0.0,
                rmse REAL DEFAULT 0.0,
                status TEXT DEFAULT 'Candidate',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
            );
        """)

        # 3. Agent Execution Logs Table (With Foreign Key to Datasets)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER NOT NULL,
                agent_name TEXT NOT NULL,
                action_taken TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
            );
        """)

        conn.commit()
        logger.info(f"[SQLite] Initialized offline database at {DB_PATH} with Foreign Keys enabled.")

def save_dataset_record(file_name: str, row_count: int, col_count: int, compiled_path: str) -> int:
    """Saves uploaded dataset record into SQLite."""
    with get_sqlite_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO datasets (file_name, row_count, col_count, compiled_path) VALUES (?, ?, ?, ?);",
            (file_name, row_count, col_count, compiled_path)
        )
        conn.commit()
        return cursor.lastrowid

def save_model_experiment(dataset_id: int, model_id: str, family_name: str, r2_score: float, mae: float, rmse: float, status: str = "Candidate"):
    """Saves model candidate record linked by Foreign Key to dataset_id."""
    with get_sqlite_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO model_experiments (dataset_id, model_id, family_name, r2_score, mae, rmse, status)
               VALUES (?, ?, ?, ?, ?, ?, ?);""",
            (dataset_id, model_id, family_name, r2_score, mae, rmse, status)
        )
        conn.commit()

def log_agent_action(dataset_id: int, agent_name: str, action_taken: str):
    """Logs agent execution action linked by Foreign Key to dataset_id."""
    with get_sqlite_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO agent_logs (dataset_id, agent_name, action_taken) VALUES (?, ?, ?);",
            (dataset_id, agent_name, action_taken)
        )
        conn.commit()

# Ensure DB is initialized when module loaded
init_sqlite_db()
