from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# what user submits
class BookBase(BaseModel):
    title: str
    author: Optional[str] = None
    cover_image_url: Optional[str] = None
    review_text: Optional[str] = None
    is_recommended: Optional[bool] = None

# when creating a book
class BookCreate(BookBase):
    pass

# what the API sends back
class Book(BookBase):
    id: int
    read_on: datetime
    created_at: datetime

    class Config:
        # conversion from SQLAlchemy ORM models to
        # Pydantic models
        from_attributes = True

# new
class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    cover_image_url: Optional[str] = None
    review_text: Optional[str] = None
    is_recommended: Optional[bool] = None