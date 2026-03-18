from alembic import op
import sqlalchemy as sa


revision = '0001_create_orders'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('customer', sa.String(length=255), nullable=False),
        sa.Column('items', sa.JSON(), nullable=False),
        sa.Column('total', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='queued'),
        sa.Column('tries', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('orders')
