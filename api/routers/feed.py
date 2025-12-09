from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.feed import get_public_feed

router = APIRouter(prefix="/feed", tags=["feed"])

@router.get("")
def public_feed(
    sort: str = Query("newest", pattern="^(newest|oldest|review_length|review_type)$"),
    genre: str | None = None,
    review_type: str | None = Query(
        None,
        pattern="^(RECOMMENDED|NOT_RECOMMENDED|NEUTRAL)$",
    ),
    limit: int = Query(20, ge=1, le=50),
    # ^^ ge=1: limit must be >= 1
    # le=50: limit must be <= 50
    after: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Public Social Readia feed.

    - Only shows PUBLIC books from PUBLIC profiles
    - Supports sort modes (newest/oldest/review_length/review_type)
    - Supports optional genre + review_type filters
    - Uses cursor-based pagination via `after` param
    """
    return get_public_feed(
        db,
        sort=sort,
        genre=genre,
        review_type=review_type,
        limit=limit,
        after=after,
    )