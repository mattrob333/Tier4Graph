# Backend (FastAPI) Overview

## Tech Stack
- Python 3.11
- FastAPI
- Neo4j
- Pydantic Settings
- LangGraph
- Uvicorn

## Run (local)
uvicorn app.main:app --reload

## Key Directories
- app/routers — API endpoints
- app/services — business logic
- app/repositories — Neo4j access
- app/models — Pydantic models
- app/db — Neo4j driver and schema

## Invariants
- Never mix routers, business logic, and DB logic
- All graph access goes through repositories
