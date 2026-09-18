"""Pull contacts, deals and companies from HubSpot REST API."""
import os

import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

BASE_URL = "https://api.hubapi.com/crm/v3/objects"
MAX_PAGES = 10_000


def _auth_headers() -> dict[str, str]:
    api_key = os.getenv("HUBSPOT_API_KEY")
    if not api_key:
        raise RuntimeError("HUBSPOT_API_KEY is required to call the HubSpot API.")
    return {"Authorization": f"Bearer {api_key}"}


def _retrying_session() -> requests.Session:
    """Build a session that respects rate limits and retries transient failures."""
    retry = Retry(
        total=5,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def _fetch_all(
    object_type: str,
    properties: list[str],
    *,
    session: requests.Session | None = None,
) -> list[dict]:
    """Paginate through all records while rejecting malformed or looping responses."""
    records, after = [], None
    url = f"{BASE_URL}/{object_type}"
    client = session or _retrying_session()
    seen_cursors: set[str] = set()
    for _ in range(MAX_PAGES):
        params: dict[str, str | int] = {"limit": 100, "properties": ",".join(properties)}
        if after is not None:
            params["after"] = after
        response = client.get(url, headers=_auth_headers(), params=params, timeout=(5, 30))
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(f"HubSpot returned invalid JSON for {object_type}") from exc
        page = data.get("results")
        if not isinstance(page, list):
            raise RuntimeError(f"HubSpot response for {object_type} is missing a results list")
        records.extend(page)
        next_cursor = data.get("paging", {}).get("next", {}).get("after")
        if next_cursor is None:
            return records
        next_cursor = str(next_cursor)
        if next_cursor in seen_cursors:
            raise RuntimeError(f"HubSpot pagination cursor repeated for {object_type}: {next_cursor}")
        seen_cursors.add(next_cursor)
        after = next_cursor
    raise RuntimeError(f"HubSpot pagination exceeded {MAX_PAGES} pages for {object_type}")


def get_contacts() -> list[dict]:
    return _fetch_all("contacts", ["firstname", "lastname", "email", "createdate", "hs_lead_status"])


def get_deals() -> list[dict]:
    return _fetch_all("deals", ["dealname", "amount", "dealstage", "closedate", "createdate", "pipeline"])


def get_companies() -> list[dict]:
    return _fetch_all("companies", ["name", "domain", "industry", "country", "createdate", "numberofemployees"])
