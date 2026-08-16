"""
aiconnex_agent/platform_kb/config.py

Configuration module for Platform Knowledge Base infrastructure backends.
Loads connection settings for PostgreSQL, Qdrant, and MinIO from environment variables,
with fallback loading from .env.kb or .env files.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


def load_env_file(env_path: str) -> None:
    """Helper to parse a key=value .env file into os.environ if key is not set."""
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip("'").strip('"')
            if key and key not in os.environ:
                os.environ[key] = val


# Attempt loading .env.kb and .env automatically on module import
_base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_env_file(os.path.join(_base_dir, ".env.kb"))
load_env_file(os.path.join(_base_dir, ".env"))


@dataclass
class PostgresConfig:
    host: str = field(default_factory=lambda: os.getenv("POSTGRES_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(os.getenv("POSTGRES_PORT", "5432")))
    db_name: str = field(default_factory=lambda: os.getenv("POSTGRES_DB", "aiconnex_kb_prod"))
    user: str = field(default_factory=lambda: os.getenv("POSTGRES_USER", "postgres"))
    password: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", "postgres"))

    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}"


@dataclass
class QdrantConfig:
    host: str = field(default_factory=lambda: os.getenv("QDRANT_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(os.getenv("QDRANT_PORT", "6333")))
    grpc_port: int = field(default_factory=lambda: int(os.getenv("QDRANT_GRPC_PORT", "6334")))
    collection: str = field(default_factory=lambda: os.getenv("QDRANT_COLLECTION", "platform_kb_embeddings"))
    vector_dim: int = field(default_factory=lambda: int(os.getenv("QDRANT_VECTOR_DIM", "384")))

    @property
    def http_url(self) -> str:
        return f"http://{self.host}:{self.port}"


@dataclass
class MinIOConfig:
    endpoint: str = field(default_factory=lambda: os.getenv("MINIO_ENDPOINT", "127.0.0.1:9000"))
    access_key: str = field(default_factory=lambda: os.getenv("MINIO_ACCESS_KEY", "minio_admin"))
    secret_key: str = field(default_factory=lambda: os.getenv("MINIO_SECRET_KEY", "minio_secret_password_2026"))
    bucket: str = field(default_factory=lambda: os.getenv("MINIO_BUCKET", "aiconnex-platform-kb-prod"))
    secure: bool = field(default_factory=lambda: os.getenv("MINIO_SECURE", "false").lower() == "true")


@dataclass
class Neo4jConfig:
    host: str = field(default_factory=lambda: os.getenv("NEO4J_HOST", "127.0.0.1"))
    bolt_port: int = field(default_factory=lambda: int(os.getenv("NEO4J_BOLT_PORT", "7687")))
    http_port: int = field(default_factory=lambda: int(os.getenv("NEO4J_HTTP_PORT", "7474")))
    user: str = field(default_factory=lambda: os.getenv("NEO4J_USER", "neo4j"))
    password: str = field(default_factory=lambda: os.getenv("NEO4J_PASSWORD", "neo4j_secret_password_2026"))

    @property
    def bolt_uri(self) -> str:
        return f"bolt://{self.host}:{self.bolt_port}"

    @property
    def http_url(self) -> str:
        return f"http://{self.host}:{self.http_port}"


@dataclass
class KBConfig:
    strict_production_mode: bool = field(
        default_factory=lambda: os.getenv("KB_STRICT_PRODUCTION_MODE", "true").lower() == "true"
    )
    postgres: PostgresConfig = field(default_factory=PostgresConfig)
    qdrant: QdrantConfig = field(default_factory=QdrantConfig)
    minio: MinIOConfig = field(default_factory=MinIOConfig)
    neo4j: Neo4jConfig = field(default_factory=Neo4jConfig)


def get_kb_config() -> KBConfig:
    """Returns a fresh instance of KBConfig populated from environment settings."""
    return KBConfig()

