-- Grain: one row per contact, current state (a type 1 dimension).
--
-- Overwriting is the right default here and it is a real trade-off: when a
-- contact changes email, history is lost. Deals carry the money, so deals get
-- a snapshot and contacts do not. If attribution ever needs "which email did
-- they have when the deal closed", this becomes a type 2 the same way
-- deal_snapshot already is.
SELECT
    contact_id,
    email,
    email_normalised,
    first_name,
    last_name,
    NULLIF(TRIM(CONCAT(COALESCE(first_name, ''), ' ', COALESCE(last_name, ''))), '') AS full_name,
    lead_status,
    lifecycle_stage,
    created_at,
    modified_at
FROM {{ ref('stg_contacts') }}
