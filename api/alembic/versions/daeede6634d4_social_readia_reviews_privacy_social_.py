"""social readia: reviews privacy, social tables, dates, counts

Revision ID: daeede6634d4
Revises: f217a5cb3762
Create Date: 2025-10-27 20:51:03.739138

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'daeede6634d4'
down_revision: Union[str, Sequence[str], None] = 'f217a5cb3762'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # add col safely w/ a default for old data
    op.add_column('users', sa.Column('profile_visibility', sa.String(16), nullable=False, server_default='PUBLIC'))
    # remove the def so it doesn't apply forever
    op.alter_column('users', 'profile_visibility', server_default=None) 

    # reviews: visibility + review_type + dates + counts
    op.add_column('reviews', sa.Column('visibility', sa.String(16), nullable=False, server_default='PUBLIC'))
    op.add_column('reviews', sa.Column('review_type', sa.String(20), nullable=True))
    op.add_column('reviews', sa.Column('review_date', sa.Date(), nullable=True))
    op.add_column('reviews', sa.Column('started_date', sa.Date(), nullable=True))
    op.add_column('reviews', sa.Column('finished_date', sa.Date(), nullable=True))
    op.add_column('reviews', sa.Column('like_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('reviews', sa.Column('comment_count', sa.Integer(), nullable=False, server_default='0'))
    op.alter_column('reviews', 'like_count', server_default=None)
    op.alter_column('reviews', 'comment_count', server_default=None)

    # Social tables
    op.create_table(
        'follows',
        sa.Column('follower_id', sa.Integer(), nullable=False),
        sa.Column('followee_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        # below, defines foreign key relationship between
        # "follows" & "users" tables
        # "Every 'follower_id' val in the 'follows' table must match
        # a valid 'id' in the 'users' table and if that user
        # is deleted, automatically delete all rows in 'follows'
        # that references it"
        sa.ForeignKeyConstraint(['follower_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['followee_id'], ['users.id'], ondelete='CASCADE'),
        # below, "each combo of 'user_id' & 'review_id' must be
        # unique and is used to uniquely identify a row in this 
        # table" -- the pair *together* form the primary key
        # ^^ oops, for next table. applies still.
        sa.PrimaryKeyConstraint('follower_id', 'followee_id'),
    )

    op.create_table(
        'likes',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('review_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['review_id'], ['reviews.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'review_id'),
    )

    op.create_table(
        'comments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('review_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['review_id'], ['reviews.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # indexes
    # below, telling Alembic (and therefore db):
    # "Create an index on the 'reviews' table that speeds up
    # queries filtering or sorting by 'visibility', then
    # by 'review_date', then by 'id'"
    # index reviews visability, date, id
    # filter for rows, look at their columns -- this speeds
    # up feed queries that filter by visibility and sort by
    # date/id . purely a performance booster
    op.create_index('idx_reviews_vis_date_id', 'reviews', ['visibility', 'review_date', 'id'])
    op.create_index('idx_likes_review', 'likes', ['review_id'])
    op.create_index('idx_comments_review_created', 'comments', ['review_id', 'created_at'])
    op.create_index('idx_follows_follower', 'follows', ['follower_id'])
    op.create_index('idx_follows_followee' 'follows', ['followee_id'])




def downgrade() -> None:
    """Downgrade schema."""
    # drop / delete indexes created earlier on the follows table
    # removes the performance indexes so that DB schemas can
    # roll back
    op.drop_index('idx_follows_followee', table_name='follows')
    op.drop_index('idx_follows_follower', table_name='follows')
    op.drop_index('idx_comments_review_created', table_name='comments')
    op.drop_index('idx_likes_review', table_name='likes')
    op.drop_index('idx_reviews_vis_date_id', table_name='reviews')

    # tables
    op.drop_table('comments')
    op.drop_table('likes')
    op.drop_table('follows')

    # ...and columns
    op.drop_column('reviews', 'comment_count')
    op.drop_column('reviews', 'like_count')
    op.drop_column('reviews', 'finished_date')
    op.drop_column('reviews', 'started_date')
    op.drop_column('reviews', 'review_date')
    op.drop_column('reviews', 'review_type')
    op.drop_column('reviews', 'visibility')
    op.drop_column('users', 'profile_visibility')
