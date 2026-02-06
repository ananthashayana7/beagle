"""Initial tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('user_id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('role', sa.String(50), nullable=False, default='analyst'),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    
    # Files table
    op.create_table(
        'files',
        sa.Column('file_id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('storage_path', sa.String(500), nullable=False),
        sa.Column('storage_bucket', sa.String(100), nullable=False),
        sa.Column('schema_info', postgresql.JSONB(), nullable=True),
        sa.Column('preview_data', postgresql.JSONB(), nullable=True),
        sa.Column('statistics', postgresql.JSONB(), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('column_count', sa.Integer(), nullable=True),
        sa.Column('processing_status', sa.String(50), default='pending'),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_file_user_created', 'files', ['user_id', 'created_at'])
    op.create_index('idx_file_expires', 'files', ['expires_at'])
    
    # Conversations table
    op.create_table(
        'conversations',
        sa.Column('conversation_id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('file_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('files.file_id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(255), default='New Conversation'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_archived', sa.Boolean(), default=False),
        sa.Column('is_pinned', sa.Boolean(), default=False),
        sa.Column('context_data', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_conv_user_archived', 'conversations', ['user_id', 'is_archived'])
    op.create_index('idx_conv_user_created', 'conversations', ['user_id', 'created_at'])
    
    # Messages table
    op.create_table(
        'messages',
        sa.Column('message_id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('conversations.conversation_id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('has_code', sa.Boolean(), default=False),
        sa.Column('has_visualization', sa.Boolean(), default=False),
        sa.Column('execution_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_msg_conv_created', 'messages', ['conversation_id', 'created_at'])
    
    # Executions table
    op.create_table(
        'executions',
        sa.Column('execution_id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('file_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('files.file_id', ondelete='SET NULL'), nullable=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('conversations.conversation_id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.Text(), nullable=False),
        sa.Column('language', sa.String(50), default='python'),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('result', postgresql.JSONB(), nullable=True),
        sa.Column('stdout', sa.Text(), nullable=True),
        sa.Column('stderr', sa.Text(), nullable=True),
        sa.Column('visualizations', postgresql.JSONB(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_exec_status', 'executions', ['status'])
    op.create_index('idx_exec_user', 'executions', ['user_id'])


def downgrade() -> None:
    op.drop_table('executions')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('files')
    op.drop_table('users')
