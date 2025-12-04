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
