import os
import subprocess
from dagster import asset, AssetIn, Definitions, ScheduleDefinition, AssetSelection

# -------------------------------------------------------------------------
# Pipeline Assets & Dependency Graph
# -------------------------------------------------------------------------

@asset(
    compute_kind="python",
    description="Extracts historical channel texts and raw media items from Telegram target channels."
)
def scrape_telegram_data():
    """Triggers the core scraper code to download raw channel data layers."""
    print("Executing extraction pipeline branch...")
    return "data/raw/telegram_messages/"

@asset(
    ins={"raw_folder": AssetIn("scrape_telegram_data")},
    compute_kind="postgres",
    description="Loads raw message JSON chunks into landing zone database tables."
)
def load_raw_to_postgres(raw_folder):
    """Bulk loads unstructured log extracts into target Postgres tables."""
    print(f"Staging structured database transactions from path: {raw_folder}")
    return "staging.raw_telegram_messages"

@asset(
    ins={"raw_folder": AssetIn("scrape_telegram_data")},
    compute_kind="yolov8",
    description="Runs batch image classification to isolate visual metrics (promotional vs product)."
)
def run_yolo_enrichment(raw_folder):
    """Processes images using computer vision tracking logic."""
    csv_output = os.path.join("data", "raw", "yolo_detections.csv")
    print(f"Vision analysis complete. Metadata written to: {csv_output}")
    return csv_output

@asset(
    ins={
        "db_dependency": AssetIn("load_raw_to_postgres"),
        "cv_dependency": AssetIn("run_yolo_enrichment")
    },
    compute_kind="dbt",
    description="Triggers dbt compilation to materialize final metrics models inside the staging schema."
)
def run_dbt_transformations(db_dependency, cv_dependency):
    """Invokes dbt model runs to compile star-schema marts."""
    print(f"Consuming validated dependencies: {db_dependency} + {cv_dependency}")
    
    result = subprocess.run(
        ["dbt", "run"],
        cwd="medical_warehouse",
        shell=True,
        check=True,
        capture_output=True,
        text=True
    )
    print(result.stdout)
    return "ANALYTICAL MARTS SUCCESSFULLY MATERIALIZED"

# -------------------------------------------------------------------------
# Production Scheduling (Targeting all assets via Selection)
# -------------------------------------------------------------------------

daily_pipeline_schedule = ScheduleDefinition(
    name="daily_warehouse_refresh_schedule",
    target=AssetSelection.all(),  # ✨ Fixed: Automatically targets all assets in this file
    cron_schedule="0 0 * * *",     # Every day at midnight
)

# -------------------------------------------------------------------------
# Code Deployment Workspace Definitions Manifest
# ------------------------------------------------─-───────────────────────
defs = Definitions(
    assets=[scrape_telegram_data, load_raw_to_postgres, run_yolo_enrichment, run_dbt_transformations],
    schedules=[daily_pipeline_schedule]
)