"""
File Management API Routes
Upload, download, preview, and manage data files
"""

import uuid
import io
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_session
from app.models.user import User
from app.models.file import File as FileModel
from app.schemas.file import (
    FileUploadResponse,
    FilePreview,
    FileStatistics,
    FileList,
    FileListItem
)
from app.core.security import get_current_active_user
from app.core.sanitizer import sanitizer
from app.core.rate_limiter import limiter
from app.config import settings
from app.services.file_processor import FileProcessor


router = APIRouter()
file_processor = FileProcessor()


@router.post("/upload", response_model=FileUploadResponse)
@limiter.limit(settings.rate_limit_upload)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Upload a data file for analysis.
    
    Supported formats: CSV, Excel (.xlsx, .xls), JSON, Parquet
    
    Maximum file size: 500 MB
    """
    # Validate filename
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )
    
    if not sanitizer.validate_filename(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename"
        )
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower().lstrip('.')
    if file_ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Supported: {', '.join(settings.allowed_extensions)}"
        )
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Check file size
    max_size = settings.max_file_size_mb * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb} MB"
        )
    
    # Process file
    try:
        file_data = await file_processor.process_file(
            content=content,
            filename=file.filename,
            file_type=file_ext
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process file: {str(e)}"
        )
    
    # Generate unique filename for storage
    storage_filename = f"{uuid.uuid4()}.{file_ext}"
    
    # Create file record
    file_record = FileModel(
        user_id=current_user.user_id,
        filename=storage_filename,
        original_filename=file.filename,
        file_type=file_ext,
        mime_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        storage_path=f"files/{current_user.user_id}/{storage_filename}",
        storage_bucket=settings.minio_bucket,
        schema_info=file_data.get("schema"),
        preview_data=file_data.get("preview"),
        statistics=file_data.get("statistics"),
        row_count=file_data.get("row_count"),
        column_count=file_data.get("column_count"),
        processing_status="completed"
    )
    
    session.add(file_record)
    await session.commit()
    await session.refresh(file_record)
    
    # Store file in MinIO (async task in production)
    try:
        await file_processor.store_file(
            content=content,
            path=file_record.storage_path,
            bucket=file_record.storage_bucket
        )
    except Exception as e:
        # Update status to failed
        file_record.processing_status = "failed"
        file_record.processing_error = str(e)
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store file"
        )
    
    return FileUploadResponse(
        file_id=file_record.file_id,
        filename=file_record.filename,
        original_filename=file_record.original_filename,
        file_type=file_record.file_type,
        file_size=file_record.file_size,
        file_size_mb=round(file_record.file_size / (1024 * 1024), 2),
        row_count=file_record.row_count,
        column_count=file_record.column_count,
        columns=file_data.get("schema", {}).get("columns", []),
        dtypes=file_data.get("schema", {}).get("dtypes", {}),
        processing_status=file_record.processing_status,
        created_at=file_record.created_at
    )


@router.get("/", response_model=FileList)
async def list_files(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """List all files for the current user."""
    # Count total
    count_result = await session.execute(
        select(func.count(FileModel.file_id))
        .where(FileModel.user_id == current_user.user_id)
        .where(FileModel.is_deleted == False)
    )
    total = count_result.scalar()
    
    # Get files
    offset = (page - 1) * page_size
    result = await session.execute(
        select(FileModel)
        .where(FileModel.user_id == current_user.user_id)
        .where(FileModel.is_deleted == False)
        .order_by(FileModel.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    files = result.scalars().all()
    
    return FileList(
        items=[
            FileListItem(
                file_id=f.file_id,
                original_filename=f.original_filename,
                file_type=f.file_type,
                file_size_mb=round(f.file_size / (1024 * 1024), 2),
                row_count=f.row_count,
                column_count=f.column_count,
                processing_status=f.processing_status,
                created_at=f.created_at
            )
            for f in files
        ],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{file_id}", response_model=FileUploadResponse)
async def get_file(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get file metadata by ID."""
    result = await session.execute(
        select(FileModel)
        .where(FileModel.file_id == file_id)
        .where(FileModel.user_id == current_user.user_id)
        .where(FileModel.is_deleted == False)
    )
    file_record = result.scalar_one_or_none()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    schema = file_record.schema_info or {}
    
    return FileUploadResponse(
        file_id=file_record.file_id,
        filename=file_record.filename,
        original_filename=file_record.original_filename,
        file_type=file_record.file_type,
        file_size=file_record.file_size,
        file_size_mb=round(file_record.file_size / (1024 * 1024), 2),
        row_count=file_record.row_count,
        column_count=file_record.column_count,
        columns=schema.get("columns", []),
        dtypes=schema.get("dtypes", {}),
        processing_status=file_record.processing_status,
        created_at=file_record.created_at
    )


@router.get("/{file_id}/preview", response_model=FilePreview)
async def get_file_preview(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get preview data for a file (first 10 rows)."""
    result = await session.execute(
        select(FileModel)
        .where(FileModel.file_id == file_id)
        .where(FileModel.user_id == current_user.user_id)
        .where(FileModel.is_deleted == False)
    )
    file_record = result.scalar_one_or_none()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    schema = file_record.schema_info or {}
    preview = file_record.preview_data or {}
    
    return FilePreview(
        file_id=file_record.file_id,
        filename=file_record.original_filename,
        columns=schema.get("columns", []),
        dtypes=schema.get("dtypes", {}),
        row_count=file_record.row_count or 0,
        column_count=file_record.column_count or 0,
        preview_rows=preview.get("rows", []),
        sample_values=preview.get("sample_values", {})
    )


@router.get("/{file_id}/statistics", response_model=FileStatistics)
async def get_file_statistics(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get statistical summary for a file."""
    result = await session.execute(
        select(FileModel)
        .where(FileModel.file_id == file_id)
        .where(FileModel.user_id == current_user.user_id)
        .where(FileModel.is_deleted == False)
    )
    file_record = result.scalar_one_or_none()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    stats = file_record.statistics or {}
    
    return FileStatistics(
        file_id=file_record.file_id,
        filename=file_record.original_filename,
        numeric_stats=stats.get("numeric"),
        categorical_stats=stats.get("categorical"),
        missing_values=stats.get("missing"),
        correlations=stats.get("correlations"),
        data_quality_score=stats.get("quality_score")
    )


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Delete a file (soft delete)."""
    result = await session.execute(
        select(FileModel)
        .where(FileModel.file_id == file_id)
        .where(FileModel.user_id == current_user.user_id)
        .where(FileModel.is_deleted == False)
    )
    file_record = result.scalar_one_or_none()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Soft delete
    file_record.is_deleted = True
    await session.commit()
    
    return {"success": True, "message": "File deleted"}
