"""
File Model
Database model for uploaded files and their metadata
"""

import uuid
from datetime import datetime
from typing import Optional, List, Any

from sqlalchemy import String, BigInteger, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class File(Base):
    """Uploaded file model"""
    
    __tablename__ = "files"
    
    # Primary key
    file_id: Mapped[str] = mapped_column(
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
    
    # File info
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # csv, xlsx, json, etc.
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)  # bytes
    
    # Storage
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_bucket: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Data schema (columns, dtypes, etc.)
    schema_info: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Preview data (first 10 rows)
    preview_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Statistics
    statistics: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    row_count: Mapped[Optional[int]] = mapped_column(nullable=True)
    column_count: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    # Processing status
    processing_status: Mapped[str] = mapped_column(
        String(50),
        default="pending"
    )  # pending, processing, completed, failed
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    
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
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="files")
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation",
        back_populates="file"
    )
    executions: Mapped[List["Execution"]] = relationship(
        "Execution",
        back_populates="file",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_file_user_created', 'user_id', 'created_at'),
        Index('idx_file_expires', 'expires_at'),
    )
    
    def __repr__(self):
        return f"<File {self.original_filename}>"
    
    def to_dict(self, include_preview: bool = False, include_stats: bool = False):
        """Convert to dictionary"""
        result = {
            "file_id": self.file_id,
            "user_id": self.user_id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_type": self.file_type,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "file_size_mb": round(self.file_size / (1024 * 1024), 2),
            "schema_info": self.schema_info,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "processing_status": self.processing_status,
            "processing_error": self.processing_error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_preview:
            result["preview_data"] = self.preview_data
        
        if include_stats:
            result["statistics"] = self.statistics
        
        return result


class Execution(Base):
    """Code execution history model"""
    
    __tablename__ = "executions"
    
    # Primary key
    execution_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # Associated file
    file_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("files.file_id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Associated conversation
    conversation_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("conversations.conversation_id", ondelete="SET NULL"),
        nullable=True
    )
    
    # User who ran it
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Code
    code: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(50), default="python")
    
    # Results
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending"
    )  # pending, running, success, failed, timeout
    result: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    stdout: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stderr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Visualizations generated
    visualizations: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Performance
    execution_time_ms: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    
    # Relationships
    file: Mapped[Optional["File"]] = relationship("File", back_populates="executions")
    
    # Indexes
    __table_args__ = (
        Index('idx_exec_status', 'status'),
        Index('idx_exec_user', 'user_id'),
    )
    
    def __repr__(self):
        return f"<Execution {self.execution_id[:8]} ({self.status})>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "execution_id": self.execution_id,
            "file_id": self.file_id,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "code": self.code,
            "language": self.language,
            "status": self.status,
            "result": self.result,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "visualizations": self.visualizations,
            "execution_time_ms": self.execution_time_ms,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# Import related models
from app.models.user import User
from app.models.conversation import Conversation
