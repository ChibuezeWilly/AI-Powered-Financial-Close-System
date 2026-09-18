import os
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Backend-only settings.

    External integrations are deliberately optional: PostgreSQL remains the
    source of truth and a missing Slack, Pinecone, or model credential must
    never prevent the API from starting.
    """

    DATABASE_URL: str = Field(default="", validation_alias=AliasChoices("DATABASE_URL", "DB_URL"))
    SECRET_KEY: str = Field(default="development-only-change-me", validation_alias=AliasChoices("SECRET_KEY", "JWT_SECRET"))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 420
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    DEFAULT_ADMIN_EMAIL: str = "obodofamily6@gmail.com"
    DEFAULT_ADMIN_PASSWORD: str = "Chibueze2007"

    REDIS_URL: str = ""

    APP_ENV: str = "development"

    HF_TOKEN: str = ""
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    RERANKING_MODEL: str = "BM25"
    VISION_MODEL: str = "meta-llama/Llama-3.3-70B-Instruct"
    INVESTIGATION_MODEL: str = "meta-llama/Llama-3.3-70B-Instruct"
    GENERAL_AGENT_MODEL: str = "meta-llama/Llama-3.3-70B-Instruct"
    LLM_PROVIDER: str = ""
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = ""

    PINECONE_API_KEY: str = Field(default="", validation_alias=AliasChoices("PINECONE_API_KEY", "PINE_CONE_API_KEY"))
    PINECONE_INDEX: str = ""
    PINECONE_NAMESPACE: str = "financial-close-resolutions"
    PINECONE_DIMENSION: int = 1024

    NEO4J_URI: str = Field(default="", validation_alias=AliasChoices("NEO4J_URI", "GRAPH_DB_URI", "GRAPH_DATABASE_URI"))
    NEO4J_USERNAME: str = Field(default="", validation_alias=AliasChoices("NEO4J_USERNAME", "GRAPH_USERNAME"))
    NEO4J_PASSWORD: str = Field(default="", validation_alias=AliasChoices("NEO4J_PASSWORD", "GRAPH_PASSWORD", "GRAPH_DB_KEY"))
    NEO4J_DATABASE: str = "neo4j"

    # SLACK_BOT_TOKEN posts messages. The signing secret verifies requests;
    # the client secret is used only for an OAuth code exchange, never logging.
    SLACK_BOT_TOKEN: str = Field(default="", validation_alias=AliasChoices("SLACK_BOT_TOKEN", "SLACK_ACCESS_TOKEN"))
    SLACK_SIGNING_SECRET: str = ""
    SLACK_CLIENT_ID: str = ""
    SLACK_CLIENT_SECRET: str = ""
    SLACK_CHANNEL_ID: str = ""

    NGROK_AUTHTOKEN: str = ""
    AGENTMAIL_API_KEY: str = ""
    AGENT_DISPLAY_NAME: str = ""
    AGENTMAIL_INBOX_ID: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_BASE_URL: str = ""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def effective_database_url(self) -> str:
        """Return the database URL to use – DATABASE_URL if set, else DB_URL."""
        return self.DATABASE_URL

    # Compatibility properties keep existing adapters operational while all
    # new code uses the canonical names above.
    @property
    def PINE_CONE_API_KEY(self) -> str:
        return self.PINECONE_API_KEY

    @property
    def GRAPH_DATABASE_URI(self) -> str:
        return self.NEO4J_URI

    @property
    def GRAPH_USERNAME(self) -> str:
        return self.NEO4J_USERNAME

    @property
    def GRAPH_PASSWORD(self) -> str:
        return self.NEO4J_PASSWORD

    @property
    def SLACK_ACCESS_TOKEN(self) -> str:
        return self.SLACK_BOT_TOKEN


settings = Settings()


def resolve_redis_url(raw_url: str) -> str:
    """Use localhost when a Docker service hostname is configured outside Docker."""
    parsed = urlparse(raw_url)
    if parsed.hostname == "redis" and not os.path.exists("/.dockerenv"):
        netloc = "localhost"
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
        if parsed.username or parsed.password:
            auth = parsed.username or ""
            if parsed.password:
                auth = f"{auth}:{parsed.password}"
            netloc = f"{auth}@{netloc}"
        return urlunparse(parsed._replace(netloc=netloc))

    return raw_url


def resolve_postgres_url(raw_url: str) -> str:
    """Normalize PostgreSQL URLs for Psycopg 3 and local Docker runs."""
    parsed = urlparse(raw_url)
    if parsed.hostname in {"postgres", "db", "postgresql"} and not os.path.exists(
        "/.dockerenv"
    ):
        netloc = "localhost"
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
        if parsed.username or parsed.password:
            auth = parsed.username or ""
            if parsed.password:
                auth = f"{auth}:{parsed.password}"
            netloc = f"{auth}@{netloc}"
        parsed = parsed._replace(netloc=netloc)

    if parsed.scheme in {"postgresql", "postgresql+psycopg2"}:
        parsed = parsed._replace(scheme="postgresql+psycopg")

    return urlunparse(parsed)
