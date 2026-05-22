-- dbt model: deal stage aggregation
SELECT
    stage,
    pipeline,
    COUNT(*)          AS deal_count,
    SUM(SAFE_CAST(amount AS FLOAT64)) AS total_value,
    AVG(SAFE_CAST(amount AS FLOAT64)) AS avg_deal_value
FROM {{ source('crm_raw', 'deals') }}
WHERE stage IS NOT NULL
GROUP BY stage, pipeline
ORDER BY total_value DESC
