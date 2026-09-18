# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## Unreleased

- Added bounded, rate-limit-aware HubSpot retries and pagination loop detection.
- Full-refresh loads now fail closed on empty extracts unless explicitly overridden.
- All source objects are extracted before warehouse mutation, reducing partial-refresh risk.
- Added API pagination, retry-policy, loader-safety, and orchestration regression tests.

## [1.0.0]

### Added
- Python extractor for HubSpot contacts, deals, companies, and activities
- Full and incremental sync modes with idempotent loads
- BigQuery loader with raw layer ingestion
- dbt models: raw → staging → marts (sales funnel, pipeline velocity, activity summaries)
- GitHub Actions workflow for scheduled daily pipeline runs
- Slack webhook alerting on pipeline failure
- `data_dictionary.md` — field definitions for all synced HubSpot objects
- pytest suite for extractor and loader logic
- `.env.example` with all required environment variables
