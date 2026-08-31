#!/usr/bin/env bash
# One entrypoint for a full run: extract, build, test. Any step that fails
# stops the run, so a broken extract never leaves marts built on top of it.
set -euo pipefail

PROJECT_DIR="${DBT_PROJECT_DIR:-dbt}"
PROFILES_DIR="${DBT_PROFILES_DIR:-$PROJECT_DIR}"
DBT_TARGET="${DBT_TARGET:-dev}"

echo "==> extract"
python src/pipeline.py "$@"

echo "==> dbt build (models, snapshots and tests)"
dbt build --project-dir "$PROJECT_DIR" --profiles-dir "$PROFILES_DIR" --target "$DBT_TARGET"

echo "==> source freshness"
# Non-fatal on its own: freshness says the extractor stopped running, which is
# worth an alert but is not a reason to fail a build that just succeeded.
dbt source freshness --project-dir "$PROJECT_DIR" --profiles-dir "$PROFILES_DIR" --target "$DBT_TARGET" || true

echo "==> done"
