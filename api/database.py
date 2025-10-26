# api/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from api.config import settings

Base = declarative_base()

def _make_engine():
    if settings.TURSO_DATABASE_URL:
        # Turso/libSQL via sqlalchemy-libsql
        return create_engine(
            settings.TURSO_DATABASE_URL,  # e.g. libsql://reading-tracker-xxxxx.turso.io
            connect_args={"auth_token": settings.TURSO_AUTH_TOKEN or ""},
            pool_pre_ping=True,
        )
    # Fallback to local SQLite (dev)
    return create_engine("sqlite:///./db.sqlite", connect_args={"check_same_thread": False})

engine = _make_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
