# crm-pipeline

> HubSpot CRM → BigQuery → Metabase data ingestion pipeline

Automates the ingestion of HubSpot CRM data (contacts, deals, companies) into BigQuery and exposes it via Metabase dashboards. Built as a portfolio project mirroring real-world B2B SaaS data engineering workflows.

## Architecture
```
HubSpot REST API
      │
      ▼
hubspot_client.py  (paginated API pull)
      │
      ▼
transform.py       (raw JSON → structured dicts)
      │
      ▼
bigquery_loader.py (schema-enforced BQ load)
      │
      ▼
BigQuery (crm_raw dataset)
      │
      ├── dbt model: deal_stage_summary
      │
      ▼
Metabase (dashboard via Docker)
```

## Setup

```bash
git clone https://github.com/giselleevita/crm-pipeline
cd crm-pipeline
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
python src/pipeline.py
```

## Metabase (local)
```bash
docker run -d -p 3000:3000 --name metabase metabase/metabase
# open http://localhost:3000 → connect BigQuery
```

## Tests
```bash
pytest tests/ -v
```

## Data Dictionary
See [data_dictionary.md](./data_dictionary.md)

## Tech Stack
Python · HubSpot API · Google BigQuery · Metabase · dbt · Docker · GitHub Actions
