"""
Vendor Seeding Script

Loads demo vendors into Neo4j via the running FastAPI backend.
Reads from backend/data/vendors_seed.json and POSTs to:
  - POST /vendors
  - POST /ingestion/vendors/{vendor_id}/facilities
  - POST /ingestion/vendors/{vendor_id}/services
  - POST /ingestion/vendors/{vendor_id}/certifications

Usage:
    python backend/scripts/seed_vendors.py

Requirements:
    - Backend must be running on http://localhost:8000
    - httpx must be installed (pip install httpx)
"""

import asyncio
import json
from pathlib import Path

import httpx

BASE_URL = "http://localhost:8000"
SEED_FILE = Path(__file__).parent.parent / "data" / "vendors_seed.json"


async def seed_vendor(client: httpx.AsyncClient, vendor_bundle: dict) -> bool:
    """
    Seed a single vendor with its facilities, services, and certifications.
    Returns True if all operations succeeded, False otherwise.
    """
    vendor = vendor_bundle["vendor"]
    vendor_id = vendor["vendor_id"]
    vendor_name = vendor["name"]

    print(f"\n{'='*60}")
    print(f"Seeding vendor: {vendor_name} ({vendor_id})")
    print(f"{'='*60}")

    all_success = True

    # 1. Create/update vendor
    print(f"  [1/4] Creating vendor...")
    try:
        resp = await client.post(f"{BASE_URL}/vendors", json=vendor)
        if resp.status_code in (200, 201):
            print(f"        OK - Vendor created/updated")
        else:
            print(f"        ERROR - Status {resp.status_code}: {resp.text}")
            all_success = False
    except httpx.RequestError as e:
        print(f"        ERROR - Request failed: {e}")
        all_success = False

    # 2. Ingest facilities
    facilities = vendor_bundle.get("facilities", [])
    print(f"  [2/4] Ingesting {len(facilities)} facilities...")
    if facilities:
        try:
            resp = await client.post(
                f"{BASE_URL}/ingestion/vendors/{vendor_id}/facilities",
                json=facilities
            )
            if resp.status_code in (200, 201):
                print(f"        OK - {len(facilities)} facilities ingested")
            else:
                print(f"        ERROR - Status {resp.status_code}: {resp.text}")
                all_success = False
        except httpx.RequestError as e:
            print(f"        ERROR - Request failed: {e}")
            all_success = False
    else:
        print(f"        SKIP - No facilities to ingest")

    # 3. Ingest services
    services = vendor_bundle.get("services", [])
    print(f"  [3/4] Ingesting {len(services)} services...")
    if services:
        try:
            resp = await client.post(
                f"{BASE_URL}/ingestion/vendors/{vendor_id}/services",
                json=services
            )
            if resp.status_code in (200, 201):
                print(f"        OK - {len(services)} services ingested")
            else:
                print(f"        ERROR - Status {resp.status_code}: {resp.text}")
                all_success = False
        except httpx.RequestError as e:
            print(f"        ERROR - Request failed: {e}")
            all_success = False
    else:
        print(f"        SKIP - No services to ingest")

    # 4. Ingest certifications
    certifications = vendor_bundle.get("certifications", [])
    print(f"  [4/4] Ingesting {len(certifications)} certifications...")
    if certifications:
        try:
            resp = await client.post(
                f"{BASE_URL}/ingestion/vendors/{vendor_id}/certifications",
                json=certifications
            )
            if resp.status_code in (200, 201):
                print(f"        OK - {len(certifications)} certifications ingested")
            else:
                print(f"        ERROR - Status {resp.status_code}: {resp.text}")
                all_success = False
        except httpx.RequestError as e:
            print(f"        ERROR - Request failed: {e}")
            all_success = False
    else:
        print(f"        SKIP - No certifications to ingest")

    return all_success


async def main():
    """Main entry point for the seeding script."""
    print("=" * 60)
    print("Vendor Seeding Script")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"Seed file: {SEED_FILE}")

    # Check if seed file exists
    if not SEED_FILE.exists():
        print(f"\nERROR: Seed file not found at {SEED_FILE}")
        return

    # Load seed data
    print(f"\nLoading seed data...")
    with open(SEED_FILE, "r", encoding="utf-8") as f:
        vendor_bundles = json.load(f)

    print(f"Found {len(vendor_bundles)} vendors to seed")

    # Check backend health first
    print(f"\nChecking backend health...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(f"{BASE_URL}/health")
            if resp.status_code == 200:
                print(f"Backend is healthy: {resp.json()}")
            else:
                print(f"WARNING: Health check returned {resp.status_code}")
        except httpx.RequestError as e:
            print(f"ERROR: Cannot reach backend at {BASE_URL}")
            print(f"       Make sure the backend is running: uvicorn app.main:app --reload")
            print(f"       Error: {e}")
            return

        # Seed each vendor
        success_count = 0
        fail_count = 0

        for vendor_bundle in vendor_bundles:
            success = await seed_vendor(client, vendor_bundle)
            if success:
                success_count += 1
            else:
                fail_count += 1

        # Summary
        print("\n" + "=" * 60)
        print("SEEDING COMPLETE")
        print("=" * 60)
        print(f"  Successful: {success_count}")
        print(f"  Failed:     {fail_count}")
        print(f"  Total:      {len(vendor_bundles)}")

        if fail_count > 0:
            print("\nWARNING: Some vendors failed to seed completely.")
            print("         Check the logs above for details.")


if __name__ == "__main__":
    asyncio.run(main())
