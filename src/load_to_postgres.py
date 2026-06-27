import os
import json
import psycopg2
from psycopg2 import extras
import logging

# 1. Setup production logging matrix
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ingestion_pipeline.log"),
        logging.StreamHandler()
    ]
)

DB_HOST = "localhost"
DB_NAME = "medical-telegram-warehouse"
DB_USER = "postgres"
DB_PASS = "your_postgres_password"  # Update with your local password or use os.environ.get()
DB_PORT = "5432"

def load_raw_data():
    raw_data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/raw_telegram_data.json"))
    
    # Error Handling Block 1: Check File Presence
    if not os.path.exists(raw_data_path):
        logging.error(f"CRITICAL: Ingestion canceled. Raw source missing at: {raw_data_path}")
        return

    # Error Handling Block 2: Verify Parse Integrity
    try:
        with open(raw_data_path, "r", encoding="utf-8") as f:
            messages = json.load(f)
        logging.info(f"Successfully loaded {len(messages)} raw records from local cache.")
    except json.JSONDecodeError as jde:
        logging.error(f"FATAL: Structural corruption detected inside JSON file: {str(jde)}")
        return
    except Exception as e:
        logging.error(f"UNEXPECTED: System I/O file block error: {str(e)}")
        return

    conn = None
    try:
        # Error Handling Block 3: Database Connectivity Handshake
        logging.info("Opening operational database transaction pool...")
        conn = psycopg2.connect(
            host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT
        )
        cursor = conn.cursor()
        
        # Enforce raw schema boundaries
        cursor.execute("CREATE SCHEMA IF NOT EXISTS raw;")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.telegram_messages (
                message_id BIGINT PRIMARY KEY,
                channel_name TEXT,
                message_at TIMESTAMP WITH TIME ZONE,
                message_text TEXT,
                view_count INTEGER,
                forward_count INTEGER,
                has_media BOOLEAN
            );
        """)
        conn.commit()

        # Batch loading using psycopg2 extras for execution velocity
        insert_query = """
            INSERT INTO raw.telegram_messages (message_id, channel_name, message_at, message_text, view_count, forward_count, has_media)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (message_id) DO UPDATE SET
                view_count = EXCLUDED.view_count,
                forward_count = EXCLUDED.forward_count;
        """
        
        prepare_data = []
        for msg in messages:
            prepare_data.append((
                msg.get("id"),
                msg.get("channel"),
                msg.get("date"),
                msg.get("text"),
                msg.get("views", 0) if msg.get("views") is not None else 0,
                msg.get("forwards", 0) if msg.get("forwards") is not None else 0,
                msg.get("has_media", False)
            ))

        extras.execute_batch(cursor, insert_query, prepare_data)
        conn.commit()
        logging.info(f"SUCCESS: Pipeline flush completed. Bulk loaded rows into raw.telegram_messages.")

    except psycopg2.DatabaseError as dbe:
        logging.error(f"DATABASE CRASH: PostgreSQL transaction broken. Rolling back operations. Trace: {str(dbe)}")
        if conn:
            conn.rollback()
    except Exception as e:
        logging.error(f"PIPELINE CRASH: Unexpected data transformation anomaly: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cursor.close()
            conn.close()
            logging.info("Database transaction connection safely returned to pool.")

if __name__ == "__main__":
    load_raw_data()