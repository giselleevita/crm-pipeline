# Case Study: CRM Pipeline

## Problem

Sales and customer-success teams often need trustworthy CRM reporting without manually exporting spreadsheets from HubSpot. The goal of this project is to show a practical, client-style data pipeline that ingests CRM records, models them into reporting tables, and keeps the operational path auditable.

## Solution

The pipeline extracts contacts, deals, companies, and activities from HubSpot, loads them into BigQuery, applies dbt transformations, and makes the modeled data available for Metabase dashboards.

The design separates raw ingestion from transformed reporting layers so the system can be re-run safely, debugged when source data changes, and extended without rewriting the full pipeline.

## Architecture

- Python extractor for HubSpot API ingestion.
- BigQuery raw dataset for source-aligned data.
- dbt staging and mart models for reporting-ready tables.
- GitHub Actions for scheduled runs and test automation.
- Slack alerting for failed pipeline runs.

## Engineering Choices

- Idempotent loads reduce duplicate records and make retries safer.
- Secrets are passed through environment variables or CI secrets, not source code.
- Service accounts are scoped separately for loading and dashboard access.
- dbt models document transformation logic in a reviewable format.

## Security And Reliability Controls

- Read-only HubSpot token scope.
- Least-privilege BigQuery service account permissions.
- No committed credentials.
- Pipeline failure alerting.
- Tests for extractor, loader, and transformation behavior.

## What This Shows

This is the strongest general software-delivery project in the portfolio because it connects engineering work to a normal business workflow: data ingestion, warehouse modeling, operational scheduling, and reporting.

It is useful in interviews because it demonstrates client-facing thinking, not only technical experimentation.

## Next Improvements

- Add Terraform for BigQuery datasets and IAM bindings.
- Add data quality checks with dbt tests or Great Expectations.
- Add sample dashboard screenshots using synthetic data.
- Add replayable fixture data for fully offline demos.
