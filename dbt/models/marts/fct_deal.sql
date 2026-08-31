-- Grain: one row per deal.
--
-- Chosen because every commercial question asked of this table -- pipeline
-- value, win rate, average deal size -- counts deals, and a grain of one row
-- per deal-contact link would silently multiply the amount by the number of
-- contacts attached. The links that grain would have given us live in
-- bridge_deal_company instead.
WITH companies AS (
    SELECT
        deal_id,
        -- Deterministic, not arbitrary: the same deal resolves to the same
        -- company on every run. Documented as a simplification, not a fact
        -- about the business.
        MIN(associated_object_id) AS primary_company_id,
        COUNT(DISTINCT associated_object_id) AS company_count
    FROM {{ ref('stg_deal_associations') }}
    WHERE associated_object_type = 'companies'
    GROUP BY deal_id
),

contacts AS (
    SELECT
        deal_id,
        MIN(associated_object_id) AS primary_contact_id,
        COUNT(DISTINCT associated_object_id) AS contact_count
    FROM {{ ref('stg_deal_associations') }}
    WHERE associated_object_type = 'contacts'
    GROUP BY deal_id
)

SELECT
    deals.deal_id,
    deals.deal_name,
    deals.stage,
    deals.pipeline,
    deals.amount,
    deals.created_at,
    deals.close_date,
    deals.modified_at,
    companies.primary_company_id,
    contacts.primary_contact_id,
    COALESCE(companies.company_count, 0) AS company_count,
    COALESCE(contacts.contact_count, 0) AS contact_count,
    deals.close_date IS NOT NULL AND deals.close_date <= CURRENT_TIMESTAMP() AS is_closed
FROM {{ ref('stg_deals') }} AS deals
LEFT JOIN companies USING (deal_id)
LEFT JOIN contacts USING (deal_id)
