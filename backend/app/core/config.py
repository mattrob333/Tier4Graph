# backend/app/core/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Neo4j connection settings (required)
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    neo4j_database: str | None = None

    # LLM provider settings (optional)
    # Set llm_provider to "openai" or "anthropic" to enable LLM-backed NL parsing
    # When not set, the system uses rule-based keyword extraction (MockNLParser)
    llm_provider: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    class Config:
        env_file = "../.env"
        env_prefix = ""


settings = Settings()
