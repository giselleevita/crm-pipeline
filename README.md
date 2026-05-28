# CRM Pipeline

![CI](https://github.com/giselleevita/crm-pipeline/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-proprietary-lightgrey)

> HubSpot CRM → BigQuery → Metabase data ingestion pipeline.

Automates contact, deal, company, and activity syncs from HubSpot into BigQuery with dbt transformations and scheduled GitHub Actions runs.

---

## Architecture

```
HubSpot API
    ↓  Python extractor (full + incremental)
BigQuery — raw layer
    ↓  dbt models
BigQuery — transformed layer
    ↓
Metabase — dashboards
```

---

## Features

- **Full + incremental sync** for contacts, deals, companies, and activities
- **Idempotent loads** — safe to re-run without duplicates
- **dbt models** for clean sales funnel and pipeline metrics
- **Scheduled daily runs** via GitHub Actions
- **Slack webhook alerting** on pipeline failure

---

## Repository Structure

```
crm-pipeline/
├── src/                    # Python extractor and loader
├── dbt_models/             # dbt transformation models
├── tests/                  # pytest suite
├── .github/workflows/      # Scheduled CI + pipeline runs
├── data_dictionary.md      # Field definitions for all synced objects
├── .env.example            # Required environment variables
└── requirements.txt
```

---

## Data Model

See [`data_dictionary.md`](./data_dictionary.md) for full field definitions.

Objects synced from HubSpot:

| Object | Sync Mode | Key Fields |
|---|---|---|
| Contacts | Full + incremental | `contact_id`, `email`, `lifecycle_stage`, `owner_id` |
| Deals | Full + incremental | `deal_id`, `deal_stage`, `amount`, `close_date`, `pipeline` |
| Companies | Full | `company_id`, `domain`, `industry`, `num_employees` |
| Activities | Incremental | `activity_id`, `type`, `contact_id`, `deal_id`, `timestamp` |

dbt layers:
- **raw** — direct from HubSpot API, minimal transformation
- **staging** — type casting, null handling, deduplication
- **marts** — sales funnel metrics, pipeline velocity, activity summaries

---

## Quick Start

```bash
git clone https://github.com/giselleevita/crm-pipeline
cd crm-pipeline
pip install -r requirements.txt
cp .env.example .env
# Fill in HUBSPOT_API_KEY, BQ_PROJECT_ID, BQ_DATASET

# Run extractor
python src/extract.py

# Run dbt transformations
dbt run

# Run tests
pytest tests/ -v
```

---

## Requirements

- Python 3.11+
- Google Cloud project with BigQuery enabled and a service account key
- HubSpot private app token
- `dbt-bigquery`

See `.env.example` for all required environment variables.

---

## License

Not licensed for reuse.
