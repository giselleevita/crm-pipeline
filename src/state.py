"""Watermarks and run history: the pipeline's own control tables.

Watermarks answer "where did we get to", run history answers "did last night
work". Both live in the warehouse rather than on disk, because the process that
writes them is a container that will not exist tomorrow.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from warehouse import RUNS_TABLE, STATE_TABLE, Warehouse

# First run for an object has no watermark. Rather than pulling all of history
# on an unbounded query, start from a fixed floor and let the operator move it.
DEFAULT_BACKFILL_DAYS = 365


def _scalar(client, sql: str, params: list | None = None):
    from google.cloud import bigquery

    job_config = bigquery.QueryJobConfig(query_parameters=params or [])
    rows = list(client.query(sql, job_config=job_config).result())
    return rows[0][0] if rows else None


def get_watermark(warehouse: Warehouse, object_type: str, lookback_minutes: int) -> datetime:
    """Where the next extract should start.

    The lookback is subtracted here rather than when the watermark is written,
    so the stored value stays an honest record of what was loaded.
    """
    from google.cloud import bigquery

    stored = _scalar(
        warehouse.client,
        f"SELECT watermark FROM `{warehouse.table_id(STATE_TABLE)}` WHERE object_type = @object_type",
        [bigquery.ScalarQueryParameter("object_type", "STRING", object_type)],
    )
    if stored is None:
        return datetime.now(UTC) - timedelta(days=DEFAULT_BACKFILL_DAYS)
    return stored - timedelta(minutes=lookback_minutes)


def watermark_merge_sql(table: str) -> str:
    return f"""
    MERGE `{table}` AS target
    USING (SELECT @object_type AS object_type, @watermark AS watermark) AS source
    ON target.object_type = source.object_type
    WHEN MATCHED THEN UPDATE SET watermark = source.watermark, updated_at = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN
        INSERT (object_type, watermark, updated_at)
        VALUES (source.object_type, source.watermark, CURRENT_TIMESTAMP())
    """.strip()


def run_insert_sql(table: str) -> str:
    return f"""
    INSERT INTO `{table}`
        (run_id, object_type, started_at, ended_at, rows_extracted, rows_loaded, status, message)
    VALUES (@run_id, @object_type, @started_at, @ended_at, @rows_extracted, @rows_loaded, @status, @message)
    """.strip()


def set_watermark(warehouse: Warehouse, object_type: str, watermark: datetime) -> None:
    """Write the watermark forward.

    Called only after the load for that object has succeeded. Writing it before
    the load would mean a failed load silently skips the records it dropped:
    the next run starts after them and nothing ever reports them missing.
    """
    from google.cloud import bigquery

    warehouse.client.query(
        watermark_merge_sql(warehouse.table_id(STATE_TABLE)),
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("object_type", "STRING", object_type),
                bigquery.ScalarQueryParameter("watermark", "TIMESTAMP", watermark),
            ]
        ),
    ).result()


def new_run_id() -> str:
    return uuid.uuid4().hex


def log_run(
    warehouse: Warehouse,
    run_id: str,
    object_type: str,
    started_at: datetime,
    ended_at: datetime | None,
    rows_extracted: int,
    rows_loaded: int,
    status: str,
    message: str | None = None,
) -> None:
    from google.cloud import bigquery

    warehouse.client.query(
        run_insert_sql(warehouse.table_id(RUNS_TABLE)),
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("run_id", "STRING", run_id),
                bigquery.ScalarQueryParameter("object_type", "STRING", object_type),
                bigquery.ScalarQueryParameter("started_at", "TIMESTAMP", started_at),
                bigquery.ScalarQueryParameter("ended_at", "TIMESTAMP", ended_at),
                bigquery.ScalarQueryParameter("rows_extracted", "INT64", rows_extracted),
                bigquery.ScalarQueryParameter("rows_loaded", "INT64", rows_loaded),
                bigquery.ScalarQueryParameter("status", "STRING", status),
                bigquery.ScalarQueryParameter("message", "STRING", message),
            ]
        ),
    ).result()
