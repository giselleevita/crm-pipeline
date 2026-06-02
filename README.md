# CRM Pipeline

![CI](https://github.com/giselleevita/crm-pipeline/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-proprietary-lightgrey)

> Secure HubSpot CRM → BigQuery → Metabase data ingestion pipeline — built with credential isolation, idempotent loads, least-privilege service accounts, and audit-ready dbt transformations.

Automates contact, deal, company, and activity syncs from HubSpot into BigQuery. Credentials are scoped to minimum required permissions; all pipeline runs are logged and alertable.

For the hiring-focused project narrative, see [docs/CASE_STUDY.md](docs/CASE_STUDY.md).

---

## Architecture

```
HubSpot API  (private app token, scoped read-only)
    ↓  Python extractor (full + incremental)
BigQuery — raw layer  (service account: BQ Data Editor only)
    ↓  dbt models
BigQuery — transformed layer
    ↓
Metabase — dashboards  (service account: BQ Data Viewer only)
```

**Security controls built in:**
- HubSpot private app token (not OAuth, no user delegation)
- BigQuery service account with least-privilege IAM roles per layer
- No credentials in code — all via environment variables / Secret Manager
- Slack alerting on pipeline failure for operational visibility
- Idempotent loads — safe to re-run without data duplication

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
├── .env.example            # Required environment variables (no secrets)
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
# Fill in HUBSPOT_API_KEY, BQ_PROJECT_ID, BQ_DATASET, GCP_SERVICE_ACCOUNT_KEY

# Run extractor
python src/extract.py

# Run dbt transformations
dbt run

# Run tests
pytest tests/ -v
```

---

## Credential Setup

| Secret | Where to set | Minimum scope |
|---|---|---|
| `HUBSPOT_API_KEY` | GitHub Actions secret / `.env` | CRM read-only |
| `GCP_SERVICE_ACCOUNT_KEY` | GitHub Actions secret / `.env` | `roles/bigquery.dataEditor` on dataset only |
| `SLACK_WEBHOOK_URL` | GitHub Actions secret / `.env` | Incoming webhook only |

Never commit credentials. Use `.env.example` as a template.

---

## Requirements

- Python 3.11+
- Google Cloud project with BigQuery enabled and a service account key
- HubSpot private app token
- `dbt-bigquery`

---

## License

Not licensed for reuse.
