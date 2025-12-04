# Cognitive Procurement Engine (CPE)

Welcome to the Cognitive Procurement Engine (CPE) repository.  
This platform is an AI-native IT procurement decision system built on:

- Neo4j AuraDB (graph + vector index)  
- FastAPI backend  
- Next.js frontend  
- LangGraph multi-agent workflows  
- LLM reasoning (Claude 4.5 Sonnet, GPT-5.1 Mini)  
- Tavily live research  

## Key Features
- Vendor ingestion pipeline  
- vCISO conversational intake  
- 3-layer vendor matching engine  
- Deep research agent  
- Advisor dashboard & proposal generator  

## Documentation
- `ARCHITECTURE.md` – Full blueprint of the system  
- `ONTOLOGY.md` – Graph data model  
- `REPO_STRUCTURE.md` – Folder layout & conventions  
- `CONTRIBUTING.md` – Contribution workflow  

## Getting Started
```bash
backend: uvicorn app.main:app --reload
frontend: pnpm dev
```

## License
Proprietary – Tier 4 Intelligence
