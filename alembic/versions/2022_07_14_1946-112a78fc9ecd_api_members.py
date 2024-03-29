"""API members

Revision ID: 112a78fc9ecd
Revises: 5e46fb9b6bac
Create Date: 2022-07-14 19:46:31.262013

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "112a78fc9ecd"
down_revision = "5e46fb9b6bac"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "members",
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("key_salt", sa.String(), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("member_id"),
    )
    op.create_index(op.f("ix_members_member_id"), "members", ["member_id"], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_members_member_id"), table_name="members")
    op.drop_table("members")
    # ### end Alembic commands ###
