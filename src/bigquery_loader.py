"""Load structured records into BigQuery."""
import os
import re

from dotenv import load_dotenv

load_dotenv()

SCHEMA_FIELDS = {
    "contacts": [
        ("id", "STRING"),
        ("firstname", "STRING"),
        ("lastname", "STRING"),
        ("email", "STRING"),
        ("lead_status", "STRING"),
        ("created_at", "TIMESTAMP"),
        ("ingested_at", "TIMESTAMP"),
    ],
    "deals": [
        ("id", "STRING"),
        ("deal_name", "STRING"),
        ("amount", "FLOAT"),
        ("stage", "STRING"),
        ("pipeline", "STRING"),
        ("close_date", "TIMESTAMP"),
        ("created_at", "TIMESTAMP"),
        ("ingested_at", "TIMESTAMP"),
    ],
    "companies": [
        ("id", "STRING"),
        ("name", "STRING"),
        ("domain", "STRING"),
        ("industry", "STRING"),
        ("country", "STRING"),
        ("employees", "INTEGER"),
        ("created_at", "TIMESTAMP"),
        ("ingested_at", "TIMESTAMP"),
    ],
}

_DATASET_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,1023}$")


def load(table_name: str, rows: list[dict]) -> None:
    project = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("GCP_DATASET_ID", "crm_raw")
    if not project:
        raise RuntimeError("GCP_PROJECT_ID is required to load rows into BigQuery.")
    if table_name not in SCHEMA_FIELDS:
        raise ValueError(f"Unsupported BigQuery table: {table_name}")
    if not _DATASET_PATTERN.fullmatch(dataset):
        raise ValueError(f"Invalid BigQuery dataset identifier: {dataset!r}")
    if not rows and os.getenv("ALLOW_EMPTY_FULL_REFRESH", "false").lower() != "true":
        raise RuntimeError(
            f"Refusing to truncate {table_name} with an empty extract. "
            "Set ALLOW_EMPTY_FULL_REFRESH=true only for an intentional reset."
        )

    from google.cloud import bigquery

    client = bigquery.Client(project=project)
    table_id = f"{project}.{dataset}.{table_name}"
    job_config = bigquery.LoadJobConfig(
        schema=[bigquery.SchemaField(name, field_type) for name, field_type in SCHEMA_FIELDS[table_name]],
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    job = client.load_table_from_json(rows, table_id, job_config=job_config)
    job.result(timeout=600)
    print(f"Loaded {len(rows)} rows into {table_id}")
