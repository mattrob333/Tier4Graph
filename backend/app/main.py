from fastapi import FastAPI

from .routers import health, admin, vendor
from .db.neo4j import init_neo4j_driver, close_neo4j_driver

app = FastAPI(
    title="Cognitive Procurement Engine API",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(admin.router)
app.include_router(vendor.router)


@app.on_event("startup")
async def on_startup() -> None:
    await init_neo4j_driver()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await close_neo4j_driver()


@app.get("/")
async def root():
    return {"message": "CPE backend up"}
