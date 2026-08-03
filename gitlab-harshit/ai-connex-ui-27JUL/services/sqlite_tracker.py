import os
import sqlite3
import json
from datetime import datetime

AIC_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(AIC_ROOT, "workspace_data", "pipeline_history.db")

def _get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = _get_connection()
    cursor = conn.cursor()
    
    # Table to track full pipeline runs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            run_id TEXT PRIMARY KEY,
            dataset_name TEXT,
            status TEXT,
            dag_id TEXT,
            family TEXT,
            suggested_task TEXT,
            manifest_content TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    # Table to track steps history for each run
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_steps_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT,
            step_name TEXT,
            status TEXT,
            output_file TEXT,
            metrics TEXT,
            timestamp TEXT,
            FOREIGN KEY (run_id) REFERENCES pipeline_runs(run_id)
        )
    """)
    
    conn.commit()
    conn.close()

# Initialize on import
init_db()

def init_run(run_id: str, dataset_name: str, dag_id: str, family: str, suggested_task: str):
    conn = _get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO pipeline_runs 
            (run_id, dataset_name, status, dag_id, family, suggested_task, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (run_id, dataset_name, "running", dag_id, family, suggested_task, now, now))
        conn.commit()
    except Exception as e:
        print(f"[SQLiteTracker] Error in init_run: {e}")
    finally:
        conn.close()

def log_step(run_id: str, step_name: str, status: str, output_file: str, metrics: dict = None):
    conn = _get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    metrics_str = json.dumps(metrics) if metrics else None
    try:
        cursor.execute("""
            INSERT INTO pipeline_steps_history 
            (run_id, step_name, status, output_file, metrics, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (run_id, step_name, status, output_file, metrics_str, now))
        
        cursor.execute("""
            UPDATE pipeline_runs 
            SET status = ?, updated_at = ?
            WHERE run_id = ?
        """, (status if step_name.lower().startswith("deployment") else "running", now, run_id))
        
        conn.commit()
    except Exception as e:
        print(f"[SQLiteTracker] Error in log_step: {e}")
    finally:
        conn.close()

def update_run_manifest(run_id: str, manifest_dict: dict):
    conn = _get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    try:
        cursor.execute("""
            UPDATE pipeline_runs 
            SET manifest_content = ?, updated_at = ?
            WHERE run_id = ?
        """, (json.dumps(manifest_dict), now, run_id))
        conn.commit()
    except Exception as e:
        print(f"[SQLiteTracker] Error in update_run_manifest: {e}")
    finally:
        conn.close()

def update_run_status(run_id: str, status: str):
    conn = _get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    try:
        cursor.execute("""
            UPDATE pipeline_runs 
            SET status = ?, updated_at = ?
            WHERE run_id = ?
        """, (status, now, run_id))
        conn.commit()
    except Exception as e:
        print(f"[SQLiteTracker] Error in update_run_status: {e}")
    finally:
        conn.close()
