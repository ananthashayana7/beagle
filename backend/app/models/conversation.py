"""
Conversation and Message Models
Database models for chat conversations and messages
"""

import uuid
from datetime import datetime
from typing import Optional, List, Any

from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class Conversation(Base):
    """Conversation/chat session model"""
    
    __tablename__ = "conversations"
    
    # Primary key
    conversation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # Owner
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Associated file (optional)
    file_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("files.file_id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Conversation info
    title: Mapped[str] = mapped_column(String(255), default="New Conversation")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Context data (column info, statistics, etc.)
    context_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="conversations")
    file: Mapped[Optional["File"]] = relationship("File", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_conv_user_archived', 'user_id', 'is_archived'),
        Index('idx_conv_user_created', 'user_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Conversation {self.conversation_id[:8]}>"
    
    def to_dict(self, include_messages: bool = False):
        """Convert to dictionary"""
        result = {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "file_id": self.file_id,
            "title": self.title,
            "description": self.description,
            "is_archived": self.is_archived,
            "is_pinned": self.is_pinned,
            "context_data": self.context_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "message_count": len(self.messages) if self.messages else 0
        }
        
        if include_messages:
            result["messages"] = [msg.to_dict() for msg in self.messages]
        
        return result


class Message(Base):
    """Chat message model"""
    
    __tablename__ = "messages"
    
    # Primary key
    message_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # Parent conversation
    conversation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Message content
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Metadata (code blocks, chart configs, execution results, etc.)
    msg_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)
    
    # Execution tracking
    has_code: Mapped[bool] = mapped_column(Boolean, default=False)
    has_visualization: Mapped[bool] = mapped_column(Boolean, default=False)
    execution_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        nullable=True
    )
    
    # Token usage (for cost tracking)
    token_count: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )
    
    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_msg_conv_created', 'conversation_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Message {self.message_id[:8]} ({self.role})>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "metadata": self.msg_metadata,
            "has_code": self.has_code,
            "has_visualization": self.has_visualization,
            "execution_id": self.execution_id,
            "token_count": self.token_count,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# Import related models
from app.models.user import User
from app.models.file import File
