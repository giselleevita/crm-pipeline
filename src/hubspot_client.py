"""HubSpot CRM API client.

Three things this module is responsible for and nothing else:

1. Authentication with a private app token.
2. Retrying the calls HubSpot tells us to retry (429 and 5xx).
3. Walking every page of a result set, including the case where a result set
   is larger than the 10,000 records the search endpoint will page through.

It returns raw API records untouched. Anything that reshapes a record lives
downstream, so that a change in what we want from a field never means going
back to the API.
"""
from __future__ import annotations

import random
import time
from collections.abc import Iterator
from datetime import datetime

import requests

BASE_URL = "https://api.hubapi.com"

# HubSpot refuses to page past 10,000 results in a single search query. Past
# that point the query has to be re-anchored on a later timestamp.
SEARCH_RESULT_CAP = 10_000

# The v4 association batch endpoint accepts 100 ids per call.
ASSOCIATION_BATCH_SIZE = 100

RETRY_STATUS = frozenset({429, 500, 502, 503, 504})

PROPERTIES: dict[str, list[str]] = {
    "contacts": [
        "firstname",
        "lastname",
        "email",
        "hs_lead_status",
        "lifecyclestage",
        "createdate",
        "hs_lastmodifieddate",
    ],
    "companies": [
        "name",
        "domain",
        "industry",
        "country",
        "numberofemployees",
        "createdate",
        "hs_lastmodifieddate",
    ],
    "deals": [
        "dealname",
        "amount",
        "dealstage",
        "pipeline",
        "closedate",
        "createdate",
        "hs_lastmodifieddate",
    ],
}

# Contacts expose their modification time under a different property name than
# every other object, which is the kind of detail that only shows up once the
# incremental filter silently returns nothing.
MODIFIED_PROPERTY = {
    "contacts": "lastmodifieddate",
    "companies": "hs_lastmodifieddate",
    "deals": "hs_lastmodifieddate",
}


def to_millis(moment: datetime) -> int:
    """HubSpot search filters compare datetimes as epoch milliseconds."""
    return int(moment.timestamp() * 1000)


class HubSpotError(RuntimeError):
    pass


class HubSpotClient:
    def __init__(
        self,
        token: str,
        session: requests.Session | None = None,
        max_retries: int = 5,
        sleep=time.sleep,
        page_size: int = 100,
    ) -> None:
        if not token:
            raise RuntimeError("HUBSPOT_API_KEY is required to call the HubSpot API.")
        self._token = token
        self._session = session or requests.Session()
        self._max_retries = max_retries
        self._sleep = sleep
        self._page_size = page_size

    # ------------------------------------------------------------------ HTTP

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    def _backoff_seconds(self, response, attempt: int) -> float:
        """Honour Retry-After when HubSpot sends it, back off exponentially when it does not."""
        retry_after = response.headers.get("Retry-After") if response is not None else None
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
        # Jitter matters here: a nightly run that fans out across three object
        # types should not synchronise its retries into a second burst.
        return (2**attempt) + random.uniform(0, 0.5)

    def _request(self, method: str, path: str, **kwargs) -> dict:
        url = f"{BASE_URL}{path}"
        last_status = None
        for attempt in range(self._max_retries + 1):
            response = self._session.request(
                method, url, headers=self._headers(), timeout=30, **kwargs
            )
            last_status = response.status_code
            if response.status_code in RETRY_STATUS:
                if attempt == self._max_retries:
                    break
                self._sleep(self._backoff_seconds(response, attempt))
                continue
            response.raise_for_status()
            return response.json()
        raise HubSpotError(
            f"{method} {path} still failing with HTTP {last_status} after {self._max_retries} retries."
        )

    # ------------------------------------------------------------- extraction

    def search_modified_since(self, object_type: str, since: datetime) -> Iterator[dict]:
        """Yield every record of object_type modified at or after `since`.

        Sorted ascending by modification time, which is what makes the
        re-anchoring below safe: when we hit HubSpot's paging cap we can
        restart the query from the last record we saw rather than starting over.
        """
        if object_type not in PROPERTIES:
            raise ValueError(f"Unsupported object type: {object_type}")

        modified_property = MODIFIED_PROPERTY[object_type]
        cursor_value = to_millis(since)
        after: str | None = None
        seen_in_query = 0

        while True:
            body = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": modified_property,
                                "operator": "GTE",
                                "value": cursor_value,
                            }
                        ]
                    }
                ],
                "sorts": [{"propertyName": modified_property, "direction": "ASCENDING"}],
                "properties": PROPERTIES[object_type],
                "limit": self._page_size,
            }
            if after:
                body["after"] = after

            payload = self._request("POST", f"/crm/v3/objects/{object_type}/search", json=body)
            results = payload.get("results", [])
            if not results:
                return

            for record in results:
                yield record

            seen_in_query += len(results)
            after = payload.get("paging", {}).get("next", {}).get("after")

            if after is None:
                return

            if seen_in_query + self._page_size > SEARCH_RESULT_CAP:
                # Re-anchor rather than page past the cap. The last record is
                # re-read on the next query; the load is an upsert, so a
                # duplicate read costs nothing but a duplicate write would.
                last_modified = results[-1].get("properties", {}).get(modified_property)
                if not last_modified:
                    raise HubSpotError(
                        f"Cannot re-anchor {object_type} search: {modified_property} missing from results."
                    )
                cursor_value = _as_millis(last_modified)
                after = None
                seen_in_query = 0

    def read_associations(
        self, from_type: str, to_type: str, ids: list[str]
    ) -> dict[str, list[str]]:
        """Map each `from` id to its associated `to` ids.

        Associations are a separate call because the search endpoint does not
        return them. That is a HubSpot constraint, not a design choice.
        """
        associations: dict[str, list[str]] = {}
        for chunk_start in range(0, len(ids), ASSOCIATION_BATCH_SIZE):
            chunk = ids[chunk_start : chunk_start + ASSOCIATION_BATCH_SIZE]
            payload = self._request(
                "POST",
                f"/crm/v4/associations/{from_type}/{to_type}/batch/read",
                json={"inputs": [{"id": record_id} for record_id in chunk]},
            )
            for result in payload.get("results", []):
                from_id = str(result.get("from", {}).get("id"))
                associations[from_id] = [
                    str(target["toObjectId"])
                    for target in result.get("to", [])
                    if target.get("toObjectId") is not None
                ]
        return associations


def _as_millis(value: str | int) -> int:
    """HubSpot returns modification times as ISO strings on some objects and epoch millis on others."""
    if isinstance(value, int):
        return value
    if value.isdigit():
        return int(value)
    return to_millis(datetime.fromisoformat(value.replace("Z", "+00:00")))
