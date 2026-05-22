"""Main pipeline: HubSpot → transform → BigQuery."""
from hubspot_client import get_contacts, get_deals, get_companies
from transform import transform_contacts, transform_deals, transform_companies
from bigquery_loader import load


def run():
    print("Fetching contacts...")
    load("contacts", transform_contacts(get_contacts()))

    print("Fetching deals...")
    load("deals", transform_deals(get_deals()))

    print("Fetching companies...")
    load("companies", transform_companies(get_companies()))

    print("Pipeline complete.")


if __name__ == "__main__":
    run()
