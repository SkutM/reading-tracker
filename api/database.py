from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Old: SQLALCHEMY_DATABASE_URL = "sqlite:///./reading_tracker.db"
# NEW: Use an absolute path relative to the current working directory (project root)
import os 
from pathlib import Path

# Get the absolute path to the project root (where uvicorn is run from)
BASE_DIR = Path(__file__).resolve().parent.parent 
SQLALCHEMY_DATABASE_URL = f"sqlite:///{BASE_DIR}/db.sqlite"

engine = create_engine(
    # disables default restriction against accessing
    # from multiple threads, preventing crashes during
    # concurrent user requests
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# SessionLocal: A factory for creating db sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base Class: class that our ORM models will inherit from
Base = declarative_base()

# Dependency to get a db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()