from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import health, admin, vendor, ingestion, match
from .db.neo4j import init_neo4j_driver, close_neo4j_driver

app = FastAPI(
    title="Cognitive Procurement Engine API",
    version="0.1.0",
)

# CORS middleware for frontend access
# Using allow_origins=["*"] for demo - in production, list specific domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for demo
    allow_credentials=False,  # Must be False when using "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(admin.router)
app.include_router(vendor.router)
app.include_router(ingestion.router)
app.include_router(match.router)


@app.on_event("startup")
async def on_startup() -> None:
    await init_neo4j_driver()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await close_neo4j_driver()


@app.get("/")
async def root():
    return {"message": "CPE backend up"}
