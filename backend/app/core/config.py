from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""

    PROJECT_NAME: str = "BCG AI Financial Analyst"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    CACHE_TTL_SECONDS: int = 3600

    # Supabase Settings (Placeholder for database integration)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # CORS configuration
    CORS_ORIGINS: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        description="Comma-separated list of allowed CORS origins",
    )
    CORS_ORIGIN_REGEX: str | None = Field(
        default=None,
        description="Optional regex pattern for allowed CORS origins (e.g. Vercel previews)",
    )

    # SEC configuration
    FINANCIAL_DATA_MODE: str = Field(default="fixture")
    SEC_USER_AGENT: str = Field(default="")

    # Gemini AI configuration
    GEMINI_API_KEY: str = Field(default="")
    GEMINI_MODEL: str = Field(default="gemini-3.6-flash")

    # Groq Fallback AI configuration
    GROQ_API_KEY: str = Field(default="")
    GROQ_MODEL: str = Field(default="openai/gpt-oss-120b")

    # LLM Provider Orchestration
    LLM_PRIMARY_PROVIDER: str = Field(default="gemini")
    LLM_FALLBACK_PROVIDER: str = Field(default="groq")
    LLM_REQUEST_TIMEOUT_SECONDS: float = Field(default=30.0)

    @property
    def cors_origins_list(self) -> list[str]:
        """Return list of parsed CORS origins."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @field_validator("FINANCIAL_DATA_MODE")
    @classmethod
    def validate_data_mode(cls, v: str) -> str:
        allowed = {"fixture", "sec", "sec_with_fixture_fallback"}
        if v not in allowed:
            raise ValueError(f"FINANCIAL_DATA_MODE must be one of {allowed}, got '{v}'")
        return v

    @field_validator("SEC_USER_AGENT")
    @classmethod
    def validate_user_agent(cls, v: str, info: ValidationInfo) -> str:
        mode = info.data.get("FINANCIAL_DATA_MODE", "fixture")
        if mode in {"sec", "sec_with_fixture_fallback"} and not v:
            raise ValueError("SEC_USER_AGENT must be set when SEC mode is enabled")
        return v

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
