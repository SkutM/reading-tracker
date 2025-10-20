from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Base schema for data coming in (what the user submits)
class BookBase(BaseModel):
    title: str
    author: Optional[str] = None
    cover_image_url: Optional[str] = None
    review_text: Optional[str] = None
    is_recommended: Optional[bool] = None

# Schema used when creating a book (adds no new fields)
class BookCreate(BookBase):
    pass

# Schema used for responses (what the API sends back)
# This includes databased-generated fields like id and read_on
class Book(BookBase):
    id: int
    read_on: datetime
    created_at: datetime

    class Config:
        # Allows conversion from SQLAlchemy ORM models to
        # Pydantic models
        from_attributes = True

# new
class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    cover_image_url: Optional[str] = None
    review_text: Optional[str] = None
    is_recommended: Optional[bool] = None