"""Runtime configuration, resolved once from the environment.

Config is read here and passed down explicitly so that nothing deeper in the
pipeline reaches for os.environ. That keeps every other module testable
without monkeypatching the environment.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

# Records modified while an extract is running would otherwise fall into the
# gap between "read from HubSpot" and "watermark written". Re-reading a few
# minutes of overlap on every run closes that gap. The load is an upsert, so
# re-reading the same record is free.
DEFAULT_LOOKBACK_MINUTES = 5


@dataclass(frozen=True)
class Config:
    hubspot_token: str
    gcp_project: str
    dataset: str
    lookback_minutes: int = DEFAULT_LOOKBACK_MINUTES
    page_size: int = 100
    max_retries: int = 5

    def table(self, name: str) -> str:
        return f"{self.gcp_project}.{self.dataset}.{name}"


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is required. Copy .env.example to .env and fill it in.")
    return value


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw in (None, ""):
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer, got {raw!r}.") from exc


def load_config() -> Config:
    return Config(
        hubspot_token=_required("HUBSPOT_API_KEY"),
        gcp_project=_required("GCP_PROJECT_ID"),
        dataset=os.getenv("GCP_DATASET_ID", "crm_raw"),
        lookback_minutes=_int_env("EXTRACT_LOOKBACK_MINUTES", DEFAULT_LOOKBACK_MINUTES),
        page_size=_int_env("HUBSPOT_PAGE_SIZE", 100),
        max_retries=_int_env("HUBSPOT_MAX_RETRIES", 5),
    )
