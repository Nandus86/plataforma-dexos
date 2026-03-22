"""add RA to biometric data

Revision ID: b5cdef012345
Revises: a4bcdef01234
Create Date: 2026-03-22 01:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b5cdef012345'
down_revision = 'a4bcdef01234'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('biometric_data', sa.Column('registration_number', sa.String(length=50), nullable=True))


def downgrade():
    op.drop_column('biometric_data', 'registration_number')
