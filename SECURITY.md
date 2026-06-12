# Security Policy

## Supported Versions

Security fixes are applied to the latest release and the `main` branch.

## Reporting a Vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub's private
vulnerability reporting flow:

https://github.com/giselleevita/crm-pipeline/security/advisories/new

Include the affected component, reproduction steps, security impact, required
attacker capabilities, and any suggested mitigation. You should receive an
acknowledgement within seven days.

## Security Scope

This repository is a reference data pipeline. Production use requires a dedicated
service account, least-privilege HubSpot and BigQuery access, managed secrets,
restricted datasets, monitoring, and an operational incident-response process.
Never commit source-system credentials, exported customer data, or generated
credential files.
