from sqlalchemy.orm import Session

from api.models import Book, Like
from api.auth_models import User


def _get_public_book_or_none(db: Session, book_id: int) -> Book | None:
    """
    Only allow liking PUBLIC books whose owner's profile is PUBLIC
    (same rule as your public feed).
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


def toggle_like(db: Session, book_id: int, user_id: int) -> tuple[bool, int]:
    """
    Toggle like for (user_id, book_id).

    Returns: (liked_now, like_count)
    """
    book = _get_public_book_or_none(db, book_id)
    if not book:
        # caller will translate this to 404
        raise ValueError("Post not found")

    existing = (
        db.query(Like)
        .filter(Like.user_id == user_id, Like.review_id == book_id)
        .first()
    )

    if existing:
        # unlike
        db.delete(existing)
        book.like_count = max((book.like_count or 0) - 1, 0)
        liked_now = False
    else:
        # like
        db.add(Like(user_id=user_id, review_id=book_id))
        book.like_count = (book.like_count or 0) + 1
        liked_now = True

    db.commit()
    db.refresh(book)

    return liked_now, book.like_count or 0
