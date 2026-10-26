"""Environment-based configuration. No secrets are hard-coded."""
import os
from dataclasses import dataclass


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def _bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    return default if raw is None else raw.strip().lower() in {"1", "true", "yes"}


_ENV = os.environ.get("CODEPROOF_ENV", "development")


@dataclass(frozen=True)
class Settings:
    app_name: str = "CodeProof"
    app_version: str = "0.2.0"
    environment: str = _ENV
    database_url: str = os.environ.get("DATABASE_URL", "sqlite:///./codeproof.db")
    cors_origins: tuple = tuple(
        o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()
    )
    max_source_bytes: int = _int("MAX_SOURCE_BYTES", 1_000_000)
    public_analysis_rate_limit: int = _int("PUBLIC_ANALYSIS_RATE_LIMIT", 20)
    model_dir: str = os.environ.get("MODEL_DIR", "./models")
    upload_dir: str = os.environ.get("UPLOAD_DIR", "./uploads")
    jwt_secret: str = os.environ.get("JWT_SECRET", "")
    jwt_exp_minutes: int = _int("JWT_EXP_MINUTES", 60)
    # Professor self-registration is convenient locally; disable it in production.
    allow_professor_registration: bool = _bool("ALLOW_PROFESSOR_REGISTRATION", _ENV != "production")
    auth_rate_limit: int = _int("AUTH_RATE_LIMIT", 10)  # attempts per minute per client IP


settings = Settings()
