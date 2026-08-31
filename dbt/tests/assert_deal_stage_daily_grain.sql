-- A singular test rather than a dbt_utils macro, so the project has no package
-- dependencies and CI can parse it offline. Returns rows only on failure.
SELECT
    snapshot_date,
    stage,
    COUNT(*) AS row_count
FROM {{ ref('fct_deal_stage_daily') }}
GROUP BY snapshot_date, stage
HAVING COUNT(*) > 1
