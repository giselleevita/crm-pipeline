# Contributing

## Getting started

```bash
git clone https://github.com/giselleevita/crm-pipeline
cd crm-pipeline
pip install -r requirements.txt
cp .env.example .env
pytest tests/ -v
```

## Branch naming

| Type | Pattern | Example |
|---|---|---|
| Feature | `feat/description` | `feat/activities-incremental-sync` |
| Bug fix | `fix/description` | `fix/deal-dedup-logic` |
| dbt model | `dbt/description` | `dbt/pipeline-velocity-mart` |
| Docs | `docs/description` | `docs/data-dictionary-update` |

## PR checklist

- [ ] `pytest tests/` passes
- [ ] New dbt models include schema tests (not_null, unique)
- [ ] `data_dictionary.md` updated for any new or changed fields
- [ ] `.env.example` updated if new env vars are added
- [ ] No real API keys, project IDs, or credentials committed
- [ ] Incremental sync logic tested with both empty and existing target tables
