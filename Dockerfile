FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY dbt ./dbt
COPY scripts ./scripts

ENV PYTHONUNBUFFERED=1 \
    DBT_PROJECT_DIR=/app/dbt \
    DBT_PROFILES_DIR=/app/dbt

ENTRYPOINT ["./scripts/run_pipeline.sh"]
