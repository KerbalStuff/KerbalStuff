"""add multigame tables

Revision ID: 4e0500347ce7
Revises: 29344aa34d9
Create Date: 2016-03-30 12:26:36.632566

"""

# revision identifiers, used by Alembic.
revision = '4e0500347ce7'
down_revision = '29344aa34d9'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'publisher',
        sa.Column('id', sa.Integer, primary_key=True,autoincrement=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.Unicode(200)),
    )
    op.create_table(
        'game',
        sa.Column('id', sa.Integer, primary_key=True,autoincrement=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.Unicode(200)),
        sa.Column('theme', sa.Integer, nullable=True),
        sa.Column('publisher', sa.Integer, nullable=False),
    )
    op.create_table(
        'theme',
        sa.Column('id', sa.Integer, primary_key=True,autoincrement=True),
        sa.Column('name', sa.String(50), nullable=False),
	 sa.Column('css', sa.String(50), nullable=False),
        sa.Column('description', sa.Unicode(200)),
    )
    op.add_column('gameversion', sa.Column('game', sa.Integer, nullable=False))
    op.add_column('mod', sa.Column('game', sa.Integer, nullable=False))


def downgrade():
    op.drop_table('publisher')
    op.drop_table('game')
    op.drop_table('theme')
    op.drop_column('gameversion', 'game')
    op.drop_column('mod', 'game')

