# api/services/feed.py

from __future__ import annotations

from datetime import date
from typing import Optional, Tuple, List, Dict, Any

from sqlalchemy import and_, desc, asc, func
from sqlalchemy.orm import Session

from api.models import Book, Like, Comment
from api.auth_models import User


# --------------------------------------------------
# Cursor helpers
# --------------------------------------------------

def _parse_cursor(cursor: Optional[str]) -> Optional[Tuple[date, int]]:
    if not cursor:
        return None
    d, id_str = cursor.split("|", 1)
    return (date.fromisoformat(d), int(id_str))


def _encode_cursor(d: date, rid: int) -> str:
    return f"{d.isoformat()}|{rid}"


# --------------------------------------------------
# Public feed (LIST)
# --------------------------------------------------

def get_public_feed(
    db: Session,
    sort: str = "newest",
    genre: Optional[str] = None,
    review_type: Optional[str] = None,
    limit: int = 20,
    after: Optional[str] = None,
) -> Dict[str, Any]:
    cursor = _parse_cursor(after)

    q = (
        db.query(Book)
        .join(User, Book.owner_id == User.id)
        .filter(
            Book.visibility == "PUBLIC",
            User.profile_visibility == "PUBLIC",
        )
    )

    if genre and hasattr(Book, "genre"):
        q = q.filter(getattr(Book, "genre") == genre)

    if review_type:
        q = q.filter(Book.review_type == review_type)

    if sort == "oldest":
        order_cols = (asc(Book.review_date), asc(Book.id))
        if cursor:
            q = q.filter(
                (Book.review_date > cursor[0])
                | and_(Book.review_date == cursor[0], Book.id > cursor[1])
            )

    elif sort == "review_length":
        order_cols = (desc(func.length(Book.review_text)), desc(Book.id))

    elif sort == "review_type":
        order_cols = (asc(Book.review_type), desc(Book.review_date), desc(Book.id))

    else:
        # newest
        order_cols = (desc(Book.review_date), desc(Book.id))
        if cursor:
            q = q.filter(
                (Book.review_date < cursor[0])
                | and_(Book.review_date == cursor[0], Book.id < cursor[1])
            )

    q = q.order_by(*order_cols).limit(min(limit, 50))
    items: List[Book] = q.all()

    next_cursor = None
    if items:
        last = items[-1]
        if last.review_date:
            next_cursor = _encode_cursor(last.review_date, last.id)

    out = []
    for b in items:
        out.append(
            {
                "id": b.id,
                "book": {
                    "id": b.id,
                    "title": b.title,
                    "author": b.author,
                    "genre": getattr(b, "genre", None),
                    "cover_image_url": getattr(b, "cover_image_url", None),
                },
                "author": {
                    "id": b.owner.id if b.owner else None,
                    "username": b.owner.username if b.owner else None,
                },
                "body_preview": (
                    b.review_text[:280] + "..."
                    if b.review_text and len(b.review_text) > 280
                    else b.review_text
                ),
                "review_type": b.review_type,
                "review_date": b.review_date.isoformat() if b.review_date else None,
                "visibility": b.visibility,
                "like_count": b.like_count or 0,
                "comment_count": b.comment_count or 0,
            }
        )

    return {"items": out, "next_cursor": next_cursor}


# --------------------------------------------------
# Public feed (DETAIL – single item)
# --------------------------------------------------

def get_public_feed_item(db: Session, book_id: int) -> Optional[Dict[str, Any]]:
    book = (
        db.query(Book)
        .join(User, Book.owner_id == User.id)
        .filter(
            Book.id == book_id,
            Book.visibility == "PUBLIC",
            User.profile_visibility == "PUBLIC",
        )
        .first()
    )

    if not book:
        return None

    owner = book.owner

    return {
        "id": book.id,
        "book": {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "genre": getattr(book, "genre", None),
            "cover_image_url": book.cover_image_url,
        },
        "author": {
            "id": owner.id if owner else None,
            "username": owner.username if owner else None,
        },
        "body": book.review_text,
        "review_type": book.review_type,
        "review_date": book.review_date.isoformat() if book.review_date else None,
        "visibility": book.visibility,
        "like_count": book.like_count or 0,
        "comment_count": book.comment_count or 0,
        "created_at": book.created_at.isoformat() if book.created_at else None,
    }


# --------------------------------------------------
# Likes (service helpers)
# --------------------------------------------------

def _get_public_book_for_engagement(db: Session, book_id: int) -> Optional[Book]:
    """
    Used for like/unlike. Enforces:
    - Book is PUBLIC
    - Owner profile is PUBLIC
    """
    return (
        db.query(Book)
        .join(User, Book.owner_id == User.id)
        .filter(
            Book.id == book_id,
            Book.visibility == "PUBLIC",
            User.profile_visibility == "PUBLIC",
        )
        .first()
    )


def has_liked(db: Session, user_id: int, book_id: int) -> bool:
    return (
        db.query(Like)
        .filter(Like.user_id == user_id, Like.review_id == book_id)
        .first()
        is not None
    )


def set_like(db: Session, user_id: int, book_id: int) -> int:
    """
    Ensure user has liked this post (idempotent).
    Returns the new like_count.
    Raises ValueError if post doesn't exist / isn't public.
    """
    book = _get_public_book_for_engagement(db, book_id)
    if not book:
        raise ValueError("Post not found")

    existing = (
        db.query(Like)
        .filter(Like.user_id == user_id, Like.review_id == book_id)
        .first()
    )
    if existing:
        return book.like_count or 0

    db.add(Like(user_id=user_id, review_id=book_id))
    book.like_count = (book.like_count or 0) + 1
    db.commit()
    db.refresh(book)
    return book.like_count or 0


def unset_like(db: Session, user_id: int, book_id: int) -> int:
    """
    Ensure user has unliked this post (idempotent).
    Returns the new like_count.
    Raises ValueError if post doesn't exist / isn't public.
    """
    book = _get_public_book_for_engagement(db, book_id)
    if not book:
        raise ValueError("Post not found")

    existing = (
        db.query(Like)
        .filter(Like.user_id == user_id, Like.review_id == book_id)
        .first()
    )
    if not existing:
        return book.like_count or 0

    db.delete(existing)
    book.like_count = max(0, (book.like_count or 0) - 1)
    db.commit()
    db.refresh(book)
    return book.like_count or 0

# --------------------------------------------------
# Comments (service helpers)
# --------------------------------------------------

def list_comments(db: Session, book_id: int) -> list[dict]:
    """
    Public: list comments for a book (oldest -> newest).
    Returns [] if book doesn't exist or isn't public.
    """
    # enforce same public rules as feed
    book = (
        db.query(Book)
        .join(User, Book.owner_id == User.id)
        .filter(
            Book.id == book_id,
            Book.visibility == "PUBLIC",
            User.profile_visibility == "PUBLIC",
        )
        .first()
    )
    if not book:
        return []

    rows = (
        db.query(Comment, User)
        .join(User, Comment.user_id == User.id)
        .filter(Comment.review_id == book_id)
        .order_by(Comment.created_at.asc(), Comment.id.asc())
        .all()
    )

    out: list[dict] = []
    for c, u in rows:
        out.append(
            {
                "id": c.id,
                "book_id": c.review_id,
                "user": {"id": u.id, "username": u.username},
                "body": c.body,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
        )
    return out


def add_comment(db: Session, user_id: int, book_id: int, body: str) -> dict:
    """
    Auth: add a comment (returns created comment as dict).
    Raises ValueError if post not found or not public.
    """
    body = (body or "").strip()
    if not body:
        raise ValueError("Empty comment")

    # enforce same public rules as feed
    book = (
        db.query(Book)
        .join(User, Book.owner_id == User.id)
        .filter(
            Book.id == book_id,
            Book.visibility == "PUBLIC",
            User.profile_visibility == "PUBLIC",
        )
        .first()
    )
    if not book:
        raise ValueError("Post not found")

    c = Comment(review_id=book_id, user_id=user_id, body=body)
    db.add(c)

    book.comment_count = (book.comment_count or 0) + 1

    db.commit()
    db.refresh(c)

    u = db.query(User).filter(User.id == user_id).first()

    return {
        "id": c.id,
        "book_id": c.review_id,
        "user": {"id": u.id if u else user_id, "username": u.username if u else None},
        "body": c.body,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }

