# Case Study: CRM Pipeline

## Problem

Sales and customer-success teams often need CRM reporting without manually exporting spreadsheets from HubSpot. A first useful step is to move core CRM records into a warehouse-friendly shape so reporting logic can be reviewed, tested, and extended.

## Solution

This project implements a compact HubSpot-to-BigQuery ingestion path:

- extract contacts, deals, and companies from the HubSpot CRM API
- transform source records into raw warehouse fields
- load full-refresh BigQuery tables
- provide a sample dbt model for deal-stage reporting
- run transformation tests in CI
- optionally run live syncs on a GitHub Actions schedule when secrets are configured

## Architecture

- Python extractor for HubSpot API pagination.
- Transform layer for contacts, deals, and companies.
- BigQuery raw dataset for source-aligned data.
- Sample dbt SQL model for deal-stage aggregation.
- GitHub Actions for tests, scheduled runs, and manual dispatch.

## Engineering Choices

- The current loader uses full refreshes (`WRITE_TRUNCATE`) because that is simple to reason about for a small demo dataset.
- Secrets are passed through environment variables or CI secrets, not source code.
- Transform tests validate the shape of warehouse records before live loading.
- The workflow skips live syncs when credentials are not configured, so pull requests can run safely without external systems.

## Security And Reliability Controls

- No committed HubSpot or Google Cloud credentials.
- HubSpot token is supplied at runtime.
- BigQuery project and dataset are supplied at runtime.
- Tests run without live vendor credentials.
- Live pipeline execution is skipped in CI if required secrets are missing.

## Current Limitations

This is not yet a production-grade CRM data platform. It does not currently implement incremental cursors, BigQuery `MERGE` upserts, activity sync, run metadata, Slack alerting, Terraform-managed IAM, or comprehensive extractor/loader mocks.

## What This Shows

This repo is useful as a data-engineering portfolio support project when presented honestly: it shows API ingestion, transformation discipline, BigQuery loading, and CI separation between offline tests and live syncs.

## Next Improvements

- Add config validation and fail-fast errors for missing environment variables.
- Add mocked HubSpot pagination tests.
- Add mocked BigQuery loader tests.
- Replace full-refresh loads with staging tables and `MERGE`.
- Store incremental cursors per object type.
- Add dbt project configuration, dbt tests, and sample dashboard screenshots.
- Add Slack or email alerting for failed scheduled runs.
