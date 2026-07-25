"""Environment-backed application configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "test", "staging", "production"]


class Settings(BaseSettings):
    """Validated Start23 application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="START23_",
        extra="ignore",
    )

    app_name: str = "Start23 API"
    app_version: str = "0.1.0"
    environment: Environment = "local"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"
    supabase_url: AnyHttpUrl = AnyHttpUrl("https://isfumhgqphieoayqahjv.supabase.co")
    supabase_jwt_audience: Literal["authenticated"] = "authenticated"
    supabase_jwt_algorithm: Literal["ES256"] = "ES256"
    supabase_jwks_cache_seconds: int = Field(default=300, ge=60, le=600)
    supabase_jwks_timeout_seconds: float = Field(default=5.0, gt=0, le=30)

    @property
    def supabase_jwt_issuer(self) -> str:
        """Return the expected issuer for Supabase user access tokens."""
        return f"{str(self.supabase_url).rstrip('/')}/auth/v1"

    @property
    def supabase_jwks_url(self) -> str:
        """Return the project's public JSON Web Key Set endpoint."""
        return f"{self.supabase_jwt_issuer}/.well-known/jwks.json"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Normalize and validate the configured logging level."""
        normalized = value.upper()
        allowed = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
        if normalized not in allowed:
            raise ValueError(f"log_level must be one of {sorted(allowed)}")
        return normalized

    @field_validator("api_v1_prefix")
    @classmethod
    def validate_api_v1_prefix(cls, value: str) -> str:
        """Require one normalized absolute API prefix."""
        if not value.startswith("/"):
            raise ValueError("api_v1_prefix must start with '/'")
        if value != "/" and value.endswith("/"):
            raise ValueError("api_v1_prefix must not end with '/'")
        return value


@lru_cache
def get_settings() -> Settings:
    """Load and cache application settings."""
    return Settings()
