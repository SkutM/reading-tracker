from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from passlib.context import CryptContext

from .database import Base

# set up password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"],
    deprecated="auto",
)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)

    # link to Book table (one user has many books)
    books = relationship("Book", back_populates="owner")

    # User Model Methods
    def set_password(self, password):
        self.password_hash = pwd_context.hash(password)
    
    def check_password(self, password):
        try:
            return pwd_context.verify(password, self.password_hash)
        except ValueError:
            return False
    
class TokenBlocklist(Base):
    __tablename__ = 'token_blocklist'

    id = Column(Integer, primary_key=True)
    jti = Column(String(36), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)