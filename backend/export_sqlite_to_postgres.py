import os
import sys
import sqlite3
import logging
from db_sqlite_manager import DB_PATH, get_sqlite_connection

logger = logging.getLogger(__name__)

def export_sqlite_to_postgresql(pg_uri: Optional[str] = None) -> dict:
    """
    Exports local offline SQLite data (datasets, model_experiments, agent_logs)
    to a production PostgreSQL database, maintaining foreign key integrity.
    """
    pg_conn_str = pg_uri or os.environ.get("DATABASE_URL") or "postgresql://admin:password@localhost:5432/aiconnex_db"

    try:
        import psycopg2
    except ImportError:
        logger.warning("[Exporter] psycopg2 not installed. SQLite data remains safe locally.")
        return {
            "status": "warning",
            "message": "psycopg2 library not installed. Install via `pip install psycopg2-binary` to export to PostgreSQL.",
            "exported_counts": {"datasets": 0, "model_experiments": 0, "agent_logs": 0}
        }

    try:
        pg_conn = psycopg2.connect(pg_conn_str)
        pg_cursor = pg_conn.cursor()

        # 1. Create PostgreSQL Schema with Foreign Keys
        pg_cursor.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id SERIAL PRIMARY KEY,
                file_name VARCHAR(255) NOT NULL,
                row_count INT DEFAULT 0,
                col_count INT DEFAULT 0,
                compiled_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS model_experiments (
                id SERIAL PRIMARY KEY,
                dataset_id INT REFERENCES datasets(id) ON DELETE CASCADE,
                model_id VARCHAR(50) NOT NULL,
                family_name VARCHAR(255) NOT NULL,
                r2_score DOUBLE PRECISION DEFAULT 0.0,
                mae DOUBLE PRECISION DEFAULT 0.0,
                rmse DOUBLE PRECISION DEFAULT 0.0,
                status VARCHAR(50) DEFAULT 'Candidate',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS agent_logs (
                id SERIAL PRIMARY KEY,
                dataset_id INT REFERENCES datasets(id) ON DELETE CASCADE,
                agent_name VARCHAR(100) NOT NULL,
                action_taken TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        pg_conn.commit()

        # 2. Read SQLite Records
        sq_conn = get_sqlite_connection()
        sq_cursor = sq_conn.cursor()

        # Export Datasets & Mapping Old IDs -> New PG IDs
        sq_cursor.execute("SELECT id, file_name, row_count, col_count, compiled_path, created_at FROM datasets ORDER BY id ASC;")
        datasets = sq_cursor.fetchall()
        id_map = {}
        ds_count = 0

        for d in datasets:
            pg_cursor.execute(
                """INSERT INTO datasets (file_name, row_count, col_count, compiled_path, created_at)
                   VALUES (%s, %s, %s, %s, %s) RETURNING id;""",
                (d["file_name"], d["row_count"], d["col_count"], d["compiled_path"], d["created_at"])
            )
            new_id = pg_cursor.fetchone()[0]
            id_map[d["id"]] = new_id
            ds_count += 1

        # Export Model Experiments with Foreign Key Mapping
        sq_cursor.execute("SELECT dataset_id, model_id, family_name, r2_score, mae, rmse, status, created_at FROM model_experiments;")
        models = sq_cursor.fetchall()
        mod_count = 0

        for m in models:
            new_ds_id = id_map.get(m["dataset_id"])
            if new_ds_id:
                pg_cursor.execute(
                    """INSERT INTO model_experiments (dataset_id, model_id, family_name, r2_score, mae, rmse, status, created_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s);""",
                    (new_ds_id, m["model_id"], m["family_name"], m["r2_score"], m["mae"], m["rmse"], m["status"], m["created_at"])
                )
                mod_count += 1

        # Export Agent Logs with Foreign Key Mapping
        sq_cursor.execute("SELECT dataset_id, agent_name, action_taken, created_at FROM agent_logs;")
        logs = sq_cursor.fetchall()
        log_count = 0

        for l in logs:
            new_ds_id = id_map.get(l["dataset_id"])
            if new_ds_id:
                pg_cursor.execute(
                    """INSERT INTO agent_logs (dataset_id, agent_name, action_taken, created_at)
                       VALUES (%s, %s, %s, %s);""",
                    (new_ds_id, l["agent_name"], l["action_taken"], l["created_at"])
                )
                log_count += 1

        pg_conn.commit()
        pg_conn.close()
        sq_conn.close()

        logger.info(f"[Exporter] Exported {ds_count} datasets, {mod_count} model experiments, and {log_count} agent logs to PostgreSQL.")
        return {
            "status": "success",
            "message": f"Successfully migrated local SQLite data to PostgreSQL target ({pg_conn_str.split('@')[-1]}).",
            "exported_counts": {"datasets": ds_count, "model_experiments": mod_count, "agent_logs": log_count}
        }
    except Exception as exc:
        logger.error(f"[Exporter] Failed to export to PostgreSQL: {exc}")
        return {
            "status": "error",
            "message": str(exc),
            "exported_counts": {"datasets": 0, "model_experiments": 0, "agent_logs": 0}
        }

if __name__ == "__main__":
    res = export_sqlite_to_postgresql()
    print(res)
