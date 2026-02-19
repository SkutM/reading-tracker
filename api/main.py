from datetime import datetime
from typing import List

import requests
from fastapi import FastAPI, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from api import models, auth_routes, jwt_utils, schemas
from api.auth_models import User
from api.database import engine, get_db, Base
from api.routers import health, feed
from api.utils.time import iso_utc
from .routers import comments
import api.database as db_mod


print("DB MODULE FILE:", db_mod.__file__)
print("ENGINE DIALECT:", engine.dialect.name)
print("ENGINE URL:", str(engine.url))


def fetch_book_cover(title: str, author: str) -> str | None:
    search_url = "https://openlibrary.org/search.json"
    query = f"title: ({title}) AND author:({author})" if author else f"title:({title})"

    try:
        response = requests.get(search_url, params={"q": query, "limit": 1}, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get("numFound", 0) > 0 and data.get("docs"):
            first_doc = data["docs"][0]
            cover_id = first_doc.get("cover_i")
            if cover_id:
                return f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
    except requests.exceptions.RequestException as e:
        print(f"Error fetching cover from Open Library: {e}")
        return None

    return None


def json_utc(payload):
    return JSONResponse(content=jsonable_encoder(payload, custom_encoder={datetime: iso_utc}))


app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://reading-tracker-omega.vercel.app",
    "https://reading-tracker-git-main-scotts-projects-69acb861.vercel.app",
    "https://reading-tracker-cezljv7u7-scotts-projects-69acb861.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https://reading-tracker-.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _create_tables():
    Base.metadata.create_all(bind=engine)


app.include_router(auth_routes.auth_router)
app.include_router(health.router)
app.include_router(feed.router)
app.include_router(comments.router)


@app.get("/ping-db")
def ping_db():
    with engine.connect() as conn:
        conn.exec_driver_sql("SELECT 1;")
    return {"db": "online"}


@app.get("/")
def read_root():
    return {"message": "Welcome to the Reading Tracker API!"}


@app.post("/books/", response_model=schemas.Book)
def create_book(
    book: schemas.BookCreate,
    current_user: User = Depends(jwt_utils.get_current_user),
    db: Session = Depends(get_db),
):
    cover_url = fetch_book_cover(book.title, book.author or "")

    db_book = models.Book(
        title=book.title,
        author=book.author,
        cover_image_url=cover_url,
        review_text=book.review_text,
        is_recommended=book.is_recommended,
        owner_id=current_user.id,
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return json_utc(db_book)


@app.get("/books/", response_model=List[schemas.Book])
def read_books(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(jwt_utils.get_current_user),
    db: Session = Depends(get_db),
):
    books = (
        db.query(models.Book)
        .filter(models.Book.owner_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return json_utc(books)


@app.get("/books/{book_id}", response_model=schemas.Book)
def read_book(
    book_id: int,
    current_user: User = Depends(jwt_utils.get_current_user),
    db: Session = Depends(get_db),
):
    book = (
        db.query(models.Book)
        .filter(models.Book.id == book_id, models.Book.owner_id == current_user.id)
        .first()
    )
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return json_utc(book)


@app.put("/books/{book_id}", response_model=schemas.Book)
def update_book(
    book_id: int,
    book_update: schemas.BookUpdate,
    current_user: User = Depends(jwt_utils.get_current_user),
    db: Session = Depends(get_db),
):
    db_book = (
        db.query(models.Book)
        .filter(models.Book.id == book_id, models.Book.owner_id == current_user.id)
        .first()
    )
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    update_data = book_update.model_dump(exclude_unset=True)

    if "title" in update_data or "author" in update_data:
        new_title = update_data.get("title", db_book.title)
        new_author = update_data.get("author", db_book.author or "")
        db_book.cover_image_url = fetch_book_cover(new_title, new_author)

    for key, value in update_data.items():
        setattr(db_book, key, value)

    db.commit()
    db.refresh(db_book)
    return json_utc(db_book)


@app.delete("/books/{book_id}", status_code=204)
def delete_book(
    book_id: int,
    current_user: User = Depends(jwt_utils.get_current_user),
    db: Session = Depends(get_db),
):
    book = (
        db.query(models.Book)
        .filter(models.Book.id == book_id, models.Book.owner_id == current_user.id)
        .first()
    )
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    db.delete(book)
    db.commit()
    return {}