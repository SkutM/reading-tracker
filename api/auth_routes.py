from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from . import auth_schemas, jwt_utils
from .database import get_db
from .auth_models import User, pwd_context, TokenBlocklist
from .config import settings

# init FastAPI router (similar to Flask bp)
auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# jwt helpers
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def is_token_in_blocklist(db: Session, jti: str):
    return db.query(TokenBlocklist).filter(TokenBlocklist.jti == jti).first() is not None

# route fncts

@auth_router.post("/register", response_model=auth_schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_in: auth_schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. check for existing user
    if get_user_by_username(db, user_in.username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")
    
    # 2. hash password and create new user
    new_user = User(username=user_in.username)
    new_user.set_password(user_in.password)

    # 3. save to db
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@auth_router.post("/login", response_model=auth_schemas.Token)
def login_for_access_token(user_in: auth_schemas.LoginRequest, db: Session = Depends(get_db)):
    user = get_user_by_username(db, user_in.username)

    # 1. check user existence & passw
    if not user or not user.check_password(user_in.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 2. create jwt token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # store user ID as the subject ("sub") for the token identity
    access_token = jwt_utils.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60 # convert minutes to seconds for client
    }

# protected route ex
@auth_router.get("/profile", response_model=auth_schemas.UserResponse)
def read_profile(current_user: User = Depends(jwt_utils.get_current_user)):
    # the get_current_user dependency automatically checks the token & fetches the user obj
    return current_user