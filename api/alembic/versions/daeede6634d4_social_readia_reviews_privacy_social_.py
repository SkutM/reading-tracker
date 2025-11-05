"""social readia: reviews privacy, social tables, dates, counts

Revision ID: daeede6634d4
Revises: f217a5cb3762
Create Date: 2025-11-04 18:07:03.391751

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
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
