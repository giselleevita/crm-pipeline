"""Load structured records into BigQuery."""
import os
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

PROJECT = os.getenv("GCP_PROJECT_ID")
DATASET = os.getenv("GCP_DATASET_ID", "crm_raw")

SCHEMAS = {
    "contacts": [
        bigquery.SchemaField("id", "STRING"),
        bigquery.SchemaField("firstname", "STRING"),
        bigquery.SchemaField("lastname", "STRING"),
        bigquery.SchemaField("email", "STRING"),
        bigquery.SchemaField("lead_status", "STRING"),
        bigquery.SchemaField("created_at", "TIMESTAMP"),
        bigquery.SchemaField("ingested_at", "TIMESTAMP"),
    ],
    "deals": [
        bigquery.SchemaField("id", "STRING"),
        bigquery.SchemaField("deal_name", "STRING"),
        bigquery.SchemaField("amount", "FLOAT"),
        bigquery.SchemaField("stage", "STRING"),
        bigquery.SchemaField("pipeline", "STRING"),
        bigquery.SchemaField("close_date", "TIMESTAMP"),
        bigquery.SchemaField("created_at", "TIMESTAMP"),
        bigquery.SchemaField("ingested_at", "TIMESTAMP"),
    ],
    "companies": [
        bigquery.SchemaField("id", "STRING"),
        bigquery.SchemaField("name", "STRING"),
        bigquery.SchemaField("domain", "STRING"),
        bigquery.SchemaField("industry", "STRING"),
        bigquery.SchemaField("country", "STRING"),
        bigquery.SchemaField("employees", "INTEGER"),
        bigquery.SchemaField("created_at", "TIMESTAMP"),
        bigquery.SchemaField("ingested_at", "TIMESTAMP"),
    ],
}


def load(table_name: str, rows: list[dict]) -> None:
    client = bigquery.Client(project=PROJECT)
    table_id = f"{PROJECT}.{DATASET}.{table_name}"
    job_config = bigquery.LoadJobConfig(
        schema=SCHEMAS[table_name],
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    job = client.load_table_from_json(rows, table_id, job_config=job_config)
    job.result()
    print(f"Loaded {len(rows)} rows into {table_id}")
