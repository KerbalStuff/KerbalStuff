"""Add background offset to mods

Revision ID: 3b5f1c92dda
Revises: 2182d60340d
Create Date: 2014-06-30 00:14:36.303925

"""

# revision identifiers, used by Alembic.
revision = '3b5f1c92dda'
down_revision = '2182d60340d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('mod', sa.Column('bgOffsetX', sa.Integer(), nullable=True))
    op.add_column('mod', sa.Column('bgOffsetY', sa.Integer(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('mod', 'bgOffsetY')
    op.drop_column('mod', 'bgOffsetX')
    ### end Alembic commands ###
