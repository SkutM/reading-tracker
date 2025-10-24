from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import requests
from fastapi.middleware.cors import CORSMiddleware # for auth middleware

# auth
from . import auth_routes
from . import jwt_utils
from .auth_models import User # need User model for type hinting/relationships

# database and model defs
from . import models, schemas
from .database import SessionLocal, engine, get_db

# alembic handles tables created if they don't alr exist

# util function to search Open Library for a cover URL

def fetch_book_cover(title: str, author: str) -> str | None:
    search_url = "https://openlibrary.org/search.json"

    # query combining title & author
    query = f"title: ({title}) AND author:({author})" if author else f"title:({title})"

    try:
        response = requests.get(search_url, params={'q': query, 'limit': 1}, timeout=5)
        response.raise_for_status() # raise exception for bad status codes

        data = response.json()

        # check if any docs were returned
        if data.get('numFound') > 0 and data.get('docs'):
            first_doc = data['docs'][0]

            # Open Lib uses a cover ID to link to a separate img service
            if 'cover_i' in first_doc:
                cover_id = first_doc['cover_i']
                # construct cover img url using the medium size (M)
                cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
                return cover_url
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching cover from Open Library: {e}")
        return None
    
    return None

# fast api init
app = FastAPI()

# auth cors middleware
# OPTIONS pre-flight checks, even with Vite proxy
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# auth router
app.include_router(auth_routes.auth_router)



# Endpoint to check API status
@app.get("/")
def read_root():
    return {"message": "Welcome to the Reading Tracker API!"}

# CRUD logic: create a book
@app.post("/books/", response_model=schemas.Book)
def create_book(
    book: schemas.BookCreate,
    # require auth, below
    current_user: User = Depends(jwt_utils.get_current_user),
    db: Session = Depends(get_db)
):

    # fetch cover img url
    cover_url = fetch_book_cover(book.title, book.author or "")

    # create an instance of the SQLAlchemy model
    db_book = models.Book(
        title=book.title,
        author=book.author,
        # save fetched url here
        cover_image_url=cover_url,
        review_text=book.review_text,
        is_recommended=book.is_recommended,
        # set foreign key
        owner_id=current_user.id
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book) # get the final obj w/ the db-generated ID/timestamps
    return db_book

# CRUD: read all books
@app.get("/books/", response_model=List[schemas.Book])
def read_books(
    skip: int = 0, 
    limit: int = 100,
    # require auth, below
    current_user: User = Depends(jwt_utils.get_current_user),
    db: Session = Depends(get_db)
):
    # new auth below, see comment
    # query all books from the db -- *only books owned by curr user*
    books = db.query(models.Book).filter(models.Book.owner_id == current_user.id).offset(skip).limit(limit).all()
    return books

# CRUD: Read a single book
@app.get("/books/{book_id}", response_model=schemas.Book)
def read_book(
    book_id: int,
    # auth below
    current_user: User = Depends(jwt_utils.get_current_user),
    db: Session = Depends(get_db)
):
    # query one book by its ID (and enforce ownership, auth)
    book = db.query(models.Book).filter(
        models.Book.id == book_id,
        # ownership check below
        models.Book.owner_id == current_user.id
    ).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

# CRUD: Update a Book
@app.put("/books/{book_id}", response_model=schemas.Book)
def update_book(
    book_id: int,
    book_update: schemas.BookUpdate, # re-use the BookCreate schema for updates
    current_user: User = Depends(jwt_utils.get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Query the book and enforce ownership
    db_book = db.query(models.Book).filter(
        models.Book.id == book_id,
        models.Book.owner_id == current_user.id # ownership check
    ).first()

    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # 2. update all fields w/ data from the request body
    # we use dicts to iterate thru all fields in pydantic schema
    update_data = book_update.model_dump(exclude_unset=True)

    # for cover, re-fetch
    if "title" in update_data or "author" in update_data:
        # use incoming new title/author, fall back to existing if not provided
        new_title = update_data.get("title", db_book.title)
        new_author = update_data.get("author", db_book.author or "")

        # fetch new cover url & update book obj
        new_cover_url = fetch_book_cover(new_title, new_author)
        db_book.cover_image_url = new_cover_url

    for key, value in update_data.items():
        setattr(db_book, key, value)

    # 3. Commit changes
    db.commit()
    db.refresh(db_book)

    return db_book

# CRUD: Delete a Book
@app.delete("/books/{book_id}", status_code=204)
def delete_book(
    book_id: int,
    current_user: User = Depends(jwt_utils.get_current_user),
    db: Session = Depends(get_db)
):
    # Query one book by its ID & enforce ownership
    book = db.query(models.Book).filter(
        models.Book.id == book_id,
        models.Book.owner_id == current_user.id # ownership check
    ).first()

    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    
    db.delete(book)
    db.commit()

    # 204 No Content is the standard response for a successful DELETE
    return {}
