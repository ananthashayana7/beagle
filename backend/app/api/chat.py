"""
Conversations/Chat API Routes
Manage conversations and send messages with AI analysis
"""

import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.models.file import File as FileModel
from app.schemas.chat import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationWithMessages,
    ConversationList,
    MessageCreate,
    MessageResponse
)
from app.core.security import get_current_active_user
from app.core.sanitizer import sanitizer
from app.core.rate_limiter import limiter
from app.config import settings
from app.services.ai_service import AIService


router = APIRouter()
ai_service = AIService()


@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Create a new conversation."""
    # Verify file exists if provided
    context_data = None
    if conversation_data.file_id:
        result = await session.execute(
            select(FileModel)
            .where(FileModel.file_id == conversation_data.file_id)
            .where(FileModel.user_id == current_user.user_id)
            .where(FileModel.is_deleted == False)
        )
        file_record = result.scalar_one_or_none()
        
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Build context from file schema
        context_data = {
            "file_id": file_record.file_id,
            "filename": file_record.original_filename,
            "columns": file_record.schema_info.get("columns", []) if file_record.schema_info else [],
            "dtypes": file_record.schema_info.get("dtypes", {}) if file_record.schema_info else {},
            "row_count": file_record.row_count,
            "column_count": file_record.column_count
        }
    
    # Create conversation
    conversation = Conversation(
        user_id=current_user.user_id,
        file_id=conversation_data.file_id,
        title=sanitizer.sanitize_text(conversation_data.title) if conversation_data.title else "New Conversation",
        description=sanitizer.sanitize_text(conversation_data.description) if conversation_data.description else None,
        context_data=context_data
    )
    
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    
    return ConversationResponse(
        conversation_id=conversation.conversation_id,
        user_id=conversation.user_id,
        file_id=conversation.file_id,
        title=conversation.title,
        description=conversation.description,
        is_archived=conversation.is_archived,
        is_pinned=conversation.is_pinned,
        context_data=conversation.context_data,
        message_count=0,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )


@router.get("/", response_model=ConversationList)
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_archived: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """List all conversations for the current user."""
    # Build query
    query = select(Conversation).where(Conversation.user_id == current_user.user_id)
    count_query = select(func.count(Conversation.conversation_id)).where(
        Conversation.user_id == current_user.user_id
    )
    
    if not include_archived:
        query = query.where(Conversation.is_archived == False)
        count_query = count_query.where(Conversation.is_archived == False)
    
    # Count total
    count_result = await session.execute(count_query)
    total = count_result.scalar()
    
    # Get conversations
    offset = (page - 1) * page_size
    result = await session.execute(
        query
        .options(selectinload(Conversation.messages))
        .order_by(Conversation.is_pinned.desc(), Conversation.updated_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    conversations = result.scalars().all()
    
    return ConversationList(
        items=[
            ConversationResponse(
                conversation_id=c.conversation_id,
                user_id=c.user_id,
                file_id=c.file_id,
                title=c.title,
                description=c.description,
                is_archived=c.is_archived,
                is_pinned=c.is_pinned,
                context_data=c.context_data,
                message_count=len(c.messages),
                created_at=c.created_at,
                updated_at=c.updated_at
            )
            for c in conversations
        ],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get a conversation with all messages."""
    result = await session.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.conversation_id == conversation_id)
        .where(Conversation.user_id == current_user.user_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return ConversationWithMessages(
        conversation_id=conversation.conversation_id,
        user_id=conversation.user_id,
        file_id=conversation.file_id,
        title=conversation.title,
        description=conversation.description,
        is_archived=conversation.is_archived,
        is_pinned=conversation.is_pinned,
        context_data=conversation.context_data,
        message_count=len(conversation.messages),
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[
            MessageResponse(
                message_id=m.message_id,
                conversation_id=m.conversation_id,
                role=m.role,
                content=m.content,
                metadata=m.metadata,
                has_code=m.has_code,
                has_visualization=m.has_visualization,
                execution_id=m.execution_id,
                token_count=m.token_count,
                created_at=m.created_at
            )
            for m in conversation.messages
        ]
    )


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    update_data: ConversationUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Update a conversation."""
    result = await session.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.conversation_id == conversation_id)
        .where(Conversation.user_id == current_user.user_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    if update_data.title is not None:
        conversation.title = sanitizer.sanitize_text(update_data.title)
    if update_data.description is not None:
        conversation.description = sanitizer.sanitize_text(update_data.description)
    if update_data.is_archived is not None:
        conversation.is_archived = update_data.is_archived
    if update_data.is_pinned is not None:
        conversation.is_pinned = update_data.is_pinned
    
    await session.commit()
    await session.refresh(conversation)
    
    return ConversationResponse(
        conversation_id=conversation.conversation_id,
        user_id=conversation.user_id,
        file_id=conversation.file_id,
        title=conversation.title,
        description=conversation.description,
        is_archived=conversation.is_archived,
        is_pinned=conversation.is_pinned,
        context_data=conversation.context_data,
        message_count=len(conversation.messages),
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Delete a conversation."""
    result = await session.execute(
        select(Conversation)
        .where(Conversation.conversation_id == conversation_id)
        .where(Conversation.user_id == current_user.user_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    await session.delete(conversation)
    await session.commit()
    
    return {"success": True, "message": "Conversation deleted"}


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
@limiter.limit(settings.rate_limit_chat)
async def send_message(
    request: Request,
    conversation_id: str,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Send a message and get AI response.
    
    This endpoint sends a user message to the conversation and returns
    the AI assistant's response.
    """
    # Get conversation
    result = await session.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.conversation_id == conversation_id)
        .where(Conversation.user_id == current_user.user_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Sanitize content
    content = sanitizer.sanitize_text(message_data.content)
    
    # Create user message
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=content,
        metadata=message_data.metadata
    )
    session.add(user_message)
    
    # Build message history for AI
    history = [
        {"role": m.role, "content": m.content}
        for m in conversation.messages[-10:]  # Last 10 messages for context
    ]
    history.append({"role": "user", "content": content})
    
    # Get AI response
    try:
        ai_response = await ai_service.generate_response(
            messages=history,
            context=conversation.context_data
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {str(e)}"
        )
    
    # Create assistant message
    assistant_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=ai_response.get("content", ""),
        metadata=ai_response.get("metadata"),
        has_code=ai_response.get("has_code", False),
        has_visualization=ai_response.get("has_visualization", False),
        token_count=ai_response.get("token_count")
    )
    session.add(assistant_message)
    
    await session.commit()
    await session.refresh(assistant_message)
    
    return MessageResponse(
        message_id=assistant_message.message_id,
        conversation_id=assistant_message.conversation_id,
        role=assistant_message.role,
        content=assistant_message.content,
        metadata=assistant_message.metadata,
        has_code=assistant_message.has_code,
        has_visualization=assistant_message.has_visualization,
        execution_id=assistant_message.execution_id,
        token_count=assistant_message.token_count,
        created_at=assistant_message.created_at
    )


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get messages for a conversation."""
    # Verify conversation ownership
    conv_result = await session.execute(
        select(Conversation.conversation_id)
        .where(Conversation.conversation_id == conversation_id)
        .where(Conversation.user_id == current_user.user_id)
    )
    if not conv_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Get messages
    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .offset(offset)
        .limit(limit)
    )
    messages = result.scalars().all()
    
    return [
        MessageResponse(
            message_id=m.message_id,
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            metadata=m.metadata,
            has_code=m.has_code,
            has_visualization=m.has_visualization,
            execution_id=m.execution_id,
            token_count=m.token_count,
            created_at=m.created_at
        )
        for m in messages
    ]
