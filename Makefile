.PHONY: test lint parse run docker-build

test:
	pytest tests/ -q

parse:
	cp -n dbt/profiles.yml.example dbt/profiles.yml || true
	dbt parse --project-dir dbt --profiles-dir dbt

run:
	./scripts/run_pipeline.sh

docker-build:
	docker build -t crm-pipeline .
