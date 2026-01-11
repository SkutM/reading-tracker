"""social readia: reviews privacy, social tables, dates, counts

Revision ID: daeede6634d4
Revises: f217a5cb3762
Create Date: 2025-10-27 20:51:03.739138
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "daeede6634d4"
down_revision: Union[str, Sequence[str], None] = "f217a5cb3762"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, col: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return any(c["name"] == col for c in insp.get_columns(table))


def upgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"

    # ---- users.profile_visibility ----
    if not _has_column("users", "profile_visibility"):
        op.add_column(
            "users",
            sa.Column("profile_visibility", sa.String(16), nullable=False, server_default="PUBLIC"),
        )
        # Drop the default only on engines that support it (NOT SQLite)
        if not is_sqlite:
            op.alter_column("users", "profile_visibility", server_default=None)

    # ---- books: visibility/type/dates/counts ----
    if not _has_column("books", "visibility"):
        op.add_column("books", sa.Column("visibility", sa.String(16), nullable=False, server_default="PUBLIC"))
    if not _has_column("books", "review_type"):
        op.add_column("books", sa.Column("review_type", sa.String(20), nullable=True))
    if not _has_column("books", "review_date"):
        op.add_column("books", sa.Column("review_date", sa.Date(), nullable=True))
    if not _has_column("books", "started_date"):
        op.add_column("books", sa.Column("started_date", sa.Date(), nullable=True))
    if not _has_column("books", "finished_date"):
        op.add_column("books", sa.Column("finished_date", sa.Date(), nullable=True))
    if not _has_column("books", "like_count"):
        op.add_column("books", sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"))
        if not is_sqlite:
            op.alter_column("books", "like_count", server_default=None)
    if not _has_column("books", "comment_count"):
        op.add_column("books", sa.Column("comment_count", sa.Integer(), nullable=False, server_default="0"))
        if not is_sqlite:
            op.alter_column("books", "comment_count", server_default=None)

    # ---- social tables ----
    # create_table with checkfirst isn't available; create if missing by probing
    insp = sa.inspect(bind)
    existing_tables = set(insp.get_table_names())

    if "follows" not in existing_tables:
        op.create_table(
            "follows",
            sa.Column("follower_id", sa.Integer(), nullable=False),
            sa.Column("followee_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.ForeignKeyConstraint(["follower_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["followee_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("follower_id", "followee_id"),
        )

    if "likes" not in existing_tables:
        op.create_table(
            "likes",
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("review_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["review_id"], ["books.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("user_id", "review_id"),
        )

    if "comments" not in existing_tables:
        op.create_table(
            "comments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("review_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.ForeignKeyConstraint(["review_id"], ["books.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        )

    # ---- indexes ----
    # guard each index creation
    def _has_index(table: str, name: str) -> bool:
        return any(ix["name"] == name for ix in insp.get_indexes(table))

    if not _has_index("books", "idx_books_vis_date_id"):
        op.create_index("idx_books_vis_date_id", "books", ["visibility", "review_date", "id"], unique=False)

    if not _has_index("likes", "idx_likes_review"):
        op.create_index("idx_likes_review", "likes", ["review_id"], unique=False)

    if not _has_index("comments", "idx_comments_review_created"):
        op.create_index("idx_comments_review_created", "comments", ["review_id", "created_at"], unique=False)

    if not _has_index("follows", "idx_follows_follower"):
        op.create_index("idx_follows_follower", "follows", ["follower_id"], unique=False)

    if not _has_index("follows", "idx_follows_followee"):
        op.create_index("idx_follows_followee", "follows", ["followee_id"], unique=False)


def downgrade() -> None:
    # drop indexes (ignore if missing)
    bind = op.get_bind()
    insp = sa.inspect(bind)
    def _has_index(table: str, name: str) -> bool:
        return any(ix["name"] == name for ix in insp.get_indexes(table))

    if _has_index("follows", "idx_follows_followee"):
        op.drop_index("idx_follows_followee", table_name="follows")
    if _has_index("follows", "idx_follows_follower"):
        op.drop_index("idx_follows_follower", table_name="follows")
    if _has_index("comments", "idx_comments_review_created"):
        op.drop_index("idx_comments_review_created", table_name="comments")
    if _has_index("likes", "idx_likes_review"):
        op.drop_index("idx_likes_review", table_name="likes")
    if _has_index("books", "idx_books_vis_date_id"):
        op.drop_index("idx_books_vis_date_id", table_name="books")

    # drop tables (ignore if missing)
    existing_tables = set(insp.get_table_names())
    if "comments" in existing_tables:
        op.drop_table("comments")
    if "likes" in existing_tables:
        op.drop_table("likes")
    if "follows" in existing_tables:
        op.drop_table("follows")

    # drop columns (ignore if missing)
    for col in ("comment_count", "like_count", "finished_date", "started_date", "review_date", "review_type", "visibility"):
        if _has_column("books", col):
            op.drop_column("books", col)
    if _has_column("users", "profile_visibility"):
        op.drop_column("users", "profile_visibility")
