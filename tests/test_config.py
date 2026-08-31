"""Configuration fails loudly at the start of a run rather than halfway through it."""
import pytest

from config import load_config


def test_missing_token_names_the_variable(monkeypatch):
    monkeypatch.delenv("HUBSPOT_API_KEY", raising=False)
    monkeypatch.setenv("GCP_PROJECT_ID", "demo")

    with pytest.raises(RuntimeError, match="HUBSPOT_API_KEY"):
        load_config()


def test_missing_project_names_the_variable(monkeypatch):
    monkeypatch.setenv("HUBSPOT_API_KEY", "token")
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)

    with pytest.raises(RuntimeError, match="GCP_PROJECT_ID"):
        load_config()


def test_dataset_defaults_and_table_ids_are_fully_qualified(monkeypatch):
    monkeypatch.setenv("HUBSPOT_API_KEY", "token")
    monkeypatch.setenv("GCP_PROJECT_ID", "demo")
    monkeypatch.delenv("GCP_DATASET_ID", raising=False)

    config = load_config()

    assert config.dataset == "crm_raw"
    assert config.table("raw_deals") == "demo.crm_raw.raw_deals"


def test_non_numeric_override_is_rejected(monkeypatch):
    monkeypatch.setenv("HUBSPOT_API_KEY", "token")
    monkeypatch.setenv("GCP_PROJECT_ID", "demo")
    monkeypatch.setenv("EXTRACT_LOOKBACK_MINUTES", "soon")

    with pytest.raises(RuntimeError, match="EXTRACT_LOOKBACK_MINUTES"):
        load_config()
