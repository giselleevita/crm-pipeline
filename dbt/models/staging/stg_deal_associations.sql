SELECT
    deal_id,
    to_object_type AS associated_object_type,
    to_object_id   AS associated_object_id,
    ingested_at
FROM {{ source('crm_raw', 'raw_deal_associations') }}
