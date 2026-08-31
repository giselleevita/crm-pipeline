# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.2.0]

### Added
- Incremental extraction filtered on `hs_lastmodifieddate`, with a per-object
  watermark in `pipeline_state` written only after a successful load
- Retries with exponential backoff and jitter on 429 and 5xx, honouring `Retry-After`
- Re-anchoring of the search query past HubSpot's 10,000 result paging cap
- Deal to company and deal to contact associations via the v4 batch endpoint
- Raw layer: HubSpot payloads landed unmodified as JSON text
- Idempotent loads: `MERGE` on the object id, source de-duplicated, no backwards updates
- dbt project: staging views, marts as tables, schema tests and two singular tests
- `dim_contact`, `dim_company`, `fct_deal`, `bridge_deal_company`, `fct_deal_stage_daily`
- `deal_snapshot`, a type 2 snapshot giving deals the history HubSpot does not keep
- `pipeline_runs` run history and dbt source freshness thresholds
- Single entrypoint (`scripts/run_pipeline.sh`), Dockerfile, and a CI job that
  runs tests and `dbt parse` without credentials

### Changed
- Loads are incremental upserts rather than `WRITE_TRUNCATE` full refreshes
- Typing and renaming moved out of Python into dbt staging models
- CI split into an offline `checks` job and a credential-dependent `sync` job

### Removed
- `src/transform.py`, superseded by the raw layer and dbt staging
- `pandas` and `pytest-mock`, neither of which was used

## [0.1.0]

### Added
- Python extractor for HubSpot contacts, companies and deals with cursor pagination
- BigQuery loader with explicit schemas, full refresh via `WRITE_TRUNCATE`
- One sample dbt SQL file for deal stage aggregation
- pytest suite for the transform layer
- GitHub Actions workflow running tests, and a live sync when secrets are present
- `data_dictionary.md` and `.env.example`
