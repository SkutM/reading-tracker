# api/scripts/seed_social_readia.py
import random
from datetime import date, timedelta, datetime

from ..database import SessionLocal
from ..auth_models import User
from ..models import Book


def run():
    db = SessionLocal()
    try:
        # 1) Create some users
        users: list[User] = []
        for i in range(10):
            u = User(
                username=f"user{i}",
                password_hash="not_used_in_seed",  # just to satisfy NOT NULL
            )
            # profile_visibility column was added via migration
            if hasattr(u, "profile_visibility"):
                u.profile_visibility = "PUBLIC"

            db.add(u)
            users.append(u)

        db.flush()  # assign IDs

        # 2) Create some books (acting as reviews)
        genres = ["Fiction", "Nonfiction", "Sci-Fi", "Fantasy", "Mystery"]
        books: list[Book] = []

        for i in range(30):
            owner = random.choice(users)
            rd = date.today() - timedelta(days=random.randint(0, 120))

            b = Book(
                title=f"Book {i}",
                author=f"Author {i}",
                cover_image_url=None,
                review_text=f"Review {i}: some thoughts about Book {i}.",
                is_recommended=random.choice([True, False]),
                read_on=datetime.utcnow(),
                created_at=datetime.utcnow(),
                owner_id=owner.id,
            )

            # set Social Readia fields if present on the model
            if hasattr(b, "visibility"):
                b.visibility = "PUBLIC"  # you can randomize later if you want

            if hasattr(b, "review_type"):
                b.review_type = random.choice(
                    ["RECOMMENDED", "NOT_RECOMMENDED", "NEUTRAL"]
                )

            if hasattr(b, "review_date"):
                b.review_date = rd

            if hasattr(b, "like_count"):
                b.like_count = random.randint(0, 20)

            if hasattr(b, "comment_count"):
                b.comment_count = random.randint(0, 5)

            db.add(b)
            books.append(b)

        db.commit()
        print("✅ Seeded Social Readia demo data.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
