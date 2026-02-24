"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "Victor Institutional Logic"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://vil:vilpass@localhost:5432/vildb"
    SQLITE_URL: str = "sqlite+aiosqlite:///../vildb.sqlite"
    USE_SQLITE_FALLBACK: bool = True

    # ── Redis ────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT ──────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "vil-super-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30  # Short-lived access token
    JWT_REFRESH_EXPIRE_DAYS: int = 7  # Refresh token lifespan

    # ── Security ─────────────────────────────────────────────────
    CREDENTIAL_ENCRYPTION_KEY: str = ""  # 64-char hex (32 bytes AES-256)
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30

    # ── CORS ─────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "https://vil-iota.vercel.app",
    ]

    # ── Mistral AI ───────────────────────────────────────────────
    MISTRAL_API_KEY: str = ""
    MISTRAL_MODEL: str = "mistral-small-latest"

    # ── OANDA (Legacy global — per-user credentials take priority) ──
    OANDA_API_KEY: str = ""
    OANDA_ACCOUNT_ID: str = ""
    OANDA_ENV: str = "practice"  # practice or live

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Force load .env for local scripts
import os
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

settings = Settings()
