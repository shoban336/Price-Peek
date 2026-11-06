"""Foundation and environment sanity tests."""
import os
import pytest
from sqlalchemy import text
from app.config.settings import get_settings
from app.config.database import Base, engine, SessionLocal


def test_settings_load():
    """Verify application configuration loads default and custom settings."""
    settings = get_settings()
    assert settings.APP_NAME == "PricePeek"
    assert settings.DATABASE_URL.startswith("sqlite")
    assert isinstance(settings.CORS_ORIGINS, list)
    assert len(settings.CORS_ORIGINS) > 0


def test_database_connection():
    """Verify SQLite engine can connect and execute a test query."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        result = session.execute(text("SELECT 1")).scalar()
        assert result == 1
    finally:
        session.close()
