# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Cognitive Procurement Engine (CPE) is an AI-native IT procurement decision platform that models vendors, facilities, services, certifications, clients, and projects in a Neo4j graph database with semantic reasoning and agentic workflows.

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

## Architecture

### Tech Stack
- **Frontend**: Next.js 14 (App Router), TypeScript, TailwindCSS, ShadcnUI
- **Backend**: FastAPI (async), Python 3.11+, Pydantic
- **Database**: Neo4j AuraDB (graph + vector indexing)
- **Orchestration**: LangGraph
- **LLMs**: Claude, GPT
- **Search**: Tavily API

### Backend Structure (`/backend/app/`)
- `routers/` — API endpoints only
- `services/` — business logic
- `repositories/` — Neo4j database access
- `models/` — Pydantic domain models
- `db/` — Neo4j driver and schema
- `orchestration/` — LangGraph workflows

### Frontend Structure (`/frontend/`)
- `app/` — Next.js App Router pages
- `components/` — React components
- `lib/` — Utilities and API clients

## Graph Ontology

Node types: Vendor, Facility, Service, Certification, Client, Project, Constraint, Carrier

Key relationships:
- `VENDOR OWNS FACILITY`
- `FACILITY CONNECTED_TO CARRIER`
- `CLIENT REQUIRES CONSTRAINT`
- `CLIENT RATED VENDOR`

Reference `docs/ONTOLOGY.md` before modifying any graph schema.

## Critical Rules

1. **Separation of concerns**: No DB logic in routers, no business logic in endpoints. All graph operations through repositories only.
2. **Strict typing**: Python uses Pydantic models for all domain objects; TypeScript strict mode enabled.
3. **Environment variables**: Load via Pydantic settings only.
4. **Logging**: Use loguru, never `print()`.
5. **Schema changes**: Always check `docs/ONTOLOGY.md` first; never modify relationship names without approval.
6. **Folder structure**: Do not create new top-level folders or modify the existing structure.
7. **Multi-file edits**: Limit to 4-5 files per operation unless approved.

## Key Documentation

- `docs/ARCHITECTURE.md` — Full system blueprint
- `docs/ONTOLOGY.md` — Graph schema definitions
- `docs/DEV_CONTEXT.md` — AI agent behavioral guidelines
- `docs/AI_DEVELOPER_GUIDE.md` — Coding style and patterns
- `docs/DEV_WARNINGS.md` — Prohibited actions
