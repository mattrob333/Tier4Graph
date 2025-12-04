# backend/app/db/schema.py

from neo4j import AsyncSession

CONSTRAINTS = [
    (
        "vendor_id_unique",
        "CREATE CONSTRAINT vendor_id_unique IF NOT EXISTS "
        "FOR (v:Vendor) REQUIRE v.vendor_id IS UNIQUE",
    ),
    (
        "facility_id_unique",
        "CREATE CONSTRAINT facility_id_unique IF NOT EXISTS "
        "FOR (f:Facility) REQUIRE f.facility_id IS UNIQUE",
    ),
    (
        "service_id_unique",
        "CREATE CONSTRAINT service_id_unique IF NOT EXISTS "
        "FOR (s:Service) REQUIRE s.service_id IS UNIQUE",
    ),
    (
        "cert_id_unique",
        "CREATE CONSTRAINT cert_id_unique IF NOT EXISTS "
        "FOR (c:Certification) REQUIRE c.cert_id IS UNIQUE",
    ),
    (
        "client_id_unique",
        "CREATE CONSTRAINT client_id_unique IF NOT EXISTS "
        "FOR (cl:Client) REQUIRE cl.client_id IS UNIQUE",
    ),
    (
        "project_id_unique",
        "CREATE CONSTRAINT project_id_unique IF NOT EXISTS "
        "FOR (p:Project) REQUIRE p.project_id IS UNIQUE",
    ),
    (
        "constraint_id_unique",
        "CREATE CONSTRAINT constraint_id_unique IF NOT EXISTS "
        "FOR (con:Constraint) REQUIRE con.constraint_id IS UNIQUE",
    ),
]

INDEXES = [
    (
        "vendor_name_index",
        "CREATE INDEX vendor_name_index IF NOT EXISTS "
        "FOR (v:Vendor) ON (v.name)",
    ),
    (
        "client_industry_index",
        "CREATE INDEX client_industry_index IF NOT EXISTS "
        "FOR (cl:Client) ON (cl.industry)",
    ),
]


async def apply_schema(session: AsyncSession) -> dict:
    """
    Apply Neo4j schema constraints and indexes.

    Idempotent: safe to run multiple times (uses IF NOT EXISTS).

    Args:
        session: Neo4j AsyncSession instance.

    Returns:
        Dictionary with lists of applied constraints and indexes.
    """
    applied_constraints = []
    applied_indexes = []

    for name, cypher in CONSTRAINTS:
        await session.run(cypher)
        applied_constraints.append(name)

    for name, cypher in INDEXES:
        await session.run(cypher)
        applied_indexes.append(name)

    return {
        "constraints": applied_constraints,
        "indexes": applied_indexes,
    }
