"""BigQuery access: schemas, idempotent loads, and the SQL that makes them idempotent.

The BigQuery client is injected rather than constructed here so the SQL this
module generates can be tested without a warehouse or credentials.
"""
from __future__ import annotations

from dataclasses import dataclass

RAW_OBJECT_SCHEMA = [
    ("object_id", "STRING", "REQUIRED"),
    ("payload", "STRING", "REQUIRED"),
    ("hs_lastmodifieddate", "TIMESTAMP", "NULLABLE"),
    ("ingested_at", "TIMESTAMP", "REQUIRED"),
]

ASSOCIATION_SCHEMA = [
    ("deal_id", "STRING", "REQUIRED"),
    ("to_object_type", "STRING", "REQUIRED"),
    ("to_object_id", "STRING", "REQUIRED"),
    ("ingested_at", "TIMESTAMP", "REQUIRED"),
]

# The staging copy allows a null target so that a deal whose last association
# was removed still arrives in the batch. Without that row there is nothing to
# tell the MERGE that the deal was looked at and found to have no links left.
ASSOCIATION_STAGING_SCHEMA = [
    ("deal_id", "STRING", "REQUIRED"),
    ("to_object_type", "STRING", "REQUIRED"),
    ("to_object_id", "STRING", "NULLABLE"),
    ("ingested_at", "TIMESTAMP", "REQUIRED"),
]

STATE_SCHEMA = [
    ("object_type", "STRING", "REQUIRED"),
    ("watermark", "TIMESTAMP", "REQUIRED"),
    ("updated_at", "TIMESTAMP", "REQUIRED"),
]

RUNS_SCHEMA = [
    ("run_id", "STRING", "REQUIRED"),
    ("object_type", "STRING", "REQUIRED"),
    ("started_at", "TIMESTAMP", "REQUIRED"),
    ("ended_at", "TIMESTAMP", "NULLABLE"),
    ("rows_extracted", "INTEGER", "NULLABLE"),
    ("rows_loaded", "INTEGER", "NULLABLE"),
    ("status", "STRING", "REQUIRED"),
    ("message", "STRING", "NULLABLE"),
]

RAW_TABLES = {
    "contacts": "raw_contacts",
    "companies": "raw_companies",
    "deals": "raw_deals",
}

ASSOCIATION_TABLE = "raw_deal_associations"
STATE_TABLE = "pipeline_state"
RUNS_TABLE = "pipeline_runs"

# Staging tables are only alive for the duration of a MERGE. The expiry is a
# backstop for the case where the process dies between load and drop.
STAGING_EXPIRY_HOURS = 6


def merge_raw_sql(target: str, staging: str) -> str:
    """Upsert on the HubSpot object id.

    Two details carry the idempotency:

    * the source is de-duplicated first, because a single extract window can
      contain the same record twice and BigQuery rejects a MERGE whose source
      matches a target row more than once
    * an update only applies when the incoming record is not older than the
      stored one, so a re-read of an overlap window cannot move a row backwards
    """
    return f"""
MERGE `{target}` AS target
USING (
    SELECT object_id, payload, hs_lastmodifieddate, ingested_at
    FROM (
        SELECT
            *,
            ROW_NUMBER() OVER (
                PARTITION BY object_id
                ORDER BY hs_lastmodifieddate DESC NULLS LAST, ingested_at DESC
            ) AS row_rank
        FROM `{staging}`
    )
    WHERE row_rank = 1
) AS source
ON target.object_id = source.object_id
WHEN MATCHED AND COALESCE(source.hs_lastmodifieddate, source.ingested_at)
              >= COALESCE(target.hs_lastmodifieddate, target.ingested_at)
    THEN UPDATE SET
        payload = source.payload,
        hs_lastmodifieddate = source.hs_lastmodifieddate,
        ingested_at = source.ingested_at
WHEN NOT MATCHED THEN
    INSERT (object_id, payload, hs_lastmodifieddate, ingested_at)
    VALUES (source.object_id, source.payload, source.hs_lastmodifieddate, source.ingested_at)
""".strip()


def replace_associations_sql(target: str, staging: str) -> str:
    """Associations are replaced per deal, not merged.

    A deal that loses a company association has no row to update, so a merge
    would leave the stale link in place. Deleting the deal's rows and
    re-inserting the current set is the only version of this that is correct.
    """
    return f"""
MERGE `{target}` AS target
USING (
    SELECT DISTINCT deal_id, to_object_type, to_object_id, ingested_at
    FROM `{staging}`
    WHERE to_object_id IS NOT NULL
) AS source
ON target.deal_id = source.deal_id
   AND target.to_object_type = source.to_object_type
   AND target.to_object_id = source.to_object_id
WHEN MATCHED THEN UPDATE SET ingested_at = source.ingested_at
WHEN NOT MATCHED THEN
    INSERT (deal_id, to_object_type, to_object_id, ingested_at)
    VALUES (source.deal_id, source.to_object_type, source.to_object_id, source.ingested_at)
WHEN NOT MATCHED BY SOURCE
     AND target.deal_id IN (SELECT DISTINCT deal_id FROM `{staging}`)
     AND target.to_object_type IN (SELECT DISTINCT to_object_type FROM `{staging}`)
    THEN DELETE
""".strip()


@dataclass
class Warehouse:
    client: object
    project: str
    dataset: str

    def table_id(self, name: str) -> str:
        return f"{self.project}.{self.dataset}.{name}"

    # ------------------------------------------------------------------ DDL

    def ensure_tables(self) -> None:
        from google.cloud import bigquery

        self.client.create_dataset(
            bigquery.Dataset(f"{self.project}.{self.dataset}"), exists_ok=True
        )
        for name in RAW_TABLES.values():
            self._create(name, RAW_OBJECT_SCHEMA)
        self._create(ASSOCIATION_TABLE, ASSOCIATION_SCHEMA)
        self._create(STATE_TABLE, STATE_SCHEMA)
        self._create(RUNS_TABLE, RUNS_SCHEMA)

    def _create(self, name: str, schema: list[tuple[str, str, str]]) -> None:
        from google.cloud import bigquery

        table = bigquery.Table(
            self.table_id(name),
            schema=[bigquery.SchemaField(f, t, mode=m) for f, t, m in schema],
        )
        self.client.create_table(table, exists_ok=True)

    # ------------------------------------------------------------------ DML

    def _load_staging(self, name: str, schema, rows: list[dict]) -> str:
        from datetime import UTC, datetime, timedelta

        from google.cloud import bigquery

        staging_id = self.table_id(f"_stg_{name}")
        table = bigquery.Table(
            staging_id, schema=[bigquery.SchemaField(f, t, mode=m) for f, t, m in schema]
        )
        table.expires = datetime.now(UTC) + timedelta(hours=STAGING_EXPIRY_HOURS)
        self.client.create_table(table, exists_ok=True)

        job = self.client.load_table_from_json(
            rows,
            staging_id,
            job_config=bigquery.LoadJobConfig(
                schema=table.schema,
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            ),
        )
        job.result()
        return staging_id

    def upsert_objects(self, object_type: str, rows: list[dict]) -> int:
        if not rows:
            return 0
        target = RAW_TABLES[object_type]
        staging_id = self._load_staging(target, RAW_OBJECT_SCHEMA, rows)
        try:
            self.client.query(merge_raw_sql(self.table_id(target), staging_id)).result()
        finally:
            self.client.delete_table(staging_id, not_found_ok=True)
        return len(rows)

    def replace_associations(self, rows: list[dict]) -> int:
        if not rows:
            return 0
        staging_id = self._load_staging(ASSOCIATION_TABLE, ASSOCIATION_STAGING_SCHEMA, rows)
        try:
            self.client.query(
                replace_associations_sql(self.table_id(ASSOCIATION_TABLE), staging_id)
            ).result()
        finally:
            self.client.delete_table(staging_id, not_found_ok=True)
        return len(rows)
