"""Add dark_theme entry

Revision ID: 3b85eb7c4d7
Revises: 3d4136d1ae1
Create Date: 2015-08-06 03:34:32.888608

"""

# revision identifiers, used by Alembic.
revision = '3b85eb7c4d7'
down_revision = '3d4136d1ae1'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', Column('dark_theme', sa.Boolean, server_default=False, nullable=false))
    pass


def downgrade():
    with op.batch_alter_table("user") as batch_op:
        batch_op.drop_column('dark_theme')
    pass
