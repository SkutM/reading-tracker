from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.feed import get_public_feed, get_public_feed_item

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
    after: str | None = None,
    db: Session = Depends(get_db),
):
    return get_public_feed(
        db,
        sort=sort,
        genre=genre,
        review_type=review_type,
        limit=limit,
        after=after,
    )


@router.get("/{book_id}")
def public_feed_item(book_id: int, db: Session = Depends(get_db)):
    item = get_public_feed_item(db, book_id=book_id)
    if not item:
        raise HTTPException(status_code=404, detail="Post not found")
    return item
