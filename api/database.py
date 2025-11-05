import os
import sqlalchemy_libsql  # for dialect check
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

def _normalize_libsql_url(url: str | None) -> str | None:
    """Accept libsql:// or sqlite+libsql:// and normalize to sqlite+libsql://"""
    if not url:
        return None
    if url.startswith("sqlite+libsql://"):
        return url
    if url.startswith("libsql://"):
        return "sqlite+libsql://" + url[len("libsql://"):]
    return url

TURSO_URL = _normalize_libsql_url(os.getenv("TURSO_DATABASE_URL"))
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

if TURSO_URL and TURSO_TOKEN:
    # turso (remote)
    engine = create_engine(
        TURSO_URL,
        connect_args={"auth_token": TURSO_TOKEN},
        pool_pre_ping=True,
    )
else:
    # fall back to sqlite otherwise (hopefully doesn't get here)
    engine = create_engine(
        "sqlite:///../db.sqlite",
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
