"""The landing envelope: what we store, and what the watermark is derived from."""
import json
from datetime import UTC, datetime

from raw_records import max_modified_at, to_association_rows, to_raw_rows

INGESTED = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)


def test_payload_is_stored_exactly_as_received():
    record = {"id": "1", "properties": {"dealname": "Big", "hs_lastmodifieddate": "2026-04-01T00:00:00Z"}}

    row = to_raw_rows("deals", [record], INGESTED)[0]

    assert json.loads(row["payload"]) == record
    assert row["object_id"] == "1"
    assert row["hs_lastmodifieddate"] == "2026-04-01T00:00:00Z"
    assert row["ingested_at"] == INGESTED.isoformat()


def test_epoch_millis_modification_times_are_normalised():
    record = {"id": "1", "properties": {"hs_lastmodifieddate": "1767225600000"}}

    row = to_raw_rows("deals", [record], INGESTED)[0]

    assert row["hs_lastmodifieddate"].startswith("2026-01-01")


def test_envelope_updated_at_is_used_when_the_property_is_absent():
    record = {"id": "1", "properties": {}, "updatedAt": "2026-02-02T10:00:00Z"}

    assert to_raw_rows("deals", [record], INGESTED)[0]["hs_lastmodifieddate"] == "2026-02-02T10:00:00Z"


def test_deal_with_no_associations_still_produces_a_row():
    """Without this row the load has nothing to tell it a link was removed."""
    rows = to_association_rows({"1": ["c1"], "2": []}, "companies", INGESTED)

    assert {"deal_id": "1", "to_object_type": "companies", "to_object_id": "c1", "ingested_at": INGESTED.isoformat()} in rows
    sentinel = [row for row in rows if row["deal_id"] == "2"]
    assert len(sentinel) == 1
    assert sentinel[0]["to_object_id"] is None


def test_watermark_is_the_newest_record_actually_landed():
    rows = to_raw_rows(
        "deals",
        [
            {"id": "1", "properties": {"hs_lastmodifieddate": "2026-04-01T00:00:00Z"}},
            {"id": "2", "properties": {"hs_lastmodifieddate": "2026-06-01T00:00:00Z"}},
        ],
        INGESTED,
    )

    assert max_modified_at(rows) == datetime(2026, 6, 1, tzinfo=UTC)


def test_watermark_is_none_when_nothing_landed():
    assert max_modified_at([]) is None
