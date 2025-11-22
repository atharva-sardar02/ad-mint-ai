"""
Add llm_conversation_history column to generations table

This migration adds a JSON column to store the complete LLM conversation history
for Master Mode generations, allowing users to view all agent interactions later.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = 'add_conversation_history'
down_revision = None  # Update this with your latest migration revision
branch_labels = None
depends_on = None


def upgrade():
    # Add llm_conversation_history column to generations table
    op.add_column(
        'generations',
        sa.Column('llm_conversation_history', sa.JSON(), nullable=True)
    )
    print("✅ Added llm_conversation_history column to generations table")


def downgrade():
    # Remove llm_conversation_history column
    op.drop_column('generations', 'llm_conversation_history')
    print("✅ Removed llm_conversation_history column from generations table")

