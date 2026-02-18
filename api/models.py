from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Date, text # foreignkey for auth
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

    review_type = Column(String(20), nullable=True)
    review_date = Column(Date, nullable=True)
    started_date = Column(Date, nullable=True)
    finished_date = Column(Date, nullable=True)
    like_count = Column(Integer, nullable=False, default=0)
    comment_count = Column(Integer, nullable=False, default=0)

    # link book to user for auth (foreign key)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="books")

class Follow(Base):
    __tablename__ = "follows"
    follower_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    followee_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

class Like(Base):
    __tablename__ = "likes"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    review_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    review_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
