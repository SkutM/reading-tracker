from datetime import date
from typing import Optional, Tuple, List

from sqlalchemy import and_, desc, asc, func
from sqlalchemy.orm import Session

from api.models import Book # Book has the social-readia columns
from api.auth_models import User # User has profile_visibility

# cursor helpers ---------------------

# cursor is a tuple (review_date, id) encoded as "YYYY-MM-DD|<id>"

# cursor pagination:
# a technique using a token (cursor) that represents the
# precise position in an ordered data set, allowing
# efficient and consistent retrieval of the next page

# why is cursor (date, id) ?
# 1) even if many items have the same date, the ID ensures
# uniqueness
# 2) index-friendly filtering:
# idx_books_vis_date_id (visibility, review_date, id)
# supports:
# WHERE (review_date < cursor_date)
#  OR (review_date = cursor_date AND id < cursor_id)
# lightning fast

# further, these are private helper functions denoted by _
# meaning: shouldn't be called directly from routes;
# shouldn't be considered "API functions"; exist only to
# support the main pagination logic
# i.e., "These functions support the module but aren't meant
# for external use"
# purely a readability + safety signal

# why do we do (cursor: Optional[str]) -> Optional[Tuple[date, int]]: ?
# this is a type hint -- it tells editors what types the fnct
# expects & returns. cursor: Optional[str] means:
# cursor can be either: a str, like "2025-11-13|42" or "None"
# "Optional[Tuple[date, int]]" means the function will return:
# either a tuple (date, id)
# or None

def _parse_cursor(cursor: Optional[str]) -> Optional[Tuple[date, int]]:
    # Turn a cursor string into (date, id) or None if not provided
    if not cursor:
        return None
    # below, "split on the first | only"
    d, id_str = cursor.split("|", 1)
    # date.fromisoformat turns "2024-05-10" into
    # datetime.date(2024, 5, 10)
    return (date.fromisoformat(d), int(id_str))


# *inverse of _parse_cursor*: takes the Python vals and turns
# them back into the string cursor we send to the client
def _encode_cursor(d: date, rid: int) -> str:
    # Turn (date, id) into a cursor string
    return f"{d.isoformat()}|{rid}"

# core feed query ---------------

def get_public_feed(
        db: Session,
        sort: str = "newest",
        genre: Optional[str] = None, # only used once you add Book.genre
        review_type: Optional[str] = None, # RECOMMENDED | NOT_RECOMMENDED | NEUTRAL
        limit: int = 20,
        after: Optional[str] = None, # cursor from prev page
):
    
    # return a page of public 'reviews' (books with review data)
    # plus a cursor for the next page, if any

    cursor = _parse_cursor(after)

    # base query: only public books from public profiles
    q = (

        # .join() for concatenating strings is highly diff
        # from this -- in SQLAlchemy .join() joins dbs together
        # i.e., "combine rows from the Book table w rows from
        # the User table where Book.owner_id == User.id"
        db.query(Book).join(User, Book.owner_id == User.id)
        .filter(
            Book.visibility == "PUBLIC",
            User.profile_visibility == "PUBLIC",
        )
    )

    # optional filters

    # hasattr checks: "does this obj have an attr named
    # 'genre'? True if yes, false if no"
    # "Does Book have a genre column?"
    if genre and hasattr(Book, "genre"):
        # safe: only applies if you later add Book.genre

        # getattr returns the actual attribute
        # i.e., Book.genre == genre only if it exists
        # "give me Book.genre dynamically"
        q = q.filter(getattr(Book, "genre") == genre)

    if review_type:
        q = q.filter(Book.review_type == review_type)

    # sorting + keyset pagination
    if sort == "oldest":
        # oldest first: (date ASC, id ASC)

        # asc() is SQLAlchemy's way of saying:
        # "Sort this column in ascending order"
        # desc() would then be newest-> oldest (descending)
        order_cols = (asc(Book.review_date), asc(Book.id))
        if cursor:
            q = q.filter(
                
                # | and not "or" in SQLAlchemy -- "or" tries
                # to evaluate actual booleans, which would not
                # do what we're trying to do -- "this is illegal"

                # cursor[0] = review_date
                # cursor[1] = id
                # "find books whose review_date is later than the
                # last one we saw"
                (Book.review_date > cursor[0]) |
                # and_() is SQLAlchemy's explicit AND constructor
                # you cannot use Python's "and" because it does
                # truthiness evaluation, not SQL building
                and_(Book.review_date == cursor[0], Book.id > cursor[1])
            )

    elif sort == "review_length":
        # longest review_text first
        # note: keyset pagination on length is more complex; we still
        # return a cursor using review_date/id but treat this as "good enough" for MVP

        # func.length is SQLAlchemy's way of calling SQL functs --
        # in this case, "LENGTH"
        # means: "Order the results by longest review_text first,
        # and if there's a tie, use descending ID"
        order_cols = (desc(func.length(Book.review_text)), desc(Book.id))

    elif sort == "review_type":
        # group by type, then newest within each type
        order_cols = (asc(Book.review_type), desc(Book.review_date), desc(Book.id))

    else:
        # default: newest first - (date DESC, id DESC)
        order_cols = (desc(Book.review_date), desc(Book.id))
        if cursor:
            q = q.filter(
                (Book.review_date < cursor[0]) |
                and_(Book.review_date == cursor[0], Book.id < cursor[1]) 
            )

    # limit results (hard cap at 50)

    # the * is because:
    # order_cols is a tuple, so * unpacks the tuple so each
    # item is passed as a separate argument
    # without the * , SQLAlchemy thinks order_cols is one argument
    # which it cannot translate properly.
    # WITH the *, q.order_by(*order_cols)
    # becomes:
    # q.order_by(
    #   asc(Book.review_date),
    #   asc(Book.id)
    # )

    ''' ex:
    def f(a, b):
    print(a, b)

    pair = (1, 2)

    f(*pair)    # prints "1 2"
    f(pair)     # error: f expects 2 args, not 1

    '''

    # what is q?
    # q is a SQLAlchemy query object (we built the query
    # earlier)
    # items = q.all() "execute this SQL query & give me the
    # list of results" -- at this point SQLAlchemy:
    # compiles the SQL
    # sends it to SQLite
    # fetches all rows
    # converts each row into a Book model instance

    # what is items: (the colon)? 
    # items: List[Book] = q.all() is a type hint
    # tells editors: "items will be a list of Book objs"
    q = q.order_by(*order_cols).limit(min(limit, 50))
    items: List[Book] = q.all()

    # build next cursor, if there is another page

    # "build next cursor" means, "Look at the last item
    # in the current page, extract its (date, id), encode it,
    # and send that encoded value to the client so the client
    # can request the NEXT page"

    # "page" is just "A chunk (subset) of results returned
    # by the backend"
    # instead of returning ALL books, ALL posts, and ALL messages,
    # you return
    # page 1 --> the first 20 items
    # page 2 --> the next 20
    # page 3 --> the next 20
    # etc. -- one batch of results at a time
    next_cursor = None
    if items:
        last = items[-1]
        if last.review_date:
            next_cursor = _encode_cursor(last.review_date, last.id)

    # shape output for the frontend

    # this is where "ORM objects" turn into "JSON your frontend
    # actually cares about"

    # out will hold a bunch of dicts, one per book/review
    # items is your list of Book ORM objects from q.all()
    out = []

    # loop over each Book from the query
    for b in items:
        out.append(
            {
                # this top level:
                # grouping book-related fields here
                "id": b.id,
                "book": {
                    "id": b.id,
                    "title": b.title,
                    "author": b.author,
                    "genre": getattr(b, "genre", None),
                },
                # now "author" -- the user who wrote the review
                "author": {
                    "id": b.owner.id if b.owner else None,
                    "username": b.owner.username if b.owner else None,
                },
                # truncate review text into a preview
                "body_preview": (
                    b.review_text[:280] + "..."
                    if b.review_text and len(b.review_text) > 280
                    else b.review_text
                ),
                # simple scalar fields
                # the remaining individual fields on the Book
                # model that you want to send to the frontend
                # no structure, no nesting, no relationships --
                # just field: value mappings
                "review_type": b.review_type,
                "review_date": b.review_date.isoformat() if b.review_date else None,
                "visibility": b.visibility,
                "like_count": b.like_count or 0,
                "comment_count": b.comment_count or 0,
            }
        )

    # what are we returning?
    # this returns a dict with two keys:
    # "items": out
    # out is the list of shaped feed objs we built with out
    # earlier 
    # "next_cursor": next_cursor
    # next_cursor is the string cursor like "2025-11-13|42"
    # tells the frontend how to load the next page
    # if there's no next page (fewer than limit results),
    # it will be None

    # FastAPI automatically converts the returned dict to
    # JSON because FastAPI sees you returned a normal
    # Python dict and knows how to serialize it

    # items: a list of Book ORM objs retrieved from the db
    # the raw results from the db query -- actual Book model
    # instances. so, items = raw DB rows as Python model objs

    # ORM: Object-Relational Mapper
    # Lets you work with db rows as Python objs instead of
    # raw SQL queries
    # so instead of writing:
    # SELECT id, title, author FROM books WHERE id = 10;
    # you write:
    # book = db.query(Book).filter(Book.id == 10).first()
    # i.e., generates SQL automatically
    # converts SQL rows --> Python objs
    """
    
    “Each item returned by the query is a Python object (Book) 
    generated by SQLAlchemy that represents a row in the 
    database. You interact with it like a normal object, 
    and the ORM handles converting it to/from SQL.”

    """


    # out: a new list you build manually, where every element
    # is a JSON-ready dictionary
    # out = human-readable, JSON-safe version of items

    # next_cursor: a string bookmark pointing to the next page
    # of results
    # i.e., a string used to fetch the NEXT page of results
    return {"items": out, "next_cursor": next_cursor}

# what we just did, conceptually:

# We centralized *all* the "how to build a feed" logic into
# one function (get_public_feed)

# Keyset pagination via (review_date, id) means we don't
# have to use (OFFSET), which gets slow on large tables

# The service returns a plain Python dict that is already
# shaped for the frontend -- so the FastAPI route can
# basically just (return get_public_feed(...))