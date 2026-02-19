from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..jwt_utils import get_current_user
from ..auth_models import User
from ..services.comments import list_comments, add_comment, delete_comment

router = APIRouter(prefix="/comments", tags=["comments"])


class CommentCreate(BaseModel):
    body: str


@router.get("/{book_id}")
def public_comments(book_id: int, db: Session = Depends(get_db)):
    # returns [] if not public/not found
    return {"items": list_comments(db, book_id)}


@router.post("/{book_id}")
def create_comment(
    book_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        created = add_comment(db, book_id, user.id, payload.body)
        return created
    except ValueError as e:
        if str(e) == "book_not_commentable":
            raise HTTPException(status_code=404, detail="Book not found or not public")
        if str(e) == "empty_body":
            raise HTTPException(status_code=400, detail="Comment body cannot be empty")
        if str(e) == "too_long":
            raise HTTPException(status_code=400, detail="Comment too long")
        raise HTTPException(status_code=400, detail="Invalid comment")


@router.delete("/{comment_id}")
def remove_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        ok = delete_comment(db, comment_id, user.id)
        if not ok:
            raise HTTPException(status_code=404, detail="Comment not found")
        return {"ok": True}
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not allowed to delete this comment")
