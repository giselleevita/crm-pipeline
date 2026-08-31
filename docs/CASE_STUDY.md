# Case study: CRM pipeline

## Problem

Commercial teams ask questions about the pipeline that HubSpot answers slowly
and history answers not at all. What is in each stage, what changed this week,
what did the pipeline look like a month ago. The last one HubSpot cannot answer
at all, because it stores current state.

## What was built

An incremental extractor and a dimensional model.

The extractor pulls contacts, companies, deals and their associations from the
HubSpot CRM API, filtered on modification time since the last successful run,
and lands each response as raw JSON in BigQuery. dbt turns that into staging
views, a type 2 snapshot of deals, and marts: `dim_contact`, `dim_company`,
`fct_deal`, `bridge_deal_company`, and `fct_deal_stage_daily`.

## Engineering choices

**Incremental, not full refresh.** A watermark per object type in
`pipeline_state`, written only after a successful load, with five minutes of
overlap re-read each run to cover records modified while the previous run was in
flight. The load is an upsert, so overlap costs nothing.

**Raw layer as the contract.** The payload is stored exactly as returned. Adding
a field is a SQL change rather than a code change plus a backfill.

**Grain stated, not assumed.** `fct_deal` is one row per deal. Multiple companies
on one deal is a real HubSpot behaviour, so the many-to-many lives in a bridge
table and the fact carries a primary key chosen by an explicit, deterministic
rule with the count alongside it.

**History where it pays.** Deals get type 2 history because stage movement is
the question people ask. Contacts and companies are type 1, and the README says
so rather than leaving it to be discovered.

## Testing

28 unit tests, none of which need a network or a warehouse: pagination across
pages, re-anchoring past the result cap, retry and backoff behaviour, the
envelope and watermark derivation, the generated MERGE SQL, and the orchestration
rule that a failed load must leave the watermark where it was. dbt adds
uniqueness, not-null, accepted-values and relationship tests, plus two singular
tests for the daily grain and orphaned associations.

## Limitations

Deletes in HubSpot are not propagated. Schema drift shows up as failing tests
rather than a named alert. Deal history begins the day the snapshot was first
run. Failures are recorded rather than alerted on. These are listed in the
README rather than left to be found.
