# Cognitive Procurement Engine (CPE)

An AI-native IT procurement decision platform built on a Neo4j graph database with a FastAPI backend. CPE uses **GPT-4** for natural language query parsing to help vCISO advisors match clients with optimal datacenter/IT vendors based on compliance requirements, risk tolerance, geographic needs, and service requirements.

## 🚀 Key Features

- **Natural Language Vendor Search** - Ask questions like *"Find backup & disaster-recovery vendors in US-West and EU-Central with ISO-27001, risk below 0.25, top 2 by lowest risk"*
- **AI-Powered Query Parsing** - GPT-4 extracts structured criteria from free-form queries
- **Multi-Criteria Scoring** - Industry, regions, certifications, services, and facilities
- **Neo4j Graph Database** - Relationship-based matching for complex vendor networks
- **Live Demo UI** - Next.js frontend at `/match-demo`

## Repository Structure

```
Tier4Graph/
├── backend/           FastAPI service, Neo4j integration, AI matching engine
│   ├── app/
│   │   ├── services/  # nl_parser_service.py (GPT-4), matching_service.py
│   │   ├── models/    # Pydantic schemas
│   │   └── routers/   # API endpoints
│   └── data/          # Vendor seed data (30+ real vendors)
├── frontend/          Next.js 14 + Tailwind CSS
│   └── app/match-demo # Interactive vendor matching demo
├── docs/              Architecture and engineering logs
└── docker-compose.yml
```

---

## 🤖 AI-Powered Matching Engine

### How It Works

1. **User submits natural language query** → `/match/nl` endpoint
2. **GPT-4 parses query** → Extracts industry, regions, certs, services, risk threshold, sort order
3. **Neo4j Cypher queries** → Fetches vendors with related facilities, services, certifications
4. **Scoring engine** → Ranks vendors by match quality across all criteria
5. **Results returned** → With score breakdown and matched reasons

### Supported Query Criteria

| Criteria | Example |
|----------|---------|
| **Industry** | "backup & disaster-recovery", "colocation", "network" |
| **Regions** | "US-West", "EU-Central", "APAC" |
| **Cities** | "Chicago", "Dallas", "Ashburn" |
| **Certifications** | "SOC 2", "HIPAA", "ISO 27001", "PCI DSS" |
| **Services** | "immutable backups", "wavelengths", "dark fiber" |
| **Risk Threshold** | "risk below 0.25" |
| **Result Control** | "top 3", "lowest risk first" |

---

## Tech Stack

| Layer       | Technology                      |
|-------------|---------------------------------|
| Backend     | FastAPI, Python 3.11+           |
| Database    | Neo4j AuraDB (async driver)     |
| AI/NLP      | OpenAI GPT-4                    |
| Models      | Pydantic v2                     |
| Frontend    | Next.js 14, Tailwind CSS        |
| Server      | Uvicorn                         |

---

## API Summary (Backend)

### Matching Endpoints (AI-Powered)

| Method | Endpoint          | Description                                      |
|--------|-------------------|--------------------------------------------------|
| POST   | `/match/nl`       | **Natural language vendor matching** (GPT-4)     |
| POST   | `/match/vendors`  | Structured vendor matching (direct criteria)     |

### Vendor Management

| Method | Endpoint                                        | Description                      |
|--------|-------------------------------------------------|----------------------------------|
| POST   | `/vendors`                                      | Create or update a vendor        |
| GET    | `/vendors/{vendor_id}`                          | Get vendor by ID                 |
| DELETE | `/vendors/{vendor_id}`                          | Delete a vendor                  |

### Ingestion & Admin

| Method | Endpoint                                        | Description                      |
|--------|-------------------------------------------------|----------------------------------|
| POST   | `/ingestion/vendors/{vendor_id}/facilities`     | Batch upsert facilities          |
| POST   | `/ingestion/vendors/{vendor_id}/services`       | Batch upsert services            |
| POST   | `/ingestion/vendors/{vendor_id}/certifications` | Batch upsert certifications      |
| POST   | `/admin/apply-schema`                           | Apply graph constraints/indexes  |
| GET    | `/health`                                       | Basic health check               |
| GET    | `/health/neo4j`                                 | Neo4j connectivity check         |

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

Create a `.env` file at the repo root:

```env
# Neo4j Connection
NEO4J_URI=neo4j+s://your-aura-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j

# AI/LLM Configuration
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-api-key-here

# Frontend
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### Run the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Visit `/docs` for the interactive Swagger UI.

---

## Getting Started (Frontend)

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000/match-demo` for the interactive vendor matching demo.

---

## Development Roadmap

### ✅ Completed
- **Phase 1** - Neo4j foundation, schema, vendor/facility/service/certification models
- **Phase 3-Lite** - AI-powered matching engine with GPT-4 NL parsing
- **Frontend Demo** - Match demo page with Tailwind CSS

### 🔜 Upcoming
- **Phase 2** - Client modeling & vCISO intake (Client/Project/Constraint APIs)
- **Phase 4** - Deep research (Tavily + LLM, LangGraph orchestration)
- **Phase 5** - Full Frontend UI (Advisor Command Center, Graph Explorer, Proposal Generator)

---

## Documentation

- `docs/ENGINEERING_LOG.md` - Development history and technical decisions
- `docs/ARCHITECTURE.md` - Full system blueprint
- `docs/ONTOLOGY.md` - Graph schema definitions
- `docs/DEV_CONTEXT.md` - AI agent behavioral guidelines
- `docs/AI_DEVELOPER_GUIDE.md` - Coding style and patterns
