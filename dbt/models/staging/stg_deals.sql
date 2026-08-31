SELECT
    object_id                                                             AS deal_id,
    JSON_VALUE(payload, '$.properties.dealname')                          AS deal_name,
    -- SAFE_CAST rather than CAST: one malformed amount should surface as a
    -- failing test on a null, not as a failed build for the whole layer.
    SAFE_CAST(JSON_VALUE(payload, '$.properties.amount') AS NUMERIC)      AS amount,
    JSON_VALUE(payload, '$.properties.dealstage')                         AS stage,
    JSON_VALUE(payload, '$.properties.pipeline')                          AS pipeline,
    SAFE_CAST(JSON_VALUE(payload, '$.properties.closedate') AS TIMESTAMP) AS close_date,
    SAFE_CAST(JSON_VALUE(payload, '$.properties.createdate') AS TIMESTAMP) AS created_at,
    hs_lastmodifieddate                                                   AS modified_at,
    ingested_at
FROM {{ source('crm_raw', 'raw_deals') }}
