"""The SQL that carries the idempotency claim, asserted without a warehouse."""
from warehouse import merge_raw_sql, replace_associations_sql

MERGE = merge_raw_sql("proj.crm_raw.raw_deals", "proj.crm_raw._stg_raw_deals")


def test_merge_keys_on_the_hubspot_object_id():
    assert "ON target.object_id = source.object_id" in MERGE


def test_merge_deduplicates_its_source():
    """A single extract window can contain the same record twice; BigQuery rejects that in a MERGE."""
    assert "ROW_NUMBER() OVER" in MERGE
    assert "PARTITION BY object_id" in MERGE
    assert "WHERE row_rank = 1" in MERGE


def test_merge_refuses_to_move_a_row_backwards():
    assert "WHEN MATCHED AND COALESCE(source.hs_lastmodifieddate, source.ingested_at)" in MERGE
    assert ">= COALESCE(target.hs_lastmodifieddate, target.ingested_at)" in MERGE


def test_association_merge_deletes_only_within_the_current_batch():
    sql = replace_associations_sql("proj.crm_raw.raw_deal_associations", "proj.crm_raw._stg_assoc")

    assert "WHEN NOT MATCHED BY SOURCE" in sql
    assert "target.deal_id IN (SELECT DISTINCT deal_id FROM `proj.crm_raw._stg_assoc`)" in sql
    assert "WHERE to_object_id IS NOT NULL" in sql, "sentinel rows must not be inserted"
