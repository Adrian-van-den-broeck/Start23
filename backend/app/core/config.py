"""Environment-backed application configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator, model_validator
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
    supabase_publishable_key: str = ""
    supabase_secret_key: SecretStr = SecretStr("")
    supabase_jwt_audience: Literal["authenticated"] = "authenticated"
    supabase_jwt_algorithm: Literal["ES256"] = "ES256"
    supabase_jwks_cache_seconds: int = Field(default=300, ge=60, le=600)
    supabase_jwks_timeout_seconds: float = Field(default=5.0, gt=0, le=30)
    supabase_data_api_timeout_seconds: float = Field(default=10.0, gt=0, le=30)
    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = "gpt-5.6-luna"
    openai_api_timeout_seconds: float = Field(default=8.0, gt=0, le=30)
    polar_client_id: str = ""
    polar_client_secret: SecretStr = SecretStr("")
    polar_oauth_redirect_url: AnyHttpUrl = AnyHttpUrl(
        "http://localhost:8000/api/v1/integrations/polar/oauth/callback"
    )
    polar_webhook_secret: SecretStr = SecretStr("")
    polar_api_timeout_seconds: float = Field(default=10.0, gt=0, le=30)
    polar_max_activity_file_bytes: int = Field(
        default=25 * 1024 * 1024,
        ge=1024,
        le=100 * 1024 * 1024,
    )

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

    @model_validator(mode="after")
    def require_deployed_supabase_keys(self) -> "Settings":
        """Fail deployment startup when either required Data API key is absent."""
        if self.environment in {"staging", "production"}:
            if not self.supabase_publishable_key.strip():
                raise ValueError("supabase_publishable_key is required when deployed")
            if not self.supabase_secret_key.get_secret_value().strip():
                raise ValueError("supabase_secret_key is required when deployed")
        return self

    @model_validator(mode="after")
    def require_complete_polar_configuration(self) -> "Settings":
        """Prevent partially configured OAuth or webhook authentication."""
        values = (
            self.polar_client_id.strip(),
            self.polar_client_secret.get_secret_value().strip(),
            self.polar_webhook_secret.get_secret_value().strip(),
        )
        if any(values) and not all(values):
            raise ValueError(
                "polar_client_id, polar_client_secret and polar_webhook_secret "
                "must be configured together"
            )
        return self

    @field_validator("openai_model")
    @classmethod
    def validate_openai_model(cls, value: str) -> str:
        """Require a non-empty provider model identifier."""
        normalized = value.strip()
        if not normalized:
            raise ValueError("openai_model must not be empty")
        return normalized


@lru_cache
def get_settings() -> Settings:
    """Load and cache application settings."""
    return Settings()
