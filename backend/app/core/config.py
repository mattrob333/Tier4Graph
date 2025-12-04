# backend/app/core/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    neo4j_database: str | None = None

    class Config:
        env_file = "../.env"
        env_prefix = ""


settings = Settings()
