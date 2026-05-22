"""Transform raw HubSpot API responses into clean, structured dicts."""
from datetime import datetime


def _safe(record: dict, key: str, default=None):
    return record.get("properties", {}).get(key, default)


def transform_contacts(raw: list[dict]) -> list[dict]:
    return [
        {
            "id": r["id"],
            "firstname": _safe(r, "firstname"),
            "lastname": _safe(r, "lastname"),
            "email": _safe(r, "email"),
            "lead_status": _safe(r, "hs_lead_status"),
            "created_at": _safe(r, "createdate"),
            "ingested_at": datetime.utcnow().isoformat(),
        }
        for r in raw
    ]


def transform_deals(raw: list[dict]) -> list[dict]:
    return [
        {
            "id": r["id"],
            "deal_name": _safe(r, "dealname"),
            "amount": _safe(r, "amount"),
            "stage": _safe(r, "dealstage"),
            "pipeline": _safe(r, "pipeline"),
            "close_date": _safe(r, "closedate"),
            "created_at": _safe(r, "createdate"),
            "ingested_at": datetime.utcnow().isoformat(),
        }
        for r in raw
    ]


def transform_companies(raw: list[dict]) -> list[dict]:
    return [
        {
            "id": r["id"],
            "name": _safe(r, "name"),
            "domain": _safe(r, "domain"),
            "industry": _safe(r, "industry"),
            "country": _safe(r, "country"),
            "employees": _safe(r, "numberofemployees"),
            "created_at": _safe(r, "createdate"),
            "ingested_at": datetime.utcnow().isoformat(),
        }
        for r in raw
    ]
