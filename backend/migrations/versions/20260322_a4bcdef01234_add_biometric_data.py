"""add biometric data

Revision ID: a4bcdef01234
Revises: f7cf729e6c17
Create Date: 2026-03-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a4bcdef01234'
down_revision = 'f7cf729e6c17'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'biometric_data',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('biometric_type', sa.String(length=50), nullable=False),
        sa.Column('finger_id', sa.Integer(), nullable=True),
        sa.Column('data', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_biometric_data_tenant_id'), 'biometric_data', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_biometric_data_user_id'), 'biometric_data', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_biometric_data_user_id'), table_name='biometric_data')
    op.drop_index(op.f('ix_biometric_data_tenant_id'), table_name='biometric_data')
    op.drop_table('biometric_data')
