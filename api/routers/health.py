from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db

router = APIRouter(tags=["health"])

@router.get("/health")
def health(db: Session = Depends(get_db)):
    """
    Health check:
    - Ensures API is up
    - Ensures we can talk to the DB
    """
    db.execute(text("SELECT 1"))
    return {"status": "ok", "db": "ok"}