from __future__ import annotations

from datetime import timezone

from sqlalchemy.orm import Session

from ..models import Book, Comment
from ..auth_models import User


# --------------------------------------------------
# Comments (service helpers)
# --------------------------------------------------

def iso_utc(dt):
    if not dt:
        return None
    # If DB gave us a naive datetime, assume it's UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # Always return UTC with Z suffix
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def list_comments(db: Session, book_id: int) -> list[dict]:
    """
    Public: list comments for a book (oldest -> newest).
    Returns [] if book doesn't exist or isn't public / owner profile isn't public.
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
                "review_id": c.review_id,
                "user": {"id": u.id, "username": u.username},
                "body": c.body,
                "created_at": iso_utc(c.created_at),
            }
        )
    return out


def add_comment(db: Session, book_id: int, user_id: int, body: str) -> dict:
    """
    Auth: add a comment to a PUBLIC book (and PUBLIC profile).
    Raises ValueError if the book isn't commentable.
    """
    # comment only on public things (same policy as the public feed)
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
        raise ValueError("book_not_commentable")

    body = (body or "").strip()
    if not body:
        raise ValueError("empty_body")
    if len(body) > 2000:
        raise ValueError("too_long")

    c = Comment(review_id=book_id, user_id=user_id, body=body)
    db.add(c)

    # keep denormalized count in sync
    if getattr(book, "comment_count", None) is not None:
        book.comment_count = int(book.comment_count or 0) + 1

    db.commit()
    db.refresh(c)

    # hydrate author for response
    u = db.query(User).filter(User.id == user_id).first()
    return {
        "id": c.id,
        "review_id": c.review_id,
        "user": {"id": u.id, "username": u.username if u else None},
        "body": c.body,
        "created_at": iso_utc(c.created_at),
    }


def delete_comment(db: Session, comment_id: int, user_id: int) -> bool:
    """
    Auth: delete your own comment.
    Returns True if deleted, False if not found.
    Raises PermissionError if not the owner.
    """
    c = db.query(Comment).filter(Comment.id == comment_id).first()
    if not c:
        return False
    if c.user_id != user_id:
        raise PermissionError("not_owner")

    # decrement count if we can find the book
    book = db.query(Book).filter(Book.id == c.review_id).first()
    if book and getattr(book, "comment_count", None) is not None:
        book.comment_count = max(0, int(book.comment_count or 0) - 1)

    db.delete(c)
    db.commit()
    return True
