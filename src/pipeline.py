"""Main pipeline: HubSpot → transform → BigQuery."""
from hubspot_client import get_contacts, get_deals, get_companies
from transform import transform_contacts, transform_deals, transform_companies
from bigquery_loader import load


def run():
    """Extract every object before mutating any warehouse table.

    This prevents an upstream API failure midway through extraction from
    leaving only a subset of the full-refresh tables updated.
    """
    print("Fetching contacts...")
    print("Fetching deals...")
    print("Fetching companies...")
    extracts = {
        "contacts": transform_contacts(get_contacts()),
        "deals": transform_deals(get_deals()),
        "companies": transform_companies(get_companies()),
    }

    for table_name, rows in extracts.items():
        print(f"Loading {table_name}...")
        load(table_name, rows)

    print("Pipeline complete.")


if __name__ == "__main__":
    run()
