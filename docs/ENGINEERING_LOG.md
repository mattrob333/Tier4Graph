# Engineering Log - Cognitive Procurement Engine (CPE)

> **Branch:** `feature/matching-engine-v1`
> **Last Updated:** 2025-12-05
> **Status:** Phase 3-Lite Complete + OpenAI Integration + Frontend Demo

This document provides a chronological log of development progress, key decisions, difficulties encountered, and next steps for the CPE project. Written for onboarding new developers.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Chronological Development Log](#chronological-development-log)
3. [Key Decisions & Rationale](#key-decisions--rationale)
4. [Difficulties & Gotchas](#difficulties--gotchas)
5. [Completed Features](#completed-features)
6. [Known Limitations & TODOs](#known-limitations--todos)
7. [Next Steps](#next-steps)

---

## Project Overview

The Cognitive Procurement Engine (CPE) is an AI-native IT procurement decision platform. It models vendors, facilities, services, certifications, clients, and projects in a **Neo4j graph database** with semantic reasoning and agentic workflows.

**Goal:** Help vCISO advisors match clients with optimal datacenter/IT vendors based on compliance requirements, risk tolerance, geographic needs, and service requirements.

---

## Chronological Development Log

### Phase 1A - Neo4j Foundation
- Set up async Neo4j driver with connection pooling
- Implemented Pydantic settings for configuration management
- Created health endpoints: `/health` (basic) and `/health/neo4j` (database connectivity)

### Phase 1B - Schema Bootstrap
- Created `/admin/apply-schema` endpoint
- Schema applies 7 uniqueness constraints + 2 indexes for performance
- Idempotent operation (safe to run multiple times)

### Phase 1C - Domain Models
- Defined Pydantic models for all graph entities:
  - Vendor, Facility, Service, Certification
  - Client, Project, Constraint, Carrier
- All models in `backend/app/models/`

### Phase 1D - Vendor Repository
- Implemented repository pattern for Neo4j operations
- Created `VendorRepository` with CRUD operations
- Added `/vendors` API endpoints (POST create/update, GET by ID)

### Phase 1E - Supporting Repositories
- Added `FacilityRepository`, `ServiceRepository`, `CertificationRepository`
- All repositories follow the same async pattern

### Phase 1F - Ingestion Endpoints
- Created batch ingestion API at `/ingestion/vendors/{vendor_id}/*`
- Supports bulk creation of facilities, services, certifications per vendor
- Uses MERGE patterns for idempotent upserts

### Phase 3-Lite - Structured Matching Engine
- **Skip Phase 2** temporarily (Client/Project modeling deferred)
- Implemented `/match/structured` endpoint for explicit criteria matching
- Implemented `/match/nl` endpoint for natural language query parsing
- Created `MockNLParser` for rule-based keyword extraction
- Built data seeding infrastructure with 10 demo vendors
- Created `seed_vendors.py` script and `vendors_seed.json` data file

### Phase 3-Lite Enhancements
- Added `Vendor-[:HOLDS]->Certification` relationship support
- Certification-based matching now functional (hard filter + scoring)
- Added `region` field to Vendor model for proper geographic matching
- Updated seed data with region values (us-east, us-west, us-central)
- Added `ScoreBreakdown` model showing per-criterion scores
- Matching response now includes `score_breakdown` with industry/region/cert scores

### OpenAI NL Parser Integration (Current)
- Implemented `OpenAINLParser` class using GPT-4o-mini model
- Structured JSON output with schema validation
- Automatic fallback to `MockNLParser` on API errors
- Factory pattern via `get_nl_parser()` selects parser based on `settings.llm_provider`
- Added `OPENAI_API_KEY` environment variable support
- Production-quality natural language understanding now available

### Frontend Match Demo Page
- Created `/match-demo` page in Next.js frontend
- Installed and configured Tailwind CSS (v4.1.17)
- Full-featured demo UI with:
  - Multi-line textarea for natural language queries
  - Loading states and error handling
  - Vendor result cards with score badges
  - Score breakdown display (industry/region/certs/total)
  - Matched reasons bullet lists
  - Collapsible raw JSON debug section
- CORS middleware added to backend for frontend access
- TypeScript types matching backend Pydantic models

### Advanced NL Parsing & Matching Refinements (2025-12-05)
Major overhaul of the query parsing and matching pipeline to handle complex natural language queries accurately.

**OpenAI Prompt Enhancements:**
- Added `backup-dr` industry mapping for "backup & disaster-recovery" queries
- Added `regions` field (separate from cities) for geographic region extraction (us-west, eu-central, etc.)
- Added `result_limit` and `sort_by` fields for query control ("top 2", "lowest risk first")
- Added service keyword mappings (immutable, disaster-recovery, wavelength, etc.)
- Included exact examples matching real user query patterns

**MatchingRequest Model Updates:**
- Added `regions: list[str]` for multi-region facility matching
- Added `result_limit: int | None` for controlling result count
- Added `sort_by: str | None` for custom sort orders (risk_asc, score_desc, name_asc)

**Matching Service Improvements:**
- `_industry_matches()`: Fuzzy matching with alias support (backup-dr ↔ backup, disaster-recovery)
- `_region_matches()`: Region-to-facility geo matching with variations
- `_service_matches()`: Keyword-based service matching (immutable → WORM, write-once, air-gap)
- Global vendors (region="global") now match any requested region with `*` indicator
- Fixed sorting: Score DESC primary, then risk/name as secondary sort
- Proper result limiting after scoring and sorting

**Database Cleanup:**
- Added DELETE /vendors/{vendor_id} endpoint
- Removed mock/duplicate vendors (digitalrealty, healthcaredc, budgetcolo)
- Fixed Service and Facility repositories to create proper relationships (OFFERS, HAS_FACILITY)

**Test Results:**
- Query: "backup & disaster-recovery vendor, immutable copies in US-West and EU-Central, ISO-27001, risk below 0.25, top 2"
- Result: Veeam (score 6), Acronis (score 5) - both correct backup-dr vendors with ISO 27001

---

## Key Decisions & Rationale

### 1. Risk Tolerance as 1-10 Scale
**Decision:** User-facing risk tolerance is an integer from 1 (very conservative) to 10 (any risk).

**Rationale:** Human-friendly scale that maps to internal 0.0-1.0 vendor risk scores. Formula: `threshold = max(0.20, risk_tolerance / 10.0)`. Floor of 0.20 ensures even "very conservative" still returns results.

### 2. Rule-Based NL Parser (MockNLParser)
**Decision:** Start with regex-based keyword extraction instead of LLM calls.

**Rationale:**
- No API key dependency for local development
- Predictable, testable behavior
- Fast response times (no network latency)
- Architecture supports swapping to LLM-backed parser later via factory pattern

### 3. Two-Layer Matching (Hard Filter + Scoring)
**Decision:** Cypher query does hard filtering (risk tolerance), Python does scoring.

**Rationale:**
- Database handles what it's good at (filtering large datasets)
- Application layer handles what it's good at (complex scoring logic)
- Keeps Cypher queries simple and maintainable
- Scoring can evolve without query changes

### 4. Matched Reasons as Explanatory Text
**Decision:** Each matched vendor includes human-readable `matched_reasons` list.

**Rationale:** Transparency for the vCISO advisor. Example reasons:
- "industry match: healthcare"
- "region match: us-east"
- "risk within tolerance: 0.15 <= 0.30"

### 5. Seed Data as Single JSON Bundle
**Decision:** `vendors_seed.json` contains complete vendor bundles (vendor + facilities + services + certs).

**Rationale:**
- Single source of truth for demo data
- Easy to version control and review
- Seeding script orchestrates API calls in correct order

### 6. Skipping Phase 2 (Client Modeling)
**Decision:** Implemented matching engine (Phase 3-Lite) before Client/Project APIs (Phase 2).

**Rationale:** Matching is the core value proposition. Demo-able sooner with seeded vendor data. Client modeling can be added when needed for full intake flow.

---

## Difficulties & Gotchas

### 1. Environment Variable Loading Path
**Problem:** `.env` file not found when running uvicorn from different directories.

**Solution:** Backend `.env` must live at `backend/.env`. When running uvicorn, ensure working directory is `backend/` or use absolute path in Pydantic settings.

**Gotcha:** If you run `uvicorn app.main:app` from the project root, it won't find `backend/.env`. Always `cd backend` first.

### 2. SSL Certificate Issues with Neo4j AuraDB
**Problem:** `CERTIFICATE_VERIFY_FAILED` errors on some systems when connecting to Neo4j Aura.

**Solution:** The Neo4j driver handles SSL automatically for `neo4j+s://` URIs. If issues persist:
- Ensure Python's `certifi` package is up to date
- Check system CA certificates
- AuraDB connections require the `+s` suffix (encrypted)

### 3. Relative Import Confusion
**Problem:** `ModuleNotFoundError` when running scripts directly.

**Solution:** Use `pip install -e .` (editable install) from `backend/` directory. This registers the `app` package properly. Then run scripts as modules: `python -m scripts.seed_vendors`.

### 4. Neo4j Parameter Binding Syntax
**Problem:** Initial Cypher queries used string formatting which is unsafe and error-prone.

**Solution:** Always use `$parameter_name` syntax in Cypher with parameter dict. Example:
```python
query = "MATCH (v:Vendor) WHERE v.risk_score_guess <= $threshold RETURN v"
result = await session.run(query, {"threshold": 0.3})
```

### 5. Async Generator Consumption
**Problem:** Neo4j async results are single-use iterators. Attempting to iterate twice yields nothing.

**Solution:** Consume results into a list immediately if you need multiple passes:
```python
records = [record async for record in result]
```

### 6. Certification Nodes Without Relationships (RESOLVED)
**Problem:** Certifications were ingested as standalone nodes but not linked to vendors.

**Solution:** Updated `CertificationRepository.upsert_certification_for_vendor()` to create `(v:Vendor)-[:HOLDS]->(c:Certification)` relationships. Ingestion endpoint now uses this method.

**Status:** Resolved. Re-run `seed_vendors.py` to populate relationships.

### 7. Region Mismatch Between Parser and Data (RESOLVED)
**Problem:** NL parser extracts regions like "us-east", but vendor data used "USA" as `hq_country`.

**Solution:** Added explicit `region` field to Vendor model. Updated seed data with proper region values. Matching service now uses `v.region` instead of `v.hq_country`.

**Status:** Resolved. Region matching now functional.

### 8. Certification Substring Matching Not Working (RESOLVED)
**Problem:** NL parser extracts "SOC 2" but seed data has "SOC 2 Type II". Exact string matching returned 0 vendors for partial cert names.

**Solution:** Changed certification matching to case-insensitive substring matching:
- Added helper functions `_cert_matches()`, `_count_cert_matches()`, `_find_matching_cert()` in `matching_service.py`
- Modified Cypher query to use `toLower()` and `CONTAINS` for substring matching
- Now "SOC 2" matches "SOC 2 Type II", "SOC 2 Type I", etc.
- Now "iso" matches "ISO 27001", etc.

**Gotcha:** After modifying `matching_service.py`, a full server restart may be required for changes to take effect (hot reload alone may not be sufficient on some systems).

**Status:** Resolved. Substring certification matching now functional.

---

## Completed Features

### Core Infrastructure
- [x] Neo4j async driver with connection pooling
- [x] Pydantic settings with `.env` support
- [x] Health check endpoints (`/health`, `/health/neo4j`)
- [x] Schema bootstrap (`/admin/apply-schema`)

### Domain Layer
- [x] Pydantic models for Vendor, Facility, Service, Certification
- [x] Repository pattern for all entities
- [x] Vendor CRUD API (`POST /vendors`, `GET /vendors/{id}`)

### Ingestion
- [x] Batch facility ingestion (`POST /ingestion/vendors/{id}/facilities`)
- [x] Batch service ingestion (`POST /ingestion/vendors/{id}/services`)
- [x] Batch certification ingestion (`POST /ingestion/vendors/{id}/certifications`)
- [x] Idempotent MERGE operations

### Matching Engine
- [x] Structured matching endpoint (`POST /match/structured`)
- [x] Natural language matching endpoint (`POST /match/nl`)
- [x] Risk tolerance hard filtering (1-10 scale)
- [x] Industry and region scoring (+1 point each)
- [x] Certification-based filtering and scoring (via HOLDS relationship)
- [x] Case-insensitive substring cert matching ("SOC 2" matches "SOC 2 Type II")
- [x] Matched reasons explanations
- [x] Score breakdown (industry/region/certs/total)
- [x] Top-20 results with score-based ranking

### NL Parser
- [x] MockNLParser with regex patterns
- [x] Certification extraction (HIPAA, SOC 2, ISO 27001, etc.)
- [x] Region extraction (us-east, us-west, eu-west, apac)
- [x] Industry extraction (colocation, healthcare, cloud, etc.)
- [x] Service extraction (colocation, DR, managed-services, etc.)
- [x] Risk tolerance extraction (conservative → aggressive)
- [x] Factory pattern for LLM parser integration
- [x] OpenAINLParser with GPT-4o-mini (structured JSON output)
- [x] Automatic fallback to MockNLParser on API errors

### Data Seeding
- [x] `seed_vendors.py` seeding script
- [x] `vendors_seed.json` with 10 vendors, 42 facilities
- [x] Vendor portfolio spanning risk profiles (0.15 to 0.72)
- [x] Healthcare-focused vendor (HealthcareDC)
- [x] Budget option (BudgetColo)
- [x] Region field populated for all vendors (us-east, us-west, us-central)

### Frontend
- [x] Next.js 14 App Router setup
- [x] Tailwind CSS v4.1.17 configured
- [x] `/match-demo` page with full matching UI
- [x] TypeScript types for API response shapes
- [x] Loading states and error handling
- [x] Vendor result cards with scores and reasons
- [x] Collapsible debug JSON viewer
- [x] CORS enabled for localhost:3000

---

## Known Limitations & TODOs

### High Priority
1. ~~**No Vendor-Certification relationships**~~ - **RESOLVED** - Certification nodes now linked via HOLDS relationship.

2. ~~**Region mismatch**~~ - **RESOLVED** - Added explicit `region` field to Vendor model.

3. ~~**Mock NL parser only**~~ - **RESOLVED** - OpenAINLParser implemented with GPT-4o-mini.

4. **No service filtering** - `required_services` is extracted but not used in matching logic.

### Medium Priority
5. ~~**No score breakdown**~~ - **RESOLVED** - API now returns `score_breakdown` with per-criterion scores.

6. **No Client/Project modeling** - Phase 2 skipped. Cannot store client requirements persistently.

7. **No semantic search** - `text_query` field reserved but unused. No vector embeddings.

8. **No collaborative filtering** - No historic client ratings or recommendations.

### Low Priority
9. **Limited test coverage** - No automated tests for matching logic.

10. ~~**No frontend**~~ - **RESOLVED** - Match demo page at `/match-demo` with full UI.

11. **Hardcoded scoring weights** - All matches worth +1 point, no configurable weights.

12. **Re-seed required** - After code changes, run `python -m scripts.seed_vendors` to populate HOLDS relationships and region data.

---

## Next Steps

### Recently Completed
- [x] Add Vendor-Certification relationships (HOLDS) - **Done**
- [x] Fix region matching (add region field) - **Done**
- [x] Add score breakdown to response - **Done**
- [x] Implement OpenAI NL Parser (GPT-4o-mini) - **Done**
- [x] Build frontend match demo page - **Done**
- [x] Add CORS middleware for frontend access - **Done**
- [x] Configure Tailwind CSS in frontend - **Done**

### Recommended Immediate Tasks (Priority Order)

#### 1. Add Service Filtering
**Goal:** Use `required_services` in matching logic.

**Tasks:**
- Update matching service to filter/score by services
- Similar pattern to certification matching
- Services may need `OFFERS` relationship to vendors

**Impact:** Medium - Completes the structured matching criteria.

#### 2. Client/Project Modeling (Phase 2)
**Goal:** Persist client requirements and project context.

**Tasks:**
- Implement Client repository and API endpoints
- Implement Project repository with Constraint relationships
- Link projects to matching results for tracking

**Impact:** Medium-High - Enables full vCISO workflow.

#### 3. Add Automated Tests
**Goal:** Ensure matching logic correctness.

**Tasks:**
- Unit tests for `match_vendors()` with mock Neo4j
- Tests for MockNLParser extraction patterns
- Integration tests for `/match/structured` and `/match/nl` endpoints

**Impact:** Medium - Confidence in code changes.

#### 4. Semantic Search / Vector Embeddings
**Goal:** Handle fuzzy matching and semantic similarity.

**Tasks:**
- Add vector index to Neo4j for vendor descriptions
- Implement embedding generation (OpenAI or local model)
- Use `text_query` field for semantic search

**Impact:** High - Production-quality fuzzy matching.

#### 5. Deep Research Integration (Phase 4)
**Goal:** Augment matching with real-time vendor research.

**Tasks:**
- Integrate Tavily API for web search
- LangGraph orchestration for research workflow
- Cache research results in graph

**Impact:** High - Differentiated AI capability.

---

## Architecture Reference

```
backend/
   app/
      core/           # Config, settings
      db/             # Neo4j driver, schema
      models/         # Pydantic domain models
      repositories/   # Neo4j data access
      routers/        # FastAPI endpoints
      services/       # Business logic
      main.py         # App entrypoint
   scripts/            # Utility scripts (seeding)
   data/               # Seed data files
   .env                # Environment variables
```

See `docs/ARCHITECTURE.md` for full system diagram.

---

## Useful Commands

```bash
# Start backend (from backend/)
cd backend
pip install -e .
uvicorn app.main:app --reload

# Seed demo data (backend must be running)
python -m scripts.seed_vendors

# Test structured matching
curl -X POST http://localhost:8000/match/structured \
  -H "Content-Type: application/json" \
  -d '{"industry": "colocation", "risk_tolerance": 5}'

# Test NL matching
curl -X POST http://localhost:8000/match/nl \
  -H "Content-Type: application/json" \
  -d '{"query": "I need HIPAA compliant colocation with low risk"}'

# Test certification-based matching
curl -X POST http://localhost:8000/match/structured \
  -H "Content-Type: application/json" \
  -d '{"required_certs": ["HIPAA", "SOC 2 Type II"], "risk_tolerance": 3}'

# Test region matching
curl -X POST http://localhost:8000/match/structured \
  -H "Content-Type: application/json" \
  -d '{"region": "us-east", "industry": "colocation"}'
```

---

## Files Changed in This Session

**Backend - Modified:**
- `backend/app/repositories/certification_repository.py` - Added `upsert_certification_for_vendor()` with HOLDS relationship
- `backend/app/routers/ingestion.py` - Updated certification ingestion to use new method
- `backend/app/services/matching_service.py` - Added cert filtering/scoring, region field, score breakdown
- `backend/app/services/nl_parser_service.py` - Added `OpenAINLParser` class with GPT-4o-mini integration
- `backend/app/models/matching.py` - Added `ScoreBreakdown` model
- `backend/app/models/__init__.py` - Exported `ScoreBreakdown`
- `backend/app/models/vendor.py` - Added `region` field
- `backend/app/repositories/vendor_repository.py` - Persist/retrieve `region` field
- `backend/app/main.py` - Added CORS middleware for frontend access
- `backend/data/vendors_seed.json` - Added `region` to all 10 vendors

**Frontend - New/Modified:**
- `frontend/tailwind.config.ts` - Tailwind CSS configuration
- `frontend/postcss.config.mjs` - PostCSS configuration
- `frontend/app/globals.css` - Tailwind directives
- `frontend/app/layout.tsx` - Updated to import globals.css
- `frontend/app/match-demo/types.ts` - TypeScript interfaces for API types
- `frontend/app/match-demo/page.tsx` - Match demo page component

---

## Running the Application

### Backend
```bash
cd backend
pip install -e .
uvicorn app.main:app --reload
# Runs on http://127.0.0.1:8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:3000
# Match demo at http://localhost:3000/match-demo
```

### Seed Data (backend must be running)
```bash
cd backend
python -m scripts.seed_vendors
```

---

*Last updated by: Claude Code (feature/matching-engine-v1)*
