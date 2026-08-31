# Data Dictionary — crm-pipeline

Three layers. Raw is what HubSpot said, staging is that parsed and typed, marts
are what a commercial team queries.

## Raw layer (`crm_raw`)

Landed by the Python extractor. The payload is the exact JSON HubSpot returned,
stored as text so that a new or renamed property never fails a load.

### `raw_contacts`, `raw_companies`, `raw_deals`
| Column | Type | Description |
|---|---|---|
| object_id | STRING | HubSpot object id. Upsert key. |
| payload | STRING | Unmodified JSON response for the object. |
| hs_lastmodifieddate | TIMESTAMP | Source modification time. Drives the watermark. |
| ingested_at | TIMESTAMP | When this row was written. |

### `raw_deal_associations`
| Column | Type | Description |
|---|---|---|
| deal_id | STRING | HubSpot deal id. |
| to_object_type | STRING | `companies` or `contacts`. |
| to_object_id | STRING | Associated object id. |
| ingested_at | TIMESTAMP | When this row was written. |

### Control tables
`pipeline_state` holds one watermark per object type: `object_type`,
`watermark`, `updated_at`. `pipeline_runs` holds one row per object per run:
`run_id`, `object_type`, `started_at`, `ended_at`, `rows_extracted`,
`rows_loaded`, `status` (`success`, `empty`, `failed`), `message`.

## Staging layer (views)

`stg_contacts`, `stg_companies`, `stg_deals`, `stg_deal_associations`. One view
per raw table: JSON unnested into typed columns, HubSpot property names renamed,
timestamps cast. No business logic.

## Marts layer (tables)

### `dim_contact` — one row per contact, current state
`contact_id`, `email`, `email_normalised`, `first_name`, `last_name`,
`full_name`, `lead_status`, `lifecycle_stage`, `created_at`, `modified_at`.

Type 1: an email change overwrites. See the README trade-off section.

### `dim_company` — one row per company, current state
`company_id`, `company_name`, `domain`, `industry`, `country`,
`employee_count`, `created_at`, `modified_at`.

### `fct_deal` — one row per deal
`deal_id`, `deal_name`, `stage`, `pipeline`, `amount`, `created_at`,
`close_date`, `modified_at`, `primary_company_id`, `primary_contact_id`,
`company_count`, `contact_count`, `is_closed`.

`primary_company_id` is the lowest associated company id. Deals with more than
one company are visible through `company_count` and resolved fully in
`bridge_deal_company`.

### `bridge_deal_company` — one row per deal-company link
`deal_id`, `company_id`.

### `fct_deal_stage_daily` — one row per day per stage
`snapshot_date`, `stage`, `deal_count`, `total_value`, `avg_deal_value`.

Built from `deal_snapshot`, so the series starts the day the snapshot first ran.

### `deal_snapshot` — slowly changing dimension, type 2
`deal_id`, `stage`, `pipeline`, `amount`, `close_date`, `modified_at`, plus
dbt's `dbt_valid_from` and `dbt_valid_to`. This is where deal history lives:
HubSpot itself only holds current state.
