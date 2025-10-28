from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey # foreignkey for auth
from sqlalchemy.orm import relationship # for auth
from api.database import Base
from datetime import datetime

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)

    # core book data
    title = Column(String(255), nullable=False)
    author = Column(String(255))
    cover_image_url = Column(String(512))

    # flip side of card
    review_text = Column(Text)
    is_recommended = Column(Boolean)

    # metadata
    read_on = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # link book to user for auth (foreign key)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="books")