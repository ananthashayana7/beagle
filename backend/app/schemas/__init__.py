"""
Beagle Schemas Package
Export all Pydantic schemas
"""

from app.schemas.auth import (
    UserBase,
    UserCreate,
    UserLogin,
    UserUpdate,
    UserResponse,
    TokenResponse,
    TokenRefresh,
    PasswordChange
)

from app.schemas.chat import (
    MessageCreate,
    MessageResponse,
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationWithMessages,
    ConversationList,
    ChatStreamRequest,
    ChatStreamChunk
)

from app.schemas.file import (
    FileUploadResponse,
    FilePreview,
    FileStatistics,
    FileListItem,
    FileList,
    ExecutionRequest,
    ExecutionResponse,
    VisualizationRequest,
    VisualizationResponse
)

__all__ = [
    # Auth
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserResponse",
    "TokenResponse",
    "TokenRefresh",
    "PasswordChange",
    # Chat
    "MessageCreate",
    "MessageResponse",
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationResponse",
    "ConversationWithMessages",
    "ConversationList",
    "ChatStreamRequest",
    "ChatStreamChunk",
    # File
    "FileUploadResponse",
    "FilePreview",
    "FileStatistics",
    "FileListItem",
    "FileList",
    "ExecutionRequest",
    "ExecutionResponse",
    "VisualizationRequest",
    "VisualizationResponse"
]
