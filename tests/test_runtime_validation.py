"""Runtime validation tests for API and warehouse boundaries."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from bigquery_loader import load
from hubspot_client import _auth_headers


def test_hubspot_auth_requires_api_key(monkeypatch):
    monkeypatch.delenv("HUBSPOT_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="HUBSPOT_API_KEY"):
        _auth_headers()


def test_hubspot_auth_uses_bearer_token(monkeypatch):
    monkeypatch.setenv("HUBSPOT_API_KEY", "secret-token")

    assert _auth_headers() == {"Authorization": "Bearer secret-token"}


def test_bigquery_load_requires_project(monkeypatch):
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)

    with pytest.raises(RuntimeError, match="GCP_PROJECT_ID"):
        load("contacts", [])


def test_bigquery_load_rejects_unknown_table_before_sdk_import(monkeypatch):
    monkeypatch.setenv("GCP_PROJECT_ID", "demo-project")

    with pytest.raises(ValueError, match="Unsupported BigQuery table"):
        load("unknown", [])
