# api/database.py
import os
import sqlalchemy_libsql  # ensures the dialect is registered
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

TURSO_HOST = os.getenv("TURSO_HOST", "reading-tracker-skutm.turso.io")
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

if TURSO_TOKEN:
    # This is the same pattern that succeeded in your test
    DATABASE_URL = f"sqlite+libsql://{TURSO_HOST}?secure=true"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"auth_token": TURSO_TOKEN},
        pool_pre_ping=True,
    )
else:
    # local fallback
    DATABASE_URL = "sqlite:///./db.sqlite"
    engine = create_engine(
        DATABASE_URL,
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
