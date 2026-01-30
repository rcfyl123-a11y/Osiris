"""Database configuration for Osiris.

Path: osiris/config/settings/database.py
"""

import os
from pathlib import Path
from urllib.parse import urlparse

from .environment import POSTGRES_READY, VAR_DIR


def _sqlite_config(path: str | None) -> dict:
    """Build a SQLite database configuration dictionary."""
    db_path = Path(path).expanduser() if path else VAR_DIR / "db.sqlite3"
    return {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(db_path),
    }


def _postgres_config(parsed) -> dict:
    """Build a PostgreSQL database configuration dictionary."""
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": parsed.path.lstrip("/"),
        "USER": parsed.username or "",
        "PASSWORD": parsed.password or "",
        "HOST": parsed.hostname or "",
        "PORT": str(parsed.port or "5432"),
        "CONN_MAX_AGE": 60,
    }


def _database_from_url(url: str) -> dict | None:
    """Create a database config dictionary from a DATABASE_URL string."""
    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()
    if scheme in {"sqlite", "sqlite3"}:
        return _sqlite_config(parsed.path.lstrip("/") or None)
    if scheme in {"postgres", "postgresql"}:
        return _postgres_config(parsed)
    return None


database_url = os.getenv("DATABASE_URL")
if database_url:
    config = _database_from_url(database_url)
    if config is None:
        raise ValueError(f"Unsupported DATABASE_URL scheme: {database_url}")
    DATABASES = {"default": config}
else:
    db_engine = os.getenv("DB_ENGINE")
    if db_engine:
        engine = db_engine.strip().lower()
        if engine in {"sqlite", "sqlite3"}:
            DATABASES = {"default": _sqlite_config(os.getenv("DB_NAME"))}
        elif engine in {"postgres", "postgresql"}:
            DATABASES = {
                "default": {
                    "ENGINE": "django.db.backends.postgresql",
                    "NAME": os.getenv("DB_NAME", ""),
                    "USER": os.getenv("DB_USER", ""),
                    "PASSWORD": os.getenv("DB_PASSWORD", ""),
                    "HOST": os.getenv("DB_HOST", ""),
                    "PORT": os.getenv("DB_PORT", "5432"),
                    "CONN_MAX_AGE": 60,
                }
            }
        else:
            raise ValueError(f"Unsupported DB_ENGINE: {db_engine}")
    elif POSTGRES_READY:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": os.getenv("POSTGRES_DB"),
                "USER": os.getenv("POSTGRES_USER"),
                "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
                "HOST": os.getenv("POSTGRES_HOST"),
                "PORT": os.getenv("POSTGRES_PORT", "5432"),
                "CONN_MAX_AGE": 60,
            }
        }
    else:
        DATABASES = {"default": _sqlite_config(None)}
