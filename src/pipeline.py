"""Entrypoint: extract changed HubSpot records into the raw warehouse layer.

One object type at a time, each one bracketed by a row in pipeline_runs. An
object that fails is recorded as failed and stops the run, so the transform
step downstream never gets to build marts on a half-loaded raw layer.
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import UTC, datetime

from config import load_config
from hubspot_client import HubSpotClient
from raw_records import max_modified_at, to_association_rows, to_raw_rows
from state import get_watermark, log_run, new_run_id, set_watermark
from warehouse import Warehouse

OBJECT_TYPES = ("contacts", "companies", "deals")

logger = logging.getLogger("pipeline")


def _sync_object(
    object_type: str,
    client: HubSpotClient,
    warehouse: Warehouse,
    run_id: str,
    lookback_minutes: int,
) -> int:
    started_at = datetime.now(UTC)
    since = get_watermark(warehouse, object_type, lookback_minutes)
    logger.info("%s: extracting records modified since %s", object_type, since.isoformat())

    try:
        records = list(client.search_modified_since(object_type, since))
        ingested_at = datetime.now(UTC)
        rows = to_raw_rows(object_type, records, ingested_at)
        loaded = warehouse.upsert_objects(object_type, rows)

        if object_type == "deals" and records:
            _sync_deal_associations(client, warehouse, [str(r["id"]) for r in records], ingested_at)

        # Watermark last, and only from records that actually landed.
        high_water = max_modified_at(rows)
        if high_water:
            set_watermark(warehouse, object_type, high_water)
    except Exception as exc:  # noqa: BLE001 - recorded, then re-raised
        log_run(
            warehouse,
            run_id,
            object_type,
            started_at,
            datetime.now(UTC),
            rows_extracted=0,
            rows_loaded=0,
            status="failed",
            message=str(exc)[:1000],
        )
        raise

    log_run(
        warehouse,
        run_id,
        object_type,
        started_at,
        datetime.now(UTC),
        rows_extracted=len(records),
        rows_loaded=loaded,
        status="success" if loaded else "empty",
    )
    logger.info("%s: %s extracted, %s loaded", object_type, len(records), loaded)
    return loaded


def _sync_deal_associations(
    client: HubSpotClient, warehouse: Warehouse, deal_ids: list[str], ingested_at: datetime
) -> None:
    for to_type in ("companies", "contacts"):
        found = client.read_associations("deals", to_type, deal_ids)
        # Deals HubSpot returns nothing for are deals with no links. They still
        # need a row in the batch so the load can remove links that were deleted.
        complete = {deal_id: found.get(deal_id, []) for deal_id in deal_ids}
        warehouse.replace_associations(to_association_rows(complete, to_type, ingested_at))


def run(objects: tuple[str, ...] = OBJECT_TYPES, fail_on_empty: bool = False) -> int:
    config = load_config()

    from google.cloud import bigquery

    warehouse = Warehouse(
        client=bigquery.Client(project=config.gcp_project),
        project=config.gcp_project,
        dataset=config.dataset,
    )
    warehouse.ensure_tables()

    client = HubSpotClient(
        token=config.hubspot_token,
        max_retries=config.max_retries,
        page_size=config.page_size,
    )

    run_id = new_run_id()
    logger.info("run %s starting for %s", run_id, ", ".join(objects))
    total = sum(
        _sync_object(object_type, client, warehouse, run_id, config.lookback_minutes)
        for object_type in objects
    )

    if total == 0:
        # An incremental run legitimately loads nothing when nothing changed,
        # so this is a warning by default. In an environment where silence is
        # always wrong, --fail-on-empty turns it into a failed build.
        logger.warning("run %s loaded zero rows across every object type", run_id)
        if fail_on_empty:
            return 1
    logger.info("run %s complete, %s rows loaded", run_id, total)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync HubSpot CRM objects into BigQuery.")
    parser.add_argument(
        "--objects",
        nargs="+",
        choices=OBJECT_TYPES,
        default=list(OBJECT_TYPES),
        help="Object types to sync (default: all).",
    )
    parser.add_argument(
        "--fail-on-empty",
        action="store_true",
        help="Exit non-zero when a run loads no rows at all.",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    return run(tuple(args.objects), fail_on_empty=args.fail_on_empty)


if __name__ == "__main__":
    sys.exit(main())
