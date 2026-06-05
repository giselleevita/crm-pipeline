"""Unit tests for transform layer."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))
from transform import transform_contacts, transform_deals, transform_companies

SAMPLE_CONTACT = {"id": "1", "properties": {"firstname": "Ada", "lastname": "Lovelace", "email": "ada@example.com", "hs_lead_status": "NEW", "createdate": "2026-01-01T00:00:00Z"}}
SAMPLE_DEAL    = {"id": "2", "properties": {"dealname": "Big Deal", "amount": "5000", "dealstage": "contractsent", "pipeline": "default", "closedate": "2026-06-01T00:00:00Z", "createdate": "2026-01-01T00:00:00Z"}}
SAMPLE_COMPANY = {"id": "3", "properties": {"name": "Acme", "domain": "acme.com", "industry": "Software", "country": "DK", "numberofemployees": "50", "createdate": "2026-01-01T00:00:00Z"}}


def test_contact_keys():
    result = transform_contacts([SAMPLE_CONTACT])
    assert result[0]["email"] == "ada@example.com"
    assert "ingested_at" in result[0]

def test_deal_keys():
    result = transform_deals([SAMPLE_DEAL])
    assert result[0]["stage"] == "contractsent"
    assert result[0]["amount"] == 5000.0

def test_company_keys():
    result = transform_companies([SAMPLE_COMPANY])
    assert result[0]["domain"] == "acme.com"
    assert result[0]["employees"] == 50

def test_invalid_numeric_values_become_null():
    deal = {"id": "4", "properties": {"amount": "not-a-number"}}
    company = {"id": "5", "properties": {"numberofemployees": "unknown"}}

    assert transform_deals([deal])[0]["amount"] is None
    assert transform_companies([company])[0]["employees"] is None
