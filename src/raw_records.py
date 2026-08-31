"""Turn HubSpot API records into the envelope we land in the warehouse.

Deliberately thin. The payload is stored exactly as HubSpot returned it and
every field beyond the ones needed to load and de-duplicate a row is left for
dbt to pull out. Two reasons:

* a new HubSpot property becomes a SQL change, not a Python change and a backfill
* a parsing mistake is recoverable, because the source of truth is still in the row
"""
from __future__ import annotations

import json
from datetime import UTC, datetime

from hubspot_client import MODIFIED_PROPERTY


def _modified_at(record: dict, object_type: str) -> str | None:
    value = record.get("properties", {}).get(MODIFIED_PROPERTY[object_type])
    if not value:
        # Fall back to the envelope field the CRM API returns alongside properties.
        value = record.get("updatedAt")
    if not value:
        return None
    if isinstance(value, str) and value.isdigit():
        return datetime.fromtimestamp(int(value) / 1000, tz=UTC).isoformat()
    return value


def to_raw_rows(object_type: str, records: list[dict], ingested_at: datetime) -> list[dict]:
    ingested = ingested_at.isoformat()
    return [
        {
            "object_id": str(record["id"]),
            "payload": json.dumps(record, separators=(",", ":"), sort_keys=True),
            "hs_lastmodifieddate": _modified_at(record, object_type),
            "ingested_at": ingested,
        }
        for record in records
    ]


def to_association_rows(
    associations: dict[str, list[str]], to_object_type: str, ingested_at: datetime
) -> list[dict]:
    ingested = ingested_at.isoformat()
    rows: list[dict] = []
    for deal_id, targets in sorted(associations.items()):
        if not targets:
            # A deal we looked at that has no links left. The null target is
            # what lets the load delete the association it used to have.
            rows.append(
                {
                    "deal_id": deal_id,
                    "to_object_type": to_object_type,
                    "to_object_id": None,
                    "ingested_at": ingested,
                }
            )
            continue
        rows.extend(
            {
                "deal_id": deal_id,
                "to_object_type": to_object_type,
                "to_object_id": target_id,
                "ingested_at": ingested,
            }
            for target_id in targets
        )
    return rows


def max_modified_at(rows: list[dict]) -> datetime | None:
    """The high-water mark for a batch: the newest modification time we actually landed."""
    stamps = [
        datetime.fromisoformat(row["hs_lastmodifieddate"].replace("Z", "+00:00"))
        for row in rows
        if row.get("hs_lastmodifieddate")
    ]
    return max(stamps) if stamps else None
