"""nullable revoked_at field on refresh_token

Revision ID: 1fa922d933ad
Revises: c2e87ff1cc2a
Create Date: 2025-12-22 18:57:49.825860

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1fa922d933ad"
down_revision: Union[str, Sequence[str], None] = "c2e87ff1cc2a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Safely alter the column to be nullable
    with op.batch_alter_table("refresh_tokens", schema=None) as batch_op:
        batch_op.alter_column(
            "revoked_at", existing_type=postgresql.TIMESTAMP(), nullable=True
        )


def downgrade() -> None:
    # 1. Revert the column to be not nullable
    with op.batch_alter_table("refresh_tokens", schema=None) as batch_op:
        batch_op.alter_column(
            "revoked_at", existing_type=postgresql.TIMESTAMP(), nullable=False
        )
