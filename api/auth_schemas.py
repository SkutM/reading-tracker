from pydantic import BaseModel, Field
from typing import List, Optional

# request schemas
class UserCreate(BaseModel):
    # matches the input fields for registration
    username: str
    password: str

class LoginRequest(BaseModel):
    # matches the input fields for login
    username: str
    password: str

# response schemas
class Token(BaseModel):
    # schema for the response after a successful login/refresh
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class UserResponse(BaseModel):
    # schema for returning basic user details (e.g., after registration)
    id: int
    username: str