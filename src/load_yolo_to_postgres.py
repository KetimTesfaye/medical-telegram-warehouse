import os
import csv
import psycopg2
from psycopg2 import extras
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_yolo_csv_to_db():
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/yolo_detections.csv"))
    
    if not os.path.exists(csv_path):
        logging.error(f"Detection dataset missing at: {csv_path}")
        return

    try:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            database=os.environ.get("DB_NAME", "medical-telegram-warehouse"),
            user=os.environ.get("DB_USER", "postgres"),
            password=os.environ.get("DB_PASSWORD", "postgres"), # Uses fallback from session
            port=os.environ.get("DB_PORT", "5432")
        )
        cursor = conn.cursor()
    except Exception as e:
        logging.error(f"Database connection fault: {str(e)}")
        return

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.yolo_image_detections (
                image_name TEXT,
                channel_folder TEXT,
                detected_objects TEXT,
                confidence_scores TEXT,
                primary_object TEXT,
                image_category TEXT,
                PRIMARY KEY (channel_folder, image_name)
            );
        """)
        conn.commit()

        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader) 
            rows = [row for row in reader if row]

        insert_query = """
            INSERT INTO raw.yolo_image_detections (image_name, channel_folder, detected_objects, confidence_scores, primary_object, image_category)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (channel_folder, image_name) DO UPDATE SET
                detected_objects = EXCLUDED.detected_objects,
                confidence_scores = EXCLUDED.confidence_scores,
                image_category = EXCLUDED.image_category;
        """
        
        extras.execute_batch(cursor, insert_query, rows)
        conn.commit()
        logging.info("SUCCESS: Computer vision features fully materialized into raw.yolo_image_detections.")

    except Exception as de:
        logging.error(f"SQL Load Failure: {str(de)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    load_yolo_csv_to_db()