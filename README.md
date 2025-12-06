# Neo4j + FastAPI + OpenAI Boilerplate

> **Also known as:** Cognitive Procurement Engine (CPE)

A production-ready boilerplate for building AI-powered graph database applications. Features natural language query parsing with OpenAI GPT, Neo4j graph database for relationship-based data, and a Next.js frontend.

## 🚀 Use as a Boilerplate

```bash
# Clone for your own project
git clone https://github.com/mattrob333/Tier4Graph.git my-new-project
cd my-new-project

# See customization guide
cat docs/BOILERPLATE_CUSTOMIZATION.md
```

**See [`docs/BOILERPLATE_CUSTOMIZATION.md`](docs/BOILERPLATE_CUSTOMIZATION.md)** for step-by-step instructions on:
- 🤖 Swapping AI models (GPT-4.1, GPT-4o, Claude)
- 📝 Customizing the NL parsing prompt
- 📊 Modifying the Neo4j schema
- 🔍 Writing custom Cypher queries
- 🎨 Adapting the frontend

---

## About This Project

An AI-native IT procurement decision platform built on a Neo4j graph database with a FastAPI backend. CPE models vendors, facilities, services, certifications, clients, and projects to enable intelligent vendor matching and procurement recommendations.

## Repository Structure

```
cpe_repo/
├── backend/       FastAPI service, Neo4j integration, LangGraph workflows
├── frontend/      Next.js 14 App Router UI (coming soon)
├── docs/          Architecture, ontology, and system design
└── docker-compose.yml
```

See `docs/ARCHITECTURE.md` for the full system blueprint.

---

## Current Backend Capabilities (MVP)

The backend currently supports:

- **Neo4j Connectivity** - Async driver with startup/shutdown lifecycle hooks
- **Schema Bootstrap** - Constraints and indexes applied via `/admin/apply-schema`
- **Vendor CRUD** - Create/update vendors and retrieve by ID
- **Repository Layer** - Facility, Service, and Certification repositories
- **Ingestion Endpoints** - Batch upsert of facilities, services, and certifications per vendor

---

## Tech Stack

| Layer       | Technology                      |
|-------------|---------------------------------|
| Backend     | FastAPI, Python 3.11+           |
| Database    | Neo4j AuraDB (async driver)     |
| Models      | Pydantic v2                     |
| Server      | Uvicorn                         |

> **Note**: Frontend (Next.js) and agent orchestration (LangGraph) will be added in future phases.

---

## API Summary (Backend)

| Method | Endpoint                                        | Description                      |
|--------|-------------------------------------------------|----------------------------------|
| GET    | `/health`                                       | Basic health check               |
| GET    | `/health/neo4j`                                 | Neo4j connectivity check         |
| POST   | `/admin/apply-schema`                           | Apply graph constraints/indexes  |
| POST   | `/vendors`                                      | Create or update a vendor        |
| GET    | `/vendors/{vendor_id}`                          | Get vendor by ID                 |
| POST   | `/ingestion/vendors/{vendor_id}/facilities`     | Batch upsert facilities          |
| POST   | `/ingestion/vendors/{vendor_id}/services`       | Batch upsert services            |
| POST   | `/ingestion/vendors/{vendor_id}/certifications` | Batch upsert certifications      |

---

## Getting Started (Backend)

### Prerequisites

- Python 3.11+
- Neo4j AuraDB instance (or local Neo4j)

### Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -e .
```

### Environment Variables

Create a `.env` file in the `backend/` directory (not at repo root):

```env
NEO4J_URI=neo4j+s://your-aura-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
```

### Run the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Visit `/docs` for the interactive Swagger UI.

---

## Next Steps (High-Level)

- **Phase 2** - Client modeling & vCISO intake (Client/Project/Constraint APIs)
- **Phase 3** - Matching engine (hard filter Cypher + semantic ranking + collaborative filtering)
- **Phase 4** - Deep research (Tavily + LLM, LangGraph orchestration)
- **Phase 5** - Frontend UI (Advisor Command Center, Graph Explorer, Proposal Generator)

---

## Documentation

- `docs/ARCHITECTURE.md` - Full system blueprint
- `docs/ONTOLOGY.md` - Graph schema definitions
- `docs/DEV_CONTEXT.md` - AI agent behavioral guidelines
- `docs/AI_DEVELOPER_GUIDE.md` - Coding style and patterns
