"""Orchestration: what happens to the watermark when a load fails."""
from datetime import UTC, datetime

import pytest

import pipeline


class FakeClient:
    def __init__(self, records=None, associations=None):
        self._records = records or []
        self._associations = associations or {}
        self.association_calls = []

    def search_modified_since(self, object_type, since):
        self.since = since
        yield from self._records

    def read_associations(self, from_type, to_type, ids):
        self.association_calls.append((to_type, list(ids)))
        return {k: v for k, v in self._associations.get(to_type, {}).items() if k in ids}


class FakeWarehouse:
    def __init__(self, fail_on_upsert=False):
        self.fail_on_upsert = fail_on_upsert
        self.upserts = []
        self.association_rows = []

    def upsert_objects(self, object_type, rows):
        if self.fail_on_upsert:
            raise RuntimeError("BigQuery said no")
        self.upserts.append((object_type, rows))
        return len(rows)

    def replace_associations(self, rows):
        self.association_rows.extend(rows)
        return len(rows)


@pytest.fixture
def recorded(monkeypatch):
    """Capture watermark and run-log writes instead of sending them to BigQuery."""
    state = {"watermarks": [], "runs": []}
    monkeypatch.setattr(pipeline, "get_watermark", lambda *a, **k: datetime(2026, 1, 1, tzinfo=UTC))
    monkeypatch.setattr(
        pipeline, "set_watermark", lambda wh, obj, mark: state["watermarks"].append((obj, mark))
    )
    monkeypatch.setattr(
        pipeline,
        "log_run",
        lambda wh, run_id, obj, start, end, rows_extracted, rows_loaded, status, message=None: state[
            "runs"
        ].append({"object": obj, "status": status, "extracted": rows_extracted, "loaded": rows_loaded}),
    )
    return state


def _deal(deal_id, modified="2026-02-01T00:00:00Z"):
    return {"id": deal_id, "properties": {"hs_lastmodifieddate": modified}}


def test_successful_sync_moves_the_watermark_to_the_newest_record(recorded):
    warehouse = FakeWarehouse()
    client = FakeClient(records=[_deal("1"), _deal("2", "2026-03-05T00:00:00Z")])

    loaded = pipeline._sync_object("deals", client, warehouse, "run-1", lookback_minutes=5)

    assert loaded == 2
    assert recorded["watermarks"] == [("deals", datetime(2026, 3, 5, tzinfo=UTC))]
    assert recorded["runs"][0]["status"] == "success"


def test_failed_load_leaves_the_watermark_where_it_was(recorded):
    """Moving it first would mean the next run starts after records that were never loaded."""
    warehouse = FakeWarehouse(fail_on_upsert=True)
    client = FakeClient(records=[_deal("1")])

    with pytest.raises(RuntimeError, match="BigQuery said no"):
        pipeline._sync_object("deals", client, warehouse, "run-1", lookback_minutes=5)

    assert recorded["watermarks"] == []
    assert recorded["runs"][0]["status"] == "failed"


def test_empty_extract_is_recorded_as_empty_not_success(recorded):
    pipeline._sync_object("deals", FakeClient(records=[]), FakeWarehouse(), "run-1", 5)

    assert recorded["runs"][0]["status"] == "empty"
    assert recorded["watermarks"] == []


def test_deals_without_associations_are_still_sent_to_the_load(recorded):
    warehouse = FakeWarehouse()
    client = FakeClient(
        records=[_deal("1"), _deal("2")],
        associations={"companies": {"1": ["c1"]}, "contacts": {}},
    )

    pipeline._sync_object("deals", client, warehouse, "run-1", 5)

    company_rows = [row for row in warehouse.association_rows if row["to_object_type"] == "companies"]
    assert {row["deal_id"]: row["to_object_id"] for row in company_rows} == {"1": "c1", "2": None}


def test_contacts_do_not_trigger_association_calls(recorded):
    client = FakeClient(records=[{"id": "1", "properties": {"lastmodifieddate": "2026-02-01T00:00:00Z"}}])

    pipeline._sync_object("contacts", client, FakeWarehouse(), "run-1", 5)

    assert client.association_calls == []
