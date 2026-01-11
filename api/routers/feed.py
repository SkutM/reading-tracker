# api/routers/feed.py

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..jwt_utils import get_current_user
from ..auth_models import User

from ..services.feed import (
    get_public_feed,
    get_public_feed_item,
    set_like,
    unset_like,
    has_liked,
)

from ..services.comments import (
    list_comments,
    add_comment,
    delete_comment,
)

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


# -------------------------
# Likes (requires auth)
# -------------------------

@router.post("/{book_id}/like")
def like_post(
    book_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        like_count = set_like(db, user_id=user.id, book_id=book_id)
        return {"book_id": book_id, "liked": True, "like_count": like_count}
    except ValueError:
        raise HTTPException(status_code=404, detail="Post not found")


@router.delete("/{book_id}/like")
def unlike_post(
    book_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        like_count = unset_like(db, user_id=user.id, book_id=book_id)
        return {"book_id": book_id, "liked": False, "like_count": like_count}
    except ValueError:
        raise HTTPException(status_code=404, detail="Post not found")


@router.get("/{book_id}/liked")
def liked_status(
    book_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return {
        "book_id": book_id,
        "liked": has_liked(db, user_id=user.id, book_id=book_id),
    }

# -------------------------
# Comments
# -------------------------

@router.get("/{book_id}/comments")
def get_comments(book_id: int, db: Session = Depends(get_db)):
    return {"book_id": book_id, "items": list_comments(db, book_id=book_id)}


@router.post("/{book_id}/comments")
def post_comment(
    book_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    body = (payload or {}).get("body")

    try:
        c = add_comment(db, user_id=user.id, book_id=book_id, body=body)
        return {"book_id": book_id, "comment": c}

    except ValueError as e:
        msg = str(e)

        if msg == "book_not_commentable":
            # book doesn't exist OR not public OR owner profile not public
            raise HTTPException(status_code=404, detail="Post not found")

        if msg == "empty_body":
            raise HTTPException(status_code=400, detail="Comment cannot be empty")

        if msg == "too_long":
            raise HTTPException(status_code=400, detail="Comment is too long")

        raise HTTPException(status_code=400, detail="Bad request")


@router.delete("/comments/{comment_id}")
def delete_comment_route(
    comment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        ok = delete_comment(db, comment_id=comment_id, user_id=user.id)
        if not ok:
            raise HTTPException(status_code=404, detail="Comment not found")
        return {"ok": True}

    except PermissionError:
        raise HTTPException(status_code=403, detail="Not allowed")
