# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

The Cognitive Procurement Engine (CPE) is an AI-native IT procurement decision platform that models vendors, facilities, services, certifications, clients, and projects in a Neo4j graph database with semantic reasoning and agentic workflows.

Reference documentation:
- `docs/ARCHITECTURE.md` - Full system blueprint
- `docs/ONTOLOGY.md` - Graph schema definitions
- `docs/DEV_CONTEXT.md` - AI agent behavioral guidelines
- `docs/AI_DEVELOPER_GUIDE.md` - Coding style and patterns

---

## Completed Phases (Checklist)

- [x] **Phase 1A** - Neo4j driver, config, health endpoints
- [x] **Phase 1B** - Schema bootstrap (`/admin/apply-schema`)
- [x] **Phase 1C** - Domain models (Vendor, Facility, Service, Certification, Client, Project, Constraint)
- [x] **Phase 1D** - Vendor repository + `/vendors` API
- [x] **Phase 1E** - Facility/Service/Certification repositories
- [x] **Phase 1F** - Ingestion endpoints (`/ingestion/vendors/{vendor_id}/...`)

---

## Current Capabilities Summary

The backend currently supports:

- **Health endpoints**: `/health` (basic) and `/health/neo4j` (database connectivity)
- **Schema management**: `/admin/apply-schema` applies 7 constraints + 2 indexes
- **Vendor CRUD**: Create/update vendors via `POST /vendors`, retrieve via `GET /vendors/{vendor_id}`
- **Batch ingestion**: Facilities, services, and certifications via `/ingestion/vendors/{vendor_id}/*`

All graph operations use the repository pattern with async Neo4j driver.

---

## Guidelines for Future Claude Sessions

### Always Read First
- `README.md`
- `CLAUDE.md` (this file)
- `docs/ARCHITECTURE.md` (if present)
- `docs/ONTOLOGY.md` (if present)
- `docs/DEV_CONTEXT.md` and `docs/AI_DEVELOPER_GUIDE.md` (if present)

### Never Do Without Explicit Instruction
- Change the graph schema or relationship names
- Modify the Neo4j driver pattern in `app/db/neo4j.py`
- Restructure the repository layout or create new top-level folders
- Add dependencies without approval

### Preferred Workflow
1. **Plan** - Outline approach and affected files
2. **Show plan** - Present to user for review
3. **Await approval** - Do not proceed without confirmation
4. **Implement** - Small, reviewable changes (4-5 files max per operation)

---

## Next Phases (High Level)

- **Phase 2** - Client modeling & vCISO intake (Client/Project/Constraint repositories + APIs)
- **Phase 3** - Matching engine (hard filter Cypher + semantic ranking + collaborative filtering)
- **Phase 4** - Deep research (Tavily + LLM, LangGraph orchestration)
- **Phase 5** - Frontend UI (Advisor Command Center, Graph Explorer, Proposal Generator)

---

## Development Commands

### Backend (FastAPI)
```bash
cd backend
pip install -e .
uvicorn app.main:app --reload
```

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
npm run build
npm run lint
```

### Docker (full stack)
```bash
docker-compose up
```
Backend runs on port 8000, frontend on port 3000.

---

## Architecture

### Tech Stack
- **Frontend**: Next.js 14 (App Router), TypeScript, TailwindCSS, ShadcnUI
- **Backend**: FastAPI (async), Python 3.11+, Pydantic
- **Database**: Neo4j AuraDB (graph + vector indexing)
- **Orchestration**: LangGraph
- **LLMs**: Claude, GPT
- **Search**: Tavily API

### Backend Structure (`/backend/app/`)
- `routers/` - API endpoints only
- `services/` - business logic
- `repositories/` - Neo4j database access
- `models/` - Pydantic domain models
- `db/` - Neo4j driver and schema
- `orchestration/` - LangGraph workflows

### Frontend Structure (`/frontend/`)
- `app/` - Next.js App Router pages
- `components/` - React components
- `lib/` - Utilities and API clients

---

## Graph Ontology

Node types: Vendor, Facility, Service, Certification, Client, Project, Constraint, Carrier

Key relationships:
- `VENDOR OWNS FACILITY`
- `FACILITY CONNECTED_TO CARRIER`
- `CLIENT REQUIRES CONSTRAINT`
- `CLIENT RATED VENDOR`

Reference `docs/ONTOLOGY.md` before modifying any graph schema.

---

## Critical Rules

1. **Separation of concerns**: No DB logic in routers, no business logic in endpoints. All graph operations through repositories only.
2. **Strict typing**: Python uses Pydantic models for all domain objects; TypeScript strict mode enabled.
3. **Environment variables**: Load via Pydantic settings only. Backend `.env` lives in `backend/.env`.
4. **Logging**: Use loguru, never `print()`.
5. **Schema changes**: Always check `docs/ONTOLOGY.md` first; never modify relationship names without approval.
6. **Folder structure**: Do not create new top-level folders or modify the existing structure.
7. **Multi-file edits**: Limit to 4-5 files per operation unless approved.
