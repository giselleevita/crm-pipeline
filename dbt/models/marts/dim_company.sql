-- Grain: one row per company, current state.
SELECT
    company_id,
    company_name,
    domain,
    industry,
    country,
    employee_count,
    created_at,
    modified_at
FROM {{ ref('stg_companies') }}
