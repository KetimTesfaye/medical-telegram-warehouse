Medical Telegram Data Warehouse

An end-to-end ELT pipeline processing structured and unstructured public Telegram medical channel feeds in Ethiopia.

Current Setup Task 1: Complete. Implemented raw Data Lake extraction using Telethon and partitioned storage formats.

End-to-End Pipeline Integration & Execution Flow

This project features a fully unified, multi-stage data architecture that automates the collection, database ingestion, and analytical transforming of Telegram public medical channels.

Data Flow Architecture
1.Extraction (Scraper Layer): Custom async Python scripts tap public API channels and dump raw unstructured messages directly into local JSON footprints (`data/raw_telegram_data.json`).
2.Ingestion (Loader Layer): A config-driven Python pipeline (`src/load_to_postgres.py`) reads the file system, coordinates an automated retry connectivity matrix, passes strict schema validations, and maps entries directly into a structured landing table inside the PostgreSQL `raw` schema layer.
3. Transformation (Analytics Layer): dbt picks up the data from `raw.telegram_messages`, running cleaning logic in the staging layer before joining records into an optimized analytical Star Schema (`dim_channels` and `fct_messages`) ready for reporting.

Operational Setup & Execution Guide

To execute the entire pipeline from scratch, run the following workflow sequence:

```bash
Step 1: Extract real-time channels using the scraper
python src/telegram_scraper.py

Step 2: Set your database password environment variable and run the ingestion pipeline
export DB_PASSWORD="your_actual_password"
python src/load_to_postgres.py

Step 3: Navigate to your warehouse and trigger dbt compilation transformations
cd medical_warehouse
dbt run --profiles-dir .
dbt test --profiles-dir .

Task 2: Data Transformation & Analytics Warehouse (dbt)
In this phase, the raw operational database layer was transformed into a clean, production-grade Star Schema Data Warehouse using dbt (Data Build Tool) and PostgreSQL.

Key Implementations:
taging Layer (`models/staging/`): Cleaned, normalized, and cast raw transactional fields (dates, message text, and channel details) from the landing tables into standardized formats.
Dimensional Modeling (`models/marts/`): `dim_channels`: De-duplicated dimension mapping unique tracking characteristics for every medical community channel.
   `fct_messages`: Centralized transactional table tracking message frequencies, view counts, forward metrics, and media flags.
Data Quality & Testing: Integrated structural testing frameworks (including `unique`, `not_null`, and explicit `accepted_values` domain constraints) to automatically validate schema pipeline integrity.