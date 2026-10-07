"""Deployment settings (Tier 2). Clinical thresholds never live here; they come from rule-set files."""

from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings

DEFAULT_SCORE_VERSION = "numic_flow_levene"


class Settings(BaseSettings):
    model_config = {"env_prefix": "NUMIC_"}

    database_url: str = Field(
        "sqlite+aiosqlite:///./numic-demo.db",
        # Local runs need no Postgres. Railway (and most hosts) expose DATABASE_URL without our prefix.
        validation_alias=AliasChoices("NUMIC_DATABASE_URL", "DATABASE_URL"),
    )
    database_echo: bool = False

    default_score_version: str = DEFAULT_SCORE_VERSION
    enabled_score_versions: list[str] = [DEFAULT_SCORE_VERSION]
    scan_day_timezone: str = "Europe/London"

    demo_enabled: bool = True
    """Serve the public demo API (sandboxes, seed babies) and run its start-up/daily jobs."""
    demo_sandbox_ttl_days: int = 7
    demo_max_babies_per_sandbox: int = 20
    demo_max_scans_per_baby: int = 30
    demo_writes_per_minute: int = 60
    demo_maintenance_interval_seconds: int = 3600
    """How often the clean-up job runs; it also re-dates the seed babies when the day changes."""

    @field_validator("database_url")
    @classmethod
    def _use_async_driver(cls, v: str) -> str:
        """Hosts hand out ``postgres://`` / ``postgresql://``; SQLAlchemy async needs ``+asyncpg``."""
        for prefix in ("postgres://", "postgresql://"):
            if v.startswith(prefix):
                return "postgresql+asyncpg://" + v[len(prefix):]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
