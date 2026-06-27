import os
import json
import psycopg2
from psycopg2 import extras
import logging
import time

# Configure centralized production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ingestion_pipeline.log"),
        logging.StreamHandler()
    ]
)

def load_config():
    """Loads operational configurations from an isolated JSON file."""
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "config.json"))
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load pipeline configuration file: {str(e)}")
        raise

def load_raw_data():
    config = load_config()
    db_cfg = config["database"]
    pipe_cfg = config["pipeline"]
    
    # Retrieve sensitive database credentials securely from environment variables
    db_pass = os.environ.get("DB_PASSWORD", "your_postgres_password") 

    raw_data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/raw_telegram_data.json"))
    
    if not os.path.exists(raw_data_path):
        logging.error(f"CRITICAL: Ingestion source missing at {raw_data_path}")
        return

    try:
        with open(raw_data_path, "r", encoding="utf-8") as f:
            messages = json.load(f)
        logging.info(f"Loaded {len(messages)} raw records from JSON source.")
    except json.JSONDecodeError as e:
        logging.error(f"Data Corruption Error: Failed to parse JSON: {str(e)}")
        return

    # Robust Connection Loop with Automatic Retries
    conn = None
    max_retries = pipe_cfg.get("max_retries", 3)
    delay = pipe_cfg.get("retry_delay_seconds", 5)
    
    for attempt in range(1, max_retries + 1):
        try:
            logging.info(f"Database connection attempt {attempt} of {max_retries}...")
            conn = psycopg2.connect(
                host=db_cfg["host"],
                database=db_cfg["name"],
                user=db_cfg["user"],
                password=db_pass,
                port=db_cfg["port"]
            )
            break  # Connection successful, break the retry loop
        except psycopg2.OperationalError as oe:
            logging.warning(f"Connection attempt {attempt} failed: {str(oe)}")
            if attempt < max_retries:
                logging.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logging.error("CRITICAL: All database connectivity retry attempts exhausted.")
                return

    try:
        cursor = conn.cursor()
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
        logging.info("SUCCESS: Raw database landing layer loaded flawlessly via batch execution.")

    except psycopg2.DatabaseError as de:
        logging.error(f"PostgreSQL Execution error: {str(de)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cursor.close()
            conn.close()
            logging.info("Database connection safely closed.")

if __name__ == "__main__":
    load_raw_data()