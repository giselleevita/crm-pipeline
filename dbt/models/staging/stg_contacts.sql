-- Cleaning and typing only. No business logic, so that anything surprising in
-- a mart can always be traced back to the source rather than to this layer.
SELECT
    object_id                                                            AS contact_id,
    JSON_VALUE(payload, '$.properties.email')                            AS email,
    LOWER(TRIM(JSON_VALUE(payload, '$.properties.email')))               AS email_normalised,
    JSON_VALUE(payload, '$.properties.firstname')                        AS first_name,
    JSON_VALUE(payload, '$.properties.lastname')                         AS last_name,
    JSON_VALUE(payload, '$.properties.hs_lead_status')                   AS lead_status,
    JSON_VALUE(payload, '$.properties.lifecyclestage')                   AS lifecycle_stage,
    SAFE_CAST(JSON_VALUE(payload, '$.properties.createdate') AS TIMESTAMP) AS created_at,
    hs_lastmodifieddate                                                  AS modified_at,
    ingested_at
FROM {{ source('crm_raw', 'raw_contacts') }}
