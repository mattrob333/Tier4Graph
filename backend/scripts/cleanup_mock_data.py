#!/usr/bin/env python3
"""
Cleanup script to remove mock/test vendor data from Neo4j.
Removes vendors that exist in the old mock seed file but not in the research data.
"""

import asyncio
import json
from pathlib import Path

from neo4j import AsyncGraphDatabase

# Mock vendor IDs to remove (old seed data that's been superseded)
MOCK_VENDOR_IDS = [
    "digitalrealty",  # Duplicate of digital-realty from research
    "healthcaredc",   # Fictional mock vendor
    "budgetcolo",     # Fictional mock vendor
]


async def cleanup_mock_vendors():
    """Remove mock vendors and all their relationships from Neo4j."""
    
    # Load Neo4j connection from environment or use defaults
    import os
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    
    driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    
    async with driver.session() as session:
        for vendor_id in MOCK_VENDOR_IDS:
            print(f"Removing mock vendor: {vendor_id}")
            
            # Delete all relationships and the vendor node
            result = await session.run("""
                MATCH (v:Vendor {vendor_id: $vendor_id})
                OPTIONAL MATCH (v)-[r]-()
                DELETE r, v
                RETURN count(v) as deleted
            """, vendor_id=vendor_id)
            
            record = await result.single()
            if record and record["deleted"] > 0:
                print(f"  ✓ Deleted {vendor_id}")
            else:
                print(f"  - {vendor_id} not found (already clean)")
    
    await driver.close()
    print("\nCleanup complete!")


if __name__ == "__main__":
    asyncio.run(cleanup_mock_vendors())
