Here is a complete Markdown file you can save as something like
`docs/NEO4J_SETUP_AND_MCP.md` in your repo.

---

# Neo4j Setup Guide For CPE

Full driver template, FastAPI wiring, and MCP integration notes

## 1. Purpose

This document tells AI coding agents (Claude Code, Windsurf, etc.) exactly how to:

* Configure Neo4j connection settings for the Cognitive Procurement Engine (CPE)
* Implement a reusable async Neo4j driver module in FastAPI
* Wire startup and shutdown events correctly
* Provide a `get_session` dependency for routes and services
* Expose a `/neo4j-health` endpoint to verify connectivity
* Understand how to connect MCP clients like Claude Desktop to Neo4j for Cypher exploration and data modeling

This is the source of truth for Neo4j integration in this project.

Relevant external docs:

* Neo4j Python driver async API reference
* FastAPI async and concurrency docs
* Official Neo4j MCP integration overview
* Official Neo4j MCP server repository
* Neo4j Data Modeling MCP server blog and config example

---

## 2. High level design

We will:

1. Load Neo4j configuration from environment variables using Pydantic Settings.
2. Initialize a global `AsyncDriver` instance on FastAPI startup.
3. Close the driver cleanly on shutdown.
4. Provide a FastAPI dependency `get_neo4j_session` that yields an `AsyncSession`.
5. Use that session in repositories and endpoints.
6. Implement a `/neo4j-health` endpoint that runs `RETURN 1 AS ok` and returns a boolean.
7. Keep all driver logic in `app/db/neo4j.py` so the rest of the code does not touch the driver directly.

This follows best practices from Neo4j async driver examples and FastAPI dependency injection patterns.

---

## 3. Environment variables

We standardize these variables and document them in `.env.example`:

```env
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password-here
NEO4J_DATABASE=neo4j
```

* `neo4j+s` scheme is used for Neo4j Aura over TLS.
* For local Docker or Desktop, you may use `bolt://localhost:7687` instead.

All backend code must read these values through a Pydantic settings class, not directly from `os.environ`.

---

## 4. Files Claude Code must create or update

Claude (or any AI dev agent) should create or update the following backend files:

* `backend/app/core/config.py`
* `backend/app/db/neo4j.py`
* `backend/app/main.py` (to wire startup, shutdown, and health route)
* `backend/app/routers/neo4j_health.py` or add to existing `health.py`
* Optional: tests under `backend/app/tests/` (for health and basic query)

The instructions and code templates below are the expected shape.

---

## 5. Pydantic settings: `app/core/config.py`

Create this file if it does not exist.

```python
# backend/app/core/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    neo4j_database: str | None = None

    class Config:
        env_file = ".env"
        env_prefix = ""


settings = Settings()
```

Requirements:

* Use `BaseSettings` from `pydantic_settings`.
* Default `neo4j_database` to `None` so the driver uses its default if not set.
* Do not hardcode secrets in this file.

---

## 6. Neo4j driver module: `app/db/neo4j.py`

Create a dedicated module for all driver lifecycle and session handling.

```python
# backend/app/db/neo4j.py

from typing import AsyncIterator, Optional

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession

from app.core.config import settings

_driver: Optional[AsyncDriver] = None


async def init_neo4j_driver() -> None:
    """
    Initialize the global Neo4j AsyncDriver.

    This should be called once on FastAPI startup.
    """
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )


async def close_neo4j_driver() -> None:
    """
    Close the global Neo4j AsyncDriver.

    This should be called once on FastAPI shutdown.
    """
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None


def get_neo4j_driver() -> AsyncDriver:
    """
    Return the global AsyncDriver instance.

    Raises:
        RuntimeError: if the driver was not initialized.
    """
    if _driver is None:
        raise RuntimeError(
            "Neo4j driver is not initialized. "
            "Ensure init_neo4j_driver() is called on application startup."
        )
    return _driver


async def get_neo4j_session() -> AsyncIterator[AsyncSession]:
    """
    FastAPI dependency that yields an AsyncSession and ensures it gets closed.

    Usage:
        async def handler(session: AsyncSession = Depends(get_neo4j_session)):
            ...
    """
    driver = get_neo4j_driver()
    db = settings.neo4j_database
    async with driver.session(database=db) as session:
        yield session
```

Key points for AI:

* Use `AsyncGraphDatabase.driver` for async.
* Store `_driver` as module global.
* Do not create a new driver per request.
* Use `async with driver.session(...)` to yield an `AsyncSession`.
* Raise a clear error if someone tries to access the driver before initialization.

---

## 7. Wiring into FastAPI: `app/main.py`

Update `backend/app/main.py` to call the init and close functions on startup and shutdown, and to include a Neo4j health route.

```python
# backend/app/main.py

from fastapi import FastAPI

from app.routers import health
from app.db.neo4j import init_neo4j_driver, close_neo4j_driver

app = FastAPI(
    title="Cognitive Procurement Engine API",
    version="0.1.0",
)

app.include_router(health.router)


@app.on_event("startup")
async def on_startup() -> None:
    await init_neo4j_driver()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await close_neo4j_driver()
```

If `health.py` already exists, we will extend it in the next step.

---

## 8. Neo4j health endpoint

You can either add this to `app/routers/health.py` or create a dedicated router file such as `app/routers/neo4j_health.py` and include it from `main.py`.

Example added to `health.py`:

```python
# backend/app/routers/health.py

from fastapi import APIRouter, Depends
from neo4j import AsyncSession

from app.db.neo4j import get_neo4j_session

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_root() -> dict:
    return {"status": "ok"}


@router.get("/neo4j")
async def neo4j_health(session: AsyncSession = Depends(get_neo4j_session)) -> dict:
    """
    Basic Neo4j connectivity check.

    Runs 'RETURN 1 AS ok' and verifies the result.
    """
    result = await session.run("RETURN 1 AS ok")
    record = await result.single()
    is_ok = bool(record and record["ok"] == 1)
    return {"neo4j_ok": is_ok}
```

Expected behavior:

* `GET /health` returns `{"status": "ok"}`.
* `GET /health/neo4j` returns `{"neo4j_ok": true}` if the DB is reachable and credentials are correct.

---

## 9. Example repository pattern using the session

Once the driver and session dependency are in place, repositories should accept `AsyncSession` instances instead of touching the driver directly.

Example `app/repositories/vendor_repository.py`:

```python
# backend/app/repositories/vendor_repository.py

from typing import Optional

from neo4j import AsyncSession


class VendorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_vendor(self, vendor_id: str, name: str) -> None:
        query = """
        MERGE (v:Vendor {vendor_id: $vendor_id})
        SET v.name = $name
        """
        await self._session.run(query, vendor_id=vendor_id, name=name)

    async def get_vendor_by_id(self, vendor_id: str) -> Optional[dict]:
        query = """
        MATCH (v:Vendor {vendor_id: $vendor_id})
        RETURN v.vendor_id AS vendor_id, v.name AS name
        """
        result = await self._session.run(query, vendor_id=vendor_id)
        record = await result.single()
        if not record:
            return None
        return {"vendor_id": record["vendor_id"], "name": record["name"]}
```

Example usage in a route:

```python
# backend/app/routers/vendor.py

from fastapi import APIRouter, Depends, HTTPException
from neo4j import AsyncSession

from app.db.neo4j import get_neo4j_session
from app.repositories.vendor_repository import VendorRepository

router = APIRouter(prefix="/vendors", tags=["vendors"])


@router.get("/{vendor_id}")
async def get_vendor(vendor_id: str, session: AsyncSession = Depends(get_neo4j_session)):
    repo = VendorRepository(session)
    vendor = await repo.get_vendor_by_id(vendor_id)
    if vendor is None:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor
```

---

## 10. What Claude Code needs to do with this file

When Claude (or another AI dev agent) reads this document, it must:

1. Respect all file paths and not invent new directories.
2. Implement the exact `config.py` and `neo4j.py` structure shown here, adapting only small details if project imports differ.
3. Wire startup and shutdown events in `main.py` exactly as described.
4. Add the `/health/neo4j` endpoint in `health.py` or a dedicated router file.
5. Ensure imports are correct and run `uvicorn app.main:app --reload` without errors.
6. Not modify the graph ontology or any documentation files unless explicitly requested.
7. After implementation, provide manual test instructions like:

   * Start backend: `uvicorn app.main:app --reload`
   * Ensure `.env` has valid Neo4j credentials
   * Call `GET http://localhost:8000/health/neo4j` and confirm `{"neo4j_ok": true}`

---

## 11. Neo4j MCP server overview and links

The Neo4j MCP server allows MCP compatible clients like Claude Desktop, VS Code, Cursor, and Windsurf to interact with Neo4j through natural language, using the Model Context Protocol (MCP).

### 11.1 Official Neo4j MCP server

* GitHub repo:
  `https://github.com/neo4j/mcp`
* Overview:
  `https://neo4j.com/developer/genai-ecosystem/model-context-protocol-mcp/`

This server is a local binary (`neo4j-mcp`) that you run, and it connects to any Neo4j deployment (Aura, Docker, Desktop, Sandbox). The repo readme includes environment variable examples for different MCP hosts.

### 11.2 Neo4j Data Modeling MCP server

For data modeling and schema design, Neo4j also provides a Data Modeling MCP server that plugs into Claude Desktop and other MCP clients.

* Blog and config example:
  `https://neo4j.com/blog/developer/neo4j-data-modeling-mcp-server/`
* It includes a sample MCP client config:

```json
{
  "mcpServers": {
    "neo4j-graph-data-modeling": {
      "command": "uvx",
      "args": ["mcp-neo4j-data-modeling@0.1.1"]
    }
  }
}
```

You then add Neo4j connection details via environment variables or additional config as documented in the repo and blog.

### 11.3 Additional MCP server variants

There are several ecosystem servers that also connect Neo4j to MCP clients:

* `neo4j-contrib/mcp-neo4j` for general Cypher interaction:
  `https://github.com/neo4j-contrib/mcp-neo4j`
* `mcp-neo4j-cypher` package for Cypher centric MCP workflows:
  `https://pypi.org/project/mcp-neo4j-cypher/`

These servers are not part of the FastAPI backend. They are separate tools you run alongside your development environment so Claude and other MCP aware AIs can:

* Inspect schema
* Run Cypher queries
* Help refactor models
* Draft ingestion flows

---

## 12. How MCP fits into CPE work

For this project, MCP is used as a developer and operator tool, not part of the runtime backend:

* The FastAPI backend uses the official Neo4j Python driver directly as described above.
* During development and modeling, you can run an MCP server to give Claude or other tools direct Cypher access to your Neo4j Aura instance.
* You can use the MCP data modeling tools to refine the CPE ontology, test Cypher queries, and explore the graph, then codify changes into `ARCHITECTURE.md` and `ONTOLOGY.md`.

This separation keeps the production backend simple while giving you powerful graph exploration tools via MCP.

---

## 13. Definition of done for Neo4j setup

Neo4j integration is considered complete for the initial phase when:

1. `.env` and `.env.example` include the four Neo4j variables.
2. `app/core/config.py` exists and loads settings without error.
3. `app/db/neo4j.py` implements `init_neo4j_driver`, `close_neo4j_driver`, `get_neo4j_driver`, `get_neo4j_session`.
4. `app/main.py` wires startup and shutdown events.
5. `GET /health/neo4j` returns `{"neo4j_ok": true}` when Neo4j is reachable.
6. A sample repository (for Vendor) can write and read a node successfully using an injected session.

Once this is working, the next vertical slice is to implement the schema bootstrap and the first ingestion pipeline step.
