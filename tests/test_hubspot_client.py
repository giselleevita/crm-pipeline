"""The extractor's two failure modes worth testing: partial pages and rate limits."""
from datetime import UTC, datetime

import pytest

import hubspot_client
from hubspot_client import HubSpotClient, HubSpotError

SINCE = datetime(2026, 1, 1, tzinfo=UTC)


class FakeResponse:
    def __init__(self, status_code=200, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.headers = headers or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise AssertionError(f"unexpected HTTP {self.status_code}")


class FakeSession:
    """Returns queued responses and records what was asked for."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.requests = []

    def request(self, method, url, **kwargs):
        self.requests.append({"method": method, "url": url, **kwargs})
        if not self._responses:
            raise AssertionError("more requests than queued responses")
        return self._responses.pop(0)


def _record(record_id, modified="2026-01-02T00:00:00Z"):
    return {"id": record_id, "properties": {"hs_lastmodifieddate": modified}}


def _client(session, **kwargs):
    return HubSpotClient(token="t", session=session, sleep=lambda _: None, **kwargs)


def test_pagination_follows_the_cursor_until_it_runs_out():
    session = FakeSession(
        [
            FakeResponse(payload={"results": [_record("1")], "paging": {"next": {"after": "abc"}}}),
            FakeResponse(payload={"results": [_record("2")]}),
        ]
    )

    records = list(_client(session).search_modified_since("deals", SINCE))

    assert [r["id"] for r in records] == ["1", "2"]
    assert session.requests[0]["json"].get("after") is None
    assert session.requests[1]["json"]["after"] == "abc"


def test_first_page_carries_the_watermark_as_epoch_millis():
    session = FakeSession([FakeResponse(payload={"results": []})])

    list(_client(session).search_modified_since("deals", SINCE))

    filters = session.requests[0]["json"]["filterGroups"][0]["filters"][0]
    assert filters["propertyName"] == "hs_lastmodifieddate"
    assert filters["operator"] == "GTE"
    assert filters["value"] == int(SINCE.timestamp() * 1000)


def test_contacts_filter_on_their_own_modified_property():
    session = FakeSession([FakeResponse(payload={"results": []})])

    list(_client(session).search_modified_since("contacts", SINCE))

    assert (
        session.requests[0]["json"]["filterGroups"][0]["filters"][0]["propertyName"]
        == "lastmodifieddate"
    )


def test_search_reanchors_instead_of_paging_past_the_result_cap(monkeypatch):
    """Past 10,000 results HubSpot stops paging, so the query restarts from the last record seen."""
    monkeypatch.setattr(hubspot_client, "SEARCH_RESULT_CAP", 2)
    session = FakeSession(
        [
            FakeResponse(
                payload={
                    "results": [_record("1"), _record("2", "2026-03-01T00:00:00Z")],
                    "paging": {"next": {"after": "200"}},
                }
            ),
            FakeResponse(payload={"results": [_record("3")]}),
        ]
    )

    records = list(_client(session, page_size=2).search_modified_since("deals", SINCE))

    assert [r["id"] for r in records] == ["1", "2", "3"]
    second_call = session.requests[1]["json"]
    assert "after" not in second_call, "re-anchored query must start from the filter, not the cursor"
    assert second_call["filterGroups"][0]["filters"][0]["value"] == int(
        datetime(2026, 3, 1, tzinfo=UTC).timestamp() * 1000
    )


def test_rate_limit_is_retried_and_respects_retry_after():
    slept = []
    session = FakeSession(
        [
            FakeResponse(status_code=429, headers={"Retry-After": "7"}),
            FakeResponse(payload={"results": [_record("1")]}),
        ]
    )
    client = HubSpotClient(token="t", session=session, sleep=slept.append)

    records = list(client.search_modified_since("deals", SINCE))

    assert [r["id"] for r in records] == ["1"]
    assert slept == [7.0]


def test_server_errors_are_retried_then_reported():
    session = FakeSession([FakeResponse(status_code=503) for _ in range(3)])
    client = _client(session, max_retries=2)

    with pytest.raises(HubSpotError, match="503"):
        list(client.search_modified_since("deals", SINCE))

    assert len(session.requests) == 3


def test_unknown_object_type_is_rejected_before_any_call():
    session = FakeSession([])

    with pytest.raises(ValueError, match="Unsupported object type"):
        list(_client(session).search_modified_since("tickets", SINCE))


def test_associations_are_chunked_and_flattened(monkeypatch):
    monkeypatch.setattr(hubspot_client, "ASSOCIATION_BATCH_SIZE", 2)
    session = FakeSession(
        [
            FakeResponse(
                payload={
                    "results": [
                        {"from": {"id": "1"}, "to": [{"toObjectId": "c1"}, {"toObjectId": "c2"}]},
                        {"from": {"id": "2"}, "to": []},
                    ]
                }
            ),
            FakeResponse(payload={"results": [{"from": {"id": "3"}, "to": [{"toObjectId": "c9"}]}]}),
        ]
    )

    result = _client(session).read_associations("deals", "companies", ["1", "2", "3"])

    assert result == {"1": ["c1", "c2"], "2": [], "3": ["c9"]}
    assert len(session.requests) == 2
    assert session.requests[0]["json"]["inputs"] == [{"id": "1"}, {"id": "2"}]


def test_missing_token_fails_immediately():
    with pytest.raises(RuntimeError, match="HUBSPOT_API_KEY"):
        HubSpotClient(token="")
