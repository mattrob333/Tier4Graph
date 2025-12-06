# Neo4j + FastAPI + OpenAI Boilerplate Customization Guide

> **Stack:** FastAPI (async) + Neo4j (graph DB) + OpenAI GPT + Next.js (frontend)
> 
> This guide explains how to adapt this boilerplate for your own domain.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Customizing the AI Model](#customizing-the-ai-model)
3. [Customizing the OpenAI Prompt](#customizing-the-openai-prompt)
4. [Customizing the Neo4j Schema](#customizing-the-neo4j-schema)
5. [Customizing Cypher Queries](#customizing-cypher-queries)
6. [Customizing Domain Models](#customizing-domain-models)
7. [File Reference](#file-reference)

---

## Quick Start

```bash
# 1. Clone this repo
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git my-project
cd my-project

# 2. Set up environment
cp .env.example .env
# Edit .env with your Neo4j and OpenAI credentials

# 3. Install backend
cd backend
pip install -e .

# 4. Install frontend
cd ../frontend
npm install

# 5. Start Neo4j (Docker)
docker-compose up -d

# 6. Run backend
cd ../backend
uvicorn app.main:app --reload

# 7. Run frontend (new terminal)
cd frontend
npm run dev
```

---

## Customizing the AI Model

### File: `backend/app/services/nl_parser_service.py`

### Current Model (GPT-4o)
```python
# Line ~311
response = await self.client.chat.completions.create(
    model="gpt-4o",  # <-- CHANGE THIS
    messages=[...],
    response_format={"type": "json_object"},
    temperature=0.0,
    max_tokens=512,
)
```

### Available Models

| Model | Best For | Cost |
|-------|----------|------|
| `gpt-4o` | General purpose, good balance | Medium |
| `gpt-4o-mini` | Faster, cheaper, good for simple queries | Low |
| `gpt-4.1` | Best instruction following (RECOMMENDED) | Medium |
| `gpt-4-turbo` | Large context window | Higher |
| `o1-preview` | Complex reasoning | Highest |

### To Switch to GPT-4.1
```python
response = await self.client.chat.completions.create(
    model="gpt-4.1",  # Excellent instruction following
    messages=[...],
    response_format={"type": "json_object"},
    temperature=0.0,
    max_tokens=512,
)
```

### Environment Variable Approach (Recommended)
```python
# In config.py, add:
openai_model: str = "gpt-4.1"

# In nl_parser_service.py:
from app.core.config import settings
model=settings.openai_model
```

Then in `.env`:
```
OPENAI_MODEL=gpt-4.1
```

---

## Customizing the OpenAI Prompt

### File: `backend/app/services/nl_parser_service.py`

### Location: `OpenAINLParser.SYSTEM_PROMPT` (Line ~222)

### Prompt Structure

```python
SYSTEM_PROMPT = """You are an expert query parser for [YOUR DOMAIN].

CONTEXT: Users search for [WHAT THEY'RE SEARCHING] in a Neo4j graph database containing:
- [Node Type 1] with properties: [list properties]
- [Node Type 2] with properties: [list properties]
- Relationships: [list relationship types]

Return a JSON object:
{
  "[field1]": string or null - [description and valid values],
  "[field2]": array of strings - [description],
  "[field3]": integer or null - [description with scale],
  ...
}

EXAMPLES:

Query: "[example user query 1]"
→ {"field1": "value", "field2": ["a", "b"], ...}

Query: "[example user query 2]"  
→ {"field1": null, "field2": [], ...}

RULES:
- [Rule 1: How to handle X]
- [Rule 2: How to normalize Y]
- Return ONLY valid JSON"""
```

### Example: E-commerce Product Search

```python
SYSTEM_PROMPT = """You are an expert query parser for an e-commerce product search.

CONTEXT: Users search for products in a Neo4j graph database containing:
- Products with categories: electronics, clothing, home, sports, beauty
- Brands: Apple, Nike, Samsung, Sony, etc.
- Price ranges and ratings

Return a JSON object:
{
  "category": string or null - Product category (electronics, clothing, home, sports, beauty),
  "brand": string or null - Brand name if mentioned,
  "price_max": number or null - Maximum price in dollars,
  "min_rating": number or null - Minimum star rating (1-5),
  "features": array of strings - Specific features mentioned (wireless, waterproof, etc.),
  "sort_by": string or null - "price_asc", "price_desc", "rating_desc", "newest"
}

EXAMPLES:

Query: "wireless headphones under $100 with good reviews"
→ {"category": "electronics", "brand": null, "price_max": 100, "min_rating": 4, "features": ["wireless"], "sort_by": null}

Query: "Nike running shoes, highest rated"
→ {"category": "sports", "brand": "Nike", "price_max": null, "min_rating": null, "features": ["running"], "sort_by": "rating_desc"}

RULES:
- "cheap" or "budget" → price_max: 50
- "good reviews" or "well reviewed" → min_rating: 4
- Return ONLY valid JSON"""
```

---

## Customizing the Neo4j Schema

### File: `backend/app/routers/admin.py`

### Current Schema (Vendor Domain)
```python
SCHEMA_STATEMENTS = [
    "CREATE CONSTRAINT vendor_id IF NOT EXISTS FOR (v:Vendor) REQUIRE v.vendor_id IS UNIQUE",
    "CREATE CONSTRAINT facility_id IF NOT EXISTS FOR (f:Facility) REQUIRE f.facility_id IS UNIQUE",
    ...
]
```

### Template for New Domain

```python
SCHEMA_STATEMENTS = [
    # Uniqueness constraints (required for MERGE operations)
    "CREATE CONSTRAINT [node]_id IF NOT EXISTS FOR (n:[Node]) REQUIRE n.[node]_id IS UNIQUE",
    
    # Indexes for frequently queried properties
    "CREATE INDEX [node]_[property] IF NOT EXISTS FOR (n:[Node]) ON (n.[property])",
    
    # Example: E-commerce
    "CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE",
    "CREATE CONSTRAINT brand_name IF NOT EXISTS FOR (b:Brand) REQUIRE b.name IS UNIQUE",
    "CREATE CONSTRAINT category_name IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE",
    "CREATE INDEX product_price IF NOT EXISTS FOR (p:Product) ON (p.price)",
    "CREATE INDEX product_rating IF NOT EXISTS FOR (p:Product) ON (p.avg_rating)",
]
```

### Common Relationship Patterns

```cypher
// One-to-Many
(Product)-[:BELONGS_TO]->(Category)
(Product)-[:MADE_BY]->(Brand)

// Many-to-Many
(Product)-[:HAS_TAG]->(Tag)
(User)-[:PURCHASED]->(Product)
(User)-[:REVIEWED {rating: 5, text: "..."}]->(Product)

// Hierarchical
(Category)-[:SUBCATEGORY_OF]->(Category)
(Employee)-[:REPORTS_TO]->(Employee)
```

---

## Customizing Cypher Queries

### File: `backend/app/services/matching_service.py`

### Query Template

```python
query = """
MATCH (primary:PrimaryNode)

// Optional relationships
OPTIONAL MATCH (primary)-[:RELATIONSHIP1]->(related1:RelatedNode1)
OPTIONAL MATCH (primary)-[:RELATIONSHIP2]->(related2:RelatedNode2)

// Collect related data
WITH primary,
     collect(DISTINCT related1.property) AS related1_list,
     collect(DISTINCT related2.property) AS related2_list

// Filtering
WHERE
    ($param1 IS NULL OR primary.property1 = $param1)
    AND ($param2 IS NULL OR primary.property2 <= $param2)

// Return with scoring
RETURN 
    primary.id AS id,
    primary.name AS name,
    related1_list,
    related2_list,
    // Inline scoring
    CASE WHEN $param1 IS NOT NULL AND primary.property1 = $param1 THEN 1 ELSE 0 END AS score1

ORDER BY score1 DESC, primary.name ASC
LIMIT 20
"""

result = await session.run(query, {
    "param1": request.field1,
    "param2": request.field2,
})
```

### Example: Product Search Query

```python
query = """
MATCH (p:Product)
OPTIONAL MATCH (p)-[:BELONGS_TO]->(c:Category)
OPTIONAL MATCH (p)-[:MADE_BY]->(b:Brand)
OPTIONAL MATCH (p)-[:HAS_TAG]->(t:Tag)

WITH p, c, b, collect(DISTINCT t.name) AS tags

WHERE
    ($category IS NULL OR c.name = $category)
    AND ($brand IS NULL OR b.name = $brand)
    AND ($price_max IS NULL OR p.price <= $price_max)
    AND ($min_rating IS NULL OR p.avg_rating >= $min_rating)

RETURN 
    p.product_id AS id,
    p.name AS name,
    p.price AS price,
    p.avg_rating AS rating,
    c.name AS category,
    b.name AS brand,
    tags

ORDER BY 
    CASE WHEN $sort_by = 'price_asc' THEN p.price END ASC,
    CASE WHEN $sort_by = 'price_desc' THEN p.price END DESC,
    CASE WHEN $sort_by = 'rating_desc' THEN p.avg_rating END DESC,
    p.name ASC

LIMIT $limit
"""
```

---

## Customizing Domain Models

### Files to Update

| File | Purpose |
|------|---------|
| `backend/app/models/matching.py` | Request/Response schemas |
| `backend/app/models/*.py` | Domain entity models |
| `frontend/app/match-demo/types.ts` | TypeScript types |

### MatchingRequest Template

```python
# backend/app/models/matching.py

class MatchingRequest(BaseModel):
    """Request schema for structured matching."""
    
    # Primary filter (maps to main node type)
    category: str | None = None
    
    # Related entity filters
    brand: str | None = None
    tags: list[str] = []
    
    # Numeric filters
    price_max: float | None = None
    min_rating: float | None = None
    
    # Result control
    result_limit: int | None = None
    sort_by: str | None = None  # price_asc, price_desc, rating_desc
    
    # Original query for logging
    text_query: str | None = None
```

### TypeScript Types Template

```typescript
// frontend/app/match-demo/types.ts

export interface MatchResult {
  id: string;
  name: string;
  score: number;
  score_breakdown: ScoreBreakdown;
  matched_reasons: string[];
  
  // Domain-specific fields
  price?: number;
  rating?: number;
  category?: string;
  brand?: string;
  tags?: string[];
  image_url?: string;
}

export interface ScoreBreakdown {
  category: number;
  brand: number;
  features: number;
  total: number;
}
```

---

## File Reference

### Core Files to Customize

| File | What to Change |
|------|----------------|
| `backend/app/services/nl_parser_service.py` | AI prompt, model selection |
| `backend/app/services/matching_service.py` | Cypher queries, scoring logic |
| `backend/app/models/matching.py` | Request/response Pydantic models |
| `backend/app/routers/admin.py` | Neo4j schema constraints |
| `frontend/app/match-demo/page.tsx` | UI components, display logic |
| `frontend/app/match-demo/types.ts` | TypeScript interfaces |

### Infrastructure (Usually Keep As-Is)

| File | Purpose |
|------|---------|
| `backend/app/core/config.py` | Settings management |
| `backend/app/db/neo4j.py` | Database connection |
| `backend/app/main.py` | FastAPI app setup |
| `docker-compose.yml` | Neo4j container |

---

## Checklist for New Project

- [ ] Clone repo and rename
- [ ] Update `.env` with your credentials
- [ ] Define your Neo4j node types and relationships
- [ ] Update schema in `admin.py`
- [ ] Create Pydantic models for your domain
- [ ] Write the OpenAI prompt for your query parsing
- [ ] Implement Cypher queries for matching
- [ ] Update frontend types and UI
- [ ] Seed sample data
- [ ] Test end-to-end

---

*Last updated: 2025-12-05*
