# Architecture

## Current Data Flow

```mermaid
flowchart LR
    Schedule[GitHub Actions schedule or manual run] --> Pipeline[Python pipeline]
    Pipeline --> HubSpot[HubSpot CRM API]
    HubSpot --> Extract[Paginated object extraction]
    Extract --> Transform[Typed field transformations]
    Transform --> Load[BigQuery JSON load jobs]
    Load --> Raw[Contacts, deals, and companies raw tables]
    Raw --> Model[Sample deal-stage dbt model]
```

## Component Boundaries

| Component | Responsibility |
|---|---|
| `src/hubspot_client.py` | Authenticate to HubSpot and paginate CRM objects |
| `src/transform.py` | Convert vendor payloads into stable warehouse records |
| `src/bigquery_loader.py` | Validate table names and load explicit BigQuery schemas |
| `src/pipeline.py` | Orchestrate contacts, deals, and companies synchronization |
| `dbt_models/` | Demonstrate a downstream reporting transformation |

## Reliability And Security Decisions

- Pull requests run offline tests and never call vendor systems.
- Scheduled live runs execute only when all required secrets are configured.
- Google service-account JSON is written to a temporary runner file with mode
  `0600` and is not stored in the repository.
- BigQuery schemas are explicit rather than inferred from API responses.
- Full refresh is deliberately used for simplicity and is documented as a
  limitation, not presented as a production-scale design.

## Production Evolution

A production implementation should add incremental cursors, staging tables and
`MERGE` operations, run metadata, data-quality checks, dead-letter handling,
alerting, and infrastructure-managed IAM.
