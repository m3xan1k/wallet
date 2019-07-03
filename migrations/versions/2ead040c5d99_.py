"""empty message

Revision ID: 2ead040c5d99
Revises: 
Create Date: 2019-07-02 16:13:06.379683

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2ead040c5d99'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('operations', sa.Column('is_income', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('operations', 'is_income')
    # ### end Alembic commands ###