"""add university courses

Revision ID: 3c69d8b16eb1
Revises: 8386fcc879ec
Create Date: 2025-12-24 13:47:51.556464

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = "3c69d8b16eb1"
down_revision: Union[str, Sequence[str], None] = "8386fcc879ec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Ensure the values match your Python Enum class exactly
course_year_enum = sa.Enum("YEAR_1", "YEAR_2", "YEAR_3", "YEAR_4", name="courseyear")


def upgrade() -> None:
    """Upgrade schema."""

    # This prevents the "type courseyear does not exist" error
    course_year_enum.create(op.get_bind())

    op.create_table(
        "university_courses",
        sa.Column("id", sqlmodel.AutoString(), nullable=False),
        sa.Column("name", sqlmodel.AutoString(), nullable=False),
        sa.Column("code", sqlmodel.AutoString(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    with op.batch_alter_table("university_courses", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_university_courses_code"), ["code"], unique=True
        )
        batch_op.create_index(
            batch_op.f("ix_university_courses_name"), ["name"], unique=True
        )

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("university_course_id", sqlmodel.AutoString(), nullable=True)
        )

        batch_op.add_column(sa.Column("course_year", course_year_enum, nullable=True))

        batch_op.create_index(
            batch_op.f("ix_users_course_year"), ["course_year"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_users_university_course_id"),
            ["university_course_id"],
            unique=False,
        )

        # Changed 'None' to 'fk_users_university_course_id'
        batch_op.create_foreign_key(
            "fk_users_university_course_id",
            "university_courses",
            ["university_course_id"],
            ["id"],
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_constraint("fk_users_university_course_id", type_="foreignkey")

        batch_op.drop_index(batch_op.f("ix_users_university_course_id"))
        batch_op.drop_index(batch_op.f("ix_users_course_year"))
        batch_op.drop_column("course_year")
        batch_op.drop_column("university_course_id")

    with op.batch_alter_table("university_courses", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_university_courses_code"))
        batch_op.drop_index(batch_op.f("ix_university_courses_name"))

    op.drop_table("university_courses")

    course_year_enum.drop(op.get_bind())
