"""HubSpot client reliability tests."""

import os
import sys
from unittest.mock import Mock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from hubspot_client import _fetch_all, _retrying_session


def _response(payload):
    response = Mock()
    response.json.return_value = payload
    return response


def test_fetch_all_paginates_and_reuses_session(monkeypatch):
    monkeypatch.setenv("HUBSPOT_API_KEY", "test-token")
    session = Mock()
    session.get.side_effect = [
        _response({"results": [{"id": "1"}], "paging": {"next": {"after": "abc"}}}),
        _response({"results": [{"id": "2"}]}),
    ]

    assert [row["id"] for row in _fetch_all("contacts", ["email"], session=session)] == ["1", "2"]
    assert session.get.call_count == 2
    assert session.get.call_args_list[1].kwargs["params"]["after"] == "abc"
    assert session.get.call_args.kwargs["timeout"] == (5, 30)


def test_fetch_all_rejects_repeated_cursor(monkeypatch):
    monkeypatch.setenv("HUBSPOT_API_KEY", "test-token")
    session = Mock()
    session.get.side_effect = [
        _response({"results": [], "paging": {"next": {"after": "same"}}}),
        _response({"results": [], "paging": {"next": {"after": "same"}}}),
    ]

    with pytest.raises(RuntimeError, match="cursor repeated"):
        _fetch_all("contacts", ["email"], session=session)


def test_fetch_all_rejects_missing_results(monkeypatch):
    monkeypatch.setenv("HUBSPOT_API_KEY", "test-token")
    session = Mock()
    session.get.return_value = _response({"paging": {}})

    with pytest.raises(RuntimeError, match="results list"):
        _fetch_all("contacts", ["email"], session=session)


def test_retrying_session_covers_rate_limits_and_transient_errors():
    retry = _retrying_session().get_adapter("https://").max_retries

    assert retry.total == 5
    assert retry.respect_retry_after_header is True
    assert {429, 500, 502, 503, 504}.issubset(set(retry.status_forcelist))
