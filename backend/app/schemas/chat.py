"""
Chat Schemas
Pydantic models for conversations and messages
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """Create a new message"""
    content: str = Field(..., min_length=1, max_length=50000)
    metadata: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    """Message response"""
    message_id: str
    conversation_id: str
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    has_code: bool = False
    has_visualization: bool = False
    execution_id: Optional[str] = None
    token_count: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    """Create a new conversation"""
    title: Optional[str] = "New Conversation"
    file_id: Optional[str] = None
    description: Optional[str] = None


class ConversationUpdate(BaseModel):
    """Update conversation"""
    title: Optional[str] = None
    description: Optional[str] = None
    is_archived: Optional[bool] = None
    is_pinned: Optional[bool] = None


class ConversationResponse(BaseModel):
    """Conversation response"""
    conversation_id: str
    user_id: str
    file_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    is_archived: bool = False
    is_pinned: bool = False
    context_data: Optional[Dict[str, Any]] = None
    message_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConversationWithMessages(ConversationResponse):
    """Conversation with all messages"""
    messages: List[MessageResponse] = []


class ConversationList(BaseModel):
    """List of conversations"""
    items: List[ConversationResponse]
    total: int
    page: int
    page_size: int


class ChatStreamRequest(BaseModel):
    """Request for streaming chat"""
    message: str = Field(..., min_length=1, max_length=50000)
    conversation_id: Optional[str] = None
    file_id: Optional[str] = None


class ChatStreamChunk(BaseModel):
    """Streaming chat response chunk"""
    type: str  # 'text', 'code', 'visualization', 'done', 'error'
    content: str
    metadata: Optional[Dict[str, Any]] = None
