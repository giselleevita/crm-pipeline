# Data Dictionary — crm-pipeline

## Table: `crm_raw.contacts`
| Column | Type | Description |
|--------|------|-------------|
| id | STRING | HubSpot contact ID |
| firstname | STRING | First name |
| lastname | STRING | Last name |
| email | STRING | Primary email address |
| lead_status | STRING | HubSpot lead status (NEW, OPEN, IN_PROGRESS, etc.) |
| created_at | TIMESTAMP | Record creation time in HubSpot |
| ingested_at | TIMESTAMP | Pipeline ingestion timestamp (UTC) |

## Table: `crm_raw.deals`
| Column | Type | Description |
|--------|------|-------------|
| id | STRING | HubSpot deal ID |
| deal_name | STRING | Name of the deal |
| amount | FLOAT | Deal value in account currency |
| stage | STRING | Current deal stage |
| pipeline | STRING | Pipeline the deal belongs to |
| close_date | TIMESTAMP | Expected or actual close date |
| created_at | TIMESTAMP | Record creation time in HubSpot |
| ingested_at | TIMESTAMP | Pipeline ingestion timestamp (UTC) |

## Table: `crm_raw.companies`
| Column | Type | Description |
|--------|------|-------------|
| id | STRING | HubSpot company ID |
| name | STRING | Company name |
| domain | STRING | Website domain |
| industry | STRING | Industry classification |
| country | STRING | Country code |
| employees | INTEGER | Number of employees |
| created_at | TIMESTAMP | Record creation time in HubSpot |
| ingested_at | TIMESTAMP | Pipeline ingestion timestamp (UTC) |

## dbt model: `deal_stage_summary`
| Column | Type | Description |
|--------|------|-------------|
| stage | STRING | Deal stage name |
| pipeline | STRING | Pipeline name |
| deal_count | INTEGER | Number of deals in this stage |
| total_value | FLOAT | Sum of deal amounts |
| avg_deal_value | FLOAT | Average deal amount |
