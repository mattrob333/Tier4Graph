"""
Research Dataset Vendor Seeding Script

Loads the full research vendor dataset into Neo4j via the running FastAPI backend.
Reads from backend/data/vendors_research_full.json and POSTs to:
  - POST /vendors
  - POST /ingestion/vendors/{vendor_id}/facilities
  - POST /ingestion/vendors/{vendor_id}/services
  - POST /ingestion/vendors/{vendor_id}/certifications

This script handles the research JSON structure which has:
{
  "generated_at": "...",
  "vendors": [
    {
      "vendor": { ... },
      "facilities": [ ... ],
      "services": [ ... ],
      "certifications": [ ... ]
    },
    ...
  ]
}

Usage:
    cd backend
    python -m scripts.seed_vendors_research

Requirements:
    - Backend must be running on http://localhost:8000
    - httpx must be installed (pip install httpx)
"""

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx

BASE_URL = "http://localhost:8000"
RESEARCH_FILE = Path(__file__).parent.parent / "data" / "vendors_full_research.json"


def extract_region(vendor_data: dict, facilities: list[dict]) -> str | None:
    """
    Extract region using fallback logic:
    1. vendor.region if present
    2. vendor.regions_served[0] if present
    3. First facility's region if present
    4. None if nothing found
    """
    # Try vendor.region first
    if vendor_data.get("region"):
        return vendor_data["region"]

    # Try regions_served[0]
    regions_served = vendor_data.get("regions_served", [])
    if regions_served and len(regions_served) > 0:
        return regions_served[0]

    # Try first facility's region
    if facilities and len(facilities) > 0:
        first_facility = facilities[0]
        if first_facility.get("region"):
            return first_facility["region"]
        # Also try 'geo' field which is used in our model
        if first_facility.get("geo"):
            return first_facility["geo"]

    return None


def build_vendor_payload(vendor_data: dict, facilities: list[dict]) -> dict:
    """
    Build the vendor payload for POST /vendors.
    Maps research JSON fields to our VendorCreate model fields.
    """
    region = extract_region(vendor_data, facilities)

    # Map primary_segments - handle various field names: segment, segments, primary_segments
    segments = vendor_data.get("primary_segments") or vendor_data.get("segments") or vendor_data.get("segment") or []
    if isinstance(segments, str):
        segments = [segments]

    # Map risk score - handle various field names
    risk_score = (
        vendor_data.get("risk_score_guess")
        or vendor_data.get("risk_level_guess")
        or vendor_data.get("risk_score")
        or vendor_data.get("risk")
    )
    if risk_score is not None:
        try:
            risk_score = float(risk_score)
        except (ValueError, TypeError):
            risk_score = None

    payload = {
        "vendor_id": vendor_data["vendor_id"],
        "name": vendor_data["name"],
        "summary": vendor_data.get("summary") or vendor_data.get("description"),
        "hq_country": vendor_data.get("hq_country") or vendor_data.get("country"),
        "hq_city": vendor_data.get("hq_city") or vendor_data.get("city"),
        "region": region,
        "website": vendor_data.get("website") or vendor_data.get("url"),
        "primary_segments": segments,
        "typical_customer_profile": vendor_data.get("typical_customer_profile")
        or vendor_data.get("customer_profile"),
        "risk_score_guess": risk_score,
        "financial_stability_guess": vendor_data.get("financial_stability_guess")
        or vendor_data.get("financial_stability"),
        "culture_text": vendor_data.get("culture_text") or vendor_data.get("culture"),
    }

    # Remove None values to let defaults apply
    return {k: v for k, v in payload.items() if v is not None}


def build_facility_payload(facility: dict, vendor_id: str) -> dict:
    """
    Build a facility payload for the ingestion endpoint.
    Maps research JSON fields to our FacilityBase model fields.
    """
    payload = {
        "facility_id": facility.get("facility_id") or f"{vendor_id}-{facility.get('name', 'facility')}".lower().replace(" ", "-"),
        "vendor_id": vendor_id,
        "geo": facility.get("geo") or facility.get("region") or facility.get("location"),
        "tier": facility.get("tier"),
        "cooling": facility.get("cooling"),
        "power_density": facility.get("power_density"),
        "address": facility.get("address") or facility.get("location"),
    }

    # Handle power_density type conversion
    if payload.get("power_density") is not None:
        try:
            payload["power_density"] = float(payload["power_density"])
        except (ValueError, TypeError):
            payload["power_density"] = None

    return {k: v for k, v in payload.items() if v is not None}


def build_service_payload(service: dict, vendor_id: str) -> dict:
    """
    Build a service payload for the ingestion endpoint.
    Maps research JSON fields to our ServiceBase model fields.
    """
    # Generate service_id if not present
    service_id = service.get("service_id")
    if not service_id:
        category = service.get("category", "service")
        service_id = f"{vendor_id}-{category}".lower().replace(" ", "-")

    payload = {
        "service_id": service_id,
        "category": service.get("category") or service.get("type") or "general",
        "description": service.get("description") or service.get("name"),
    }

    return {k: v for k, v in payload.items() if v is not None}


def build_certification_payload(cert: dict, vendor_id: str) -> dict:
    """
    Build a certification payload for the ingestion endpoint.
    Maps research JSON fields to our CertificationBase model fields.
    """
    # Generate cert_id if not present
    cert_id = cert.get("cert_id")
    if not cert_id:
        name = cert.get("name", "cert")
        cert_id = f"{vendor_id}-{name}".lower().replace(" ", "-").replace("/", "-")

    payload = {
        "cert_id": cert_id,
        "name": cert.get("name") or cert.get("certification") or cert.get("title"),
        "notes": cert.get("notes") or cert.get("description") or cert.get("details"),
    }

    return {k: v for k, v in payload.items() if v is not None and k != "name" or payload.get("name")}


async def seed_vendor(client: httpx.AsyncClient, vendor_bundle: dict) -> bool:
    """
    Seed a single vendor with its facilities, services, and certifications.
    Returns True if all operations succeeded, False otherwise.
    """
    vendor_data = vendor_bundle.get("vendor", {})
    facilities_raw = vendor_bundle.get("facilities", [])
    services_raw = vendor_bundle.get("services", [])
    certifications_raw = vendor_bundle.get("certifications", [])

    vendor_id = vendor_data.get("vendor_id")
    vendor_name = vendor_data.get("name", "Unknown")

    if not vendor_id:
        print(f"  SKIP - No vendor_id found for vendor: {vendor_name}")
        return False

    print(f"\n{'='*60}")
    print(f"Seeding vendor: {vendor_name} ({vendor_id})")
    print(f"  Facilities: {len(facilities_raw)}, Services: {len(services_raw)}, Certs: {len(certifications_raw)}")
    print(f"{'='*60}")

    all_success = True

    # 1. Create/update vendor
    vendor_payload = build_vendor_payload(vendor_data, facilities_raw)
    print(f"  [1/4] Creating vendor (region={vendor_payload.get('region')})...")
    try:
        resp = await client.post(f"{BASE_URL}/vendors", json=vendor_payload)
        if resp.status_code in (200, 201):
            print(f"        OK - Vendor created/updated")
        else:
            print(f"        ERROR - Status {resp.status_code}: {resp.text[:200]}")
            all_success = False
    except httpx.RequestError as e:
        print(f"        ERROR - Request failed: {e}")
        all_success = False

    # 2. Ingest facilities
    print(f"  [2/4] Ingesting {len(facilities_raw)} facilities...")
    if facilities_raw:
        facilities_payload = [
            build_facility_payload(f, vendor_id) for f in facilities_raw
        ]
        # Filter out facilities without required fields
        facilities_payload = [
            f for f in facilities_payload if f.get("facility_id") and f.get("vendor_id")
        ]
        try:
            resp = await client.post(
                f"{BASE_URL}/ingestion/vendors/{vendor_id}/facilities",
                json=facilities_payload,
            )
            if resp.status_code in (200, 201):
                print(f"        OK - {len(facilities_payload)} facilities ingested")
            else:
                print(f"        ERROR - Status {resp.status_code}: {resp.text[:200]}")
                all_success = False
        except httpx.RequestError as e:
            print(f"        ERROR - Request failed: {e}")
            all_success = False
    else:
        print(f"        SKIP - No facilities to ingest")

    # 3. Ingest services
    print(f"  [3/4] Ingesting {len(services_raw)} services...")
    if services_raw:
        services_payload = [build_service_payload(s, vendor_id) for s in services_raw]
        # Filter out services without required fields
        services_payload = [
            s for s in services_payload if s.get("service_id") and s.get("category")
        ]
        try:
            resp = await client.post(
                f"{BASE_URL}/ingestion/vendors/{vendor_id}/services",
                json=services_payload,
            )
            if resp.status_code in (200, 201):
                print(f"        OK - {len(services_payload)} services ingested")
            else:
                print(f"        ERROR - Status {resp.status_code}: {resp.text[:200]}")
                all_success = False
        except httpx.RequestError as e:
            print(f"        ERROR - Request failed: {e}")
            all_success = False
    else:
        print(f"        SKIP - No services to ingest")

    # 4. Ingest certifications
    print(f"  [4/4] Ingesting {len(certifications_raw)} certifications...")
    if certifications_raw:
        certifications_payload = [
            build_certification_payload(c, vendor_id) for c in certifications_raw
        ]
        # Filter out certs without required name field
        certifications_payload = [
            c for c in certifications_payload if c.get("name")
        ]
        try:
            resp = await client.post(
                f"{BASE_URL}/ingestion/vendors/{vendor_id}/certifications",
                json=certifications_payload,
            )
            if resp.status_code in (200, 201):
                print(f"        OK - {len(certifications_payload)} certifications ingested")
            else:
                print(f"        ERROR - Status {resp.status_code}: {resp.text[:200]}")
                all_success = False
        except httpx.RequestError as e:
            print(f"        ERROR - Request failed: {e}")
            all_success = False
    else:
        print(f"        SKIP - No certifications to ingest")

    return all_success


async def main():
    """Main entry point for the research dataset seeding script."""
    print("=" * 60)
    print("Research Dataset Vendor Seeding Script")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"Research file: {RESEARCH_FILE}")

    # Check if research file exists
    if not RESEARCH_FILE.exists():
        print(f"\nERROR: Research file not found at {RESEARCH_FILE}")
        print("       Please ensure vendors_research_full.json exists in backend/data/")
        return

    # Load research data
    print(f"\nLoading research data...")
    with open(RESEARCH_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Extract vendor bundles from the "vendors" key
    vendor_bundles = data.get("vendors", [])

    if not vendor_bundles:
        print("ERROR: No vendors found in the research file.")
        print("       Expected structure: { 'vendors': [ {...}, {...}, ... ] }")
        return

    generated_at = data.get("generated_at", "unknown")
    print(f"Dataset generated at: {generated_at}")
    print(f"Found {len(vendor_bundles)} vendors to seed")

    # Check backend health first
    print(f"\nChecking backend health...")
    async with httpx.AsyncClient(timeout=60.0) as client:
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
        total_facilities = 0
        total_services = 0
        total_certs = 0

        for vendor_bundle in vendor_bundles:
            success = await seed_vendor(client, vendor_bundle)
            if success:
                success_count += 1
            else:
                fail_count += 1

            # Track totals
            total_facilities += len(vendor_bundle.get("facilities", []))
            total_services += len(vendor_bundle.get("services", []))
            total_certs += len(vendor_bundle.get("certifications", []))

        # Summary
        print("\n" + "=" * 60)
        print("SEEDING COMPLETE")
        print("=" * 60)
        print(f"  Vendors:        {success_count} succeeded, {fail_count} failed")
        print(f"  Total vendors:  {len(vendor_bundles)}")
        print(f"  Facilities:     {total_facilities}")
        print(f"  Services:       {total_services}")
        print(f"  Certifications: {total_certs}")

        if fail_count > 0:
            print("\nWARNING: Some vendors failed to seed completely.")
            print("         Check the logs above for details.")


if __name__ == "__main__":
    asyncio.run(main())
