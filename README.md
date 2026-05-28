# crm-pipeline

HubSpot CRM → BigQuery → Metabase data ingestion pipeline. Automates contact, deal, and activity syncs with dbt transformations and GitHub Actions scheduling.

## Architecture

```
HubSpot API
    ↓ (Python extractor)
BigQuery (raw layer)
    ↓ (dbt models)
BigQuery (transformed layer)
    ↓
Metabase (dashboards)
```

## Features

- Full + incremental sync modes (contacts, deals, companies, activities)
- dbt models for clean sales funnel and pipeline metrics
- GitHub Actions workflow for scheduled daily runs
- Error alerting via Slack webhook on pipeline failure
- Idempotent loads — safe to re-run without duplicates

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in HUBSPOT_API_KEY, BQ_PROJECT_ID, BQ_DATASET
python pipeline/extract.py
dbt run
```

## Requirements

- Python 3.11+
- Google Cloud project with BigQuery enabled
- HubSpot private app token
- dbt-bigquery

## License

Not licensed for reuse.
