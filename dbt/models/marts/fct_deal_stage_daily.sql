-- Grain: one row per calendar day per stage.
--
-- Built from the snapshot rather than from current state, because the question
-- this answers is "what did the pipeline look like on the 14th", and current
-- state can only ever answer "what does it look like now".
WITH history AS (
    SELECT
        deal_id,
        stage,
        amount,
        DATE(dbt_valid_from) AS valid_from,
        DATE(COALESCE(dbt_valid_to, CURRENT_TIMESTAMP())) AS valid_to,
        dbt_valid_from
    FROM {{ ref('deal_snapshot') }}
),

bounds AS (
    SELECT MIN(valid_from) AS first_day FROM history
),

spine AS (
    SELECT day
    FROM bounds, UNNEST(GENERATE_DATE_ARRAY(bounds.first_day, CURRENT_DATE())) AS day
),

deal_state_per_day AS (
    SELECT
        spine.day AS snapshot_date,
        history.deal_id,
        history.stage,
        history.amount
    FROM spine
    INNER JOIN history
        ON spine.day >= history.valid_from
        AND spine.day <= history.valid_to
    -- A deal changed twice in one day has two valid versions that day. Keep
    -- the last one, so the daily count stays one row per deal.
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY spine.day, history.deal_id
        ORDER BY history.dbt_valid_from DESC
    ) = 1
)

SELECT
    snapshot_date,
    stage,
    COUNT(*) AS deal_count,
    SUM(amount) AS total_value,
    AVG(amount) AS avg_deal_value
FROM deal_state_per_day
GROUP BY snapshot_date, stage
