Medical Telegram Data Warehouse

An end-to-end ELT pipeline processing structured and unstructured public Telegram medical channel feeds in Ethiopia.

Current Setup Task 1: Complete. Implemented raw Data Lake extraction using Telethon and partitioned storage formats.

Task 2: Data Transformation & Analytics Warehouse (dbt)
In this phase, the raw operational database layer was transformed into a clean, production-grade Star Schema Data Warehouse using dbt (Data Build Tool) and PostgreSQL.

Key Implementations:
taging Layer (`models/staging/`): Cleaned, normalized, and cast raw transactional fields (dates, message text, and channel details) from the landing tables into standardized formats.
Dimensional Modeling (`models/marts/`): `dim_channels`: De-duplicated dimension mapping unique tracking characteristics for every medical community channel.
   `fct_messages`: Centralized transactional table tracking message frequencies, view counts, forward metrics, and media flags.
Data Quality & Testing: Integrated structural testing frameworks (including `unique`, `not_null`, and explicit `accepted_values` domain constraints) to automatically validate schema pipeline integrity.