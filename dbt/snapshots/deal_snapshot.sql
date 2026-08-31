{% snapshot deal_snapshot %}
{{
    config(
        unique_key='deal_id',
        strategy='timestamp',
        updated_at='modified_at',
        invalidate_hard_deletes=False
    )
}}
-- HubSpot holds current state only: ask it what stage a deal was in last month
-- and it cannot tell you. This snapshot is where deal history starts existing,
-- which is what makes a stage-by-day fact possible at all. It only knows about
-- changes since the first run, so the series begins the day this was deployed.
SELECT deal_id, stage, pipeline, amount, close_date, modified_at
FROM {{ ref('stg_deals') }}
{% endsnapshot %}
