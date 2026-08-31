SELECT
    object_id                                                              AS company_id,
    JSON_VALUE(payload, '$.properties.name')                               AS company_name,
    LOWER(TRIM(JSON_VALUE(payload, '$.properties.domain')))                AS domain,
    JSON_VALUE(payload, '$.properties.industry')                           AS industry,
    JSON_VALUE(payload, '$.properties.country')                            AS country,
    SAFE_CAST(JSON_VALUE(payload, '$.properties.numberofemployees') AS INT64) AS employee_count,
    SAFE_CAST(JSON_VALUE(payload, '$.properties.createdate') AS TIMESTAMP)  AS created_at,
    hs_lastmodifieddate                                                    AS modified_at,
    ingested_at
FROM {{ source('crm_raw', 'raw_companies') }}
