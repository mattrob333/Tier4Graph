# System Diagram (Text-Based)

## Core Architecture
```
[Next.js Frontend]
       |
       v
[FastAPI Backend] ---> [LangGraph Workflows]
       |
       v
[Neo4j AuraDB] <----> [Embedding Services]

FastAPI <--> Tavily Research API
FastAPI <--> LLM Providers
```

## Flow Example: Matching Request
```
Client Intake --> Profile Extraction --> Neo4j Storage
       |
       v
Hard Filter (Cypher)  
       |
       v
Semantic Ranking (Vectors)  
       |
       v
Collaborative Filtering (Graph History)
       |
       v
Deep Research Agent
       |
       v
Proposal Generator
```
