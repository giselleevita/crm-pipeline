-- Every association must point at a deal we actually hold. If this fails the
-- extractor loaded links for deals it never landed, which means the deal load
-- and the association load have drifted out of step.
SELECT associations.deal_id
FROM {{ ref('stg_deal_associations') }} AS associations
LEFT JOIN {{ ref('stg_deals') }} AS deals USING (deal_id)
WHERE deals.deal_id IS NULL
