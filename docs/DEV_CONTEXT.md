# Developer Context for AI Coding Agents

This repository contains the Cognitive Procurement Engine (CPE), an AI-native IT procurement decision platform.

AI coding agents (Claude, GPT, Windsurf Agents) must follow these rules:

## 1. Core System Boundaries
- Frontend: Next.js 14 App Router, TypeScript, Tailwind, ShadcnUI
- Backend: FastAPI (async), Python 3.11+
- Database: Neo4j AuraDB (graph + vector indexing)
- Orchestration: LangGraph
- LLM Providers: Claude 4.5 Sonnet, GPT-5.1 mini
- Embeddings: OpenAI or Anthropic embeddings
- Search: Tavily API

## 2. Folder Structure Contract
- `/backend` contains *all backend logic* including ingestion, matching, research, orchestration, and Neo4j integration.
- `/frontend` contains all UI.
- `/docs` contains all architectural specs.
- AI should never create or require new top-level folders without asking.

## 3. Critical Invariants
AI must maintain:
- Strict typing (Python + TS)
- Pydantic models for all domain objects
- Clean separation: no DB logic in routers, no business logic in endpoints
- All env vars loaded via Pydantic settings
- All graph operations through repositories only
- Node/relationship names must follow the ontology in `ONTOLOGY.md`

## 4. When In Doubt
AI coding agents must:
- Refer to `docs/ARCHITECTURE.md`
- Refer to `docs/ONTOLOGY.md`
- Ask before changing schemas or relationships
- Ask before adding dependencies
- Explain their plan before writing code

## 5. Output Requirements
For any feature:
1. Create a plan
2. Create/update files
3. Generate tests
4. Provide a quick “how to test this manually” note

## 6. Project Goal
Build in vertical slices:
- ingestion
- extraction
- graph loading
- intake
- matching engine
- deep research
- advisor UI
- proposal generation
