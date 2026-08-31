-- Grain: one row per deal-company link.
--
-- HubSpot allows a deal to be associated with more than one company. Rather
-- than pretend otherwise, the many-to-many lives here and fct_deal carries a
-- single primary key chosen by an explicit rule. Anyone who needs the full
-- picture joins this instead.
SELECT
    deal_id,
    associated_object_id AS company_id
FROM {{ ref('stg_deal_associations') }}
WHERE associated_object_type = 'companies'
