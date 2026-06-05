"""Pull contacts, deals and companies from HubSpot REST API."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.hubapi.com/crm/v3/objects"


def _auth_headers() -> dict[str, str]:
    api_key = os.getenv("HUBSPOT_API_KEY")
    if not api_key:
        raise RuntimeError("HUBSPOT_API_KEY is required to call the HubSpot API.")
    return {"Authorization": f"Bearer {api_key}"}


def _fetch_all(object_type: str, properties: list[str]) -> list[dict]:
    """Paginate through all records for a given CRM object."""
    records, after = [], None
    url = f"{BASE_URL}/{object_type}"
    while True:
        params = {"limit": 100, "properties": ",".join(properties)}
        if after:
            params["after"] = after
        resp = requests.get(url, headers=_auth_headers(), params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        records.extend(data.get("results", []))
        paging = data.get("paging", {}).get("next", {})
        after = paging.get("after")
        if not after:
            break
    return records


def get_contacts() -> list[dict]:
    return _fetch_all("contacts", ["firstname", "lastname", "email", "createdate", "hs_lead_status"])


def get_deals() -> list[dict]:
    return _fetch_all("deals", ["dealname", "amount", "dealstage", "closedate", "createdate", "pipeline"])


def get_companies() -> list[dict]:
    return _fetch_all("companies", ["name", "domain", "industry", "country", "createdate", "numberofemployees"])
