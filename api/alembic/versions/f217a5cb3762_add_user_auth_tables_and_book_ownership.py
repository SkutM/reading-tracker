"""add user auth tables and book ownership

Revision ID: f217a5cb3762
Revises: 36bae87080c2
Create Date: 2025-10-20 18:46:36.599149
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "f217a5cb3762"
down_revision: Union[str, Sequence[str], None] = "36bae87080c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names()


def _has_column(table: str, col: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return any(c["name"] == col for c in insp.get_columns(table))


def upgrade() -> None:
    import logging

    logging.getLogger("alembic.runtime.migration").warning(">> f217a5cb3762 upgrade() entered")

    # -------------------
    # token_blocklist
    # -------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS token_blocklist (
            id INTEGER NOT NULL PRIMARY KEY,
            jti VARCHAR(36) NOT NULL,
            created_at DATETIME NOT NULL
        );
    """)

    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_indexes = {ix["name"] for ix in insp.get_indexes("token_blocklist")}
    if "ix_token_blocklist_jti" not in existing_indexes:
        op.create_index(op.f("ix_token_blocklist_jti"), "token_blocklist", ["jti"], unique=False)

    # -------------------
    # users
    # -------------------
    if not _has_table("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("username", sa.String(length=80), nullable=False),
            sa.Column("password_hash", sa.String(length=128), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    # -------------------
    # books.owner_id + FK
    # -------------------
    if not _has_column("books", "owner_id"):
        op.add_column("books", sa.Column("owner_id", sa.Integer(), nullable=True))

    # rebuild books table with FK constraint
    op.execute("PRAGMA foreign_keys=OFF;")
    op.execute("""
        CREATE TABLE books_tmp AS
        SELECT id, title, author, cover_image_url, review_text,
               is_recommended, read_on, created_at, owner_id
        FROM books;
    """)
    op.execute("DROP TABLE books;")
    op.execute("""
        CREATE TABLE books (
            id INTEGER PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            author VARCHAR(255),
            cover_image_url VARCHAR(512),
            review_text TEXT,
            is_recommended BOOLEAN,
            read_on DATETIME,
            created_at DATETIME,
            owner_id INTEGER,
            CONSTRAINT fk_books_owner_id_users_id
                FOREIGN KEY(owner_id) REFERENCES users(id)
        );
    """)
    op.execute("""
        INSERT INTO books (
            id, title, author, cover_image_url, review_text,
            is_recommended, read_on, created_at, owner_id
        )
        SELECT id, title, author, cover_image_url, review_text,
               is_recommended, read_on, created_at, owner_id
        FROM books_tmp;
    """)
    op.execute("DROP TABLE books_tmp;")
    op.execute("PRAGMA foreign_keys=ON;")


def downgrade() -> None:
    op.drop_constraint("fk_books_owner_id_users_id", "books", type_="foreignkey")
    op.drop_column("books", "owner_id")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_token_blocklist_jti"), table_name="token_blocklist")
    op.drop_table("token_blocklist")
