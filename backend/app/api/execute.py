"""
Code Execution API Routes
Execute Python code in a sandboxed environment
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_session
from app.models.user import User
from app.models.file import File as FileModel, Execution
from app.schemas.file import ExecutionRequest, ExecutionResponse
from app.core.security import get_current_active_user
from app.core.sanitizer import sanitizer
from app.core.rate_limiter import limiter
from app.config import settings
from app.services.process_executor import ProcessExecutor
from app.services.docker_executor import DockerExecutor
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Select executor based on configuration
if settings.execution_mode.upper() == "DOCKER":
    try:
        import docker
        docker.from_env().ping()
        code_executor = DockerExecutor()
        logger.info("Using DockerExecutor for code execution")
    except Exception as e:
        logger.warning(f"Docker not available ({e}), falling back to ProcessExecutor")
        code_executor = ProcessExecutor()
else:
    code_executor = ProcessExecutor()
    logger.info("Using ProcessExecutor for code execution")


@router.post("/", response_model=ExecutionResponse)
@limiter.limit(settings.rate_limit_execute)
async def execute_code(
    request: Request,
    execution_request: ExecutionRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Execute Python code in a sandboxed environment.
    
    Security restrictions:
    - Only whitelisted imports allowed (pandas, numpy, scipy, etc.)
    - 30 second timeout
    - No file system access
    - No network access
    - No dangerous operations (eval, exec, os, subprocess, etc.)
    """
    # Sanitize code
    code = sanitizer.sanitize_code(execution_request.code)
    
    # Validate code safety
    is_valid, error_msg = code_executor.validate_code(code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Code validation failed: {error_msg}"
        )
    
    # Load dataframe if file_id provided
    dataframe = None
    if execution_request.file_id:
        result = await session.execute(
            select(FileModel)
            .where(FileModel.file_id == execution_request.file_id)
            .where(FileModel.user_id == current_user.user_id)
            .where(FileModel.is_deleted == False)
        )
        file_record = result.scalar_one_or_none()
        
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Load dataframe from storage
        from app.services.file_processor import FileProcessor
        file_processor = FileProcessor()
        dataframe = await file_processor.load_dataframe(
            path=file_record.storage_path,
            bucket=file_record.storage_bucket,
            file_type=file_record.file_type
        )
    
    # Create execution record
    execution = Execution(
        file_id=execution_request.file_id,
        conversation_id=execution_request.conversation_id,
        user_id=current_user.user_id,
        code=code,
        language="python",
        status="running",
        started_at=datetime.utcnow()
    )
    session.add(execution)
    await session.commit()
    await session.refresh(execution)
    
    # Execute code
    try:
        exec_result = await code_executor.execute(
            code=code,
            dataframe=dataframe,
            timeout=settings.code_execution_timeout
        )
        
        # Update execution record
        execution.status = "success" if exec_result["success"] else "failed"
        execution.result = exec_result.get("result")
        execution.stdout = exec_result.get("stdout")
        execution.stderr = exec_result.get("stderr")
        execution.visualizations = exec_result.get("visualizations")
        execution.execution_time_ms = exec_result.get("execution_time_ms")
        execution.completed_at = datetime.utcnow()
        
    except TimeoutError:
        execution.status = "timeout"
        execution.stderr = f"Execution timed out after {settings.code_execution_timeout} seconds"
        execution.completed_at = datetime.utcnow()
        
    except Exception as e:
        execution.status = "failed"
        execution.stderr = str(e)
        execution.completed_at = datetime.utcnow()
    
    await session.commit()
    await session.refresh(execution)
    
    return ExecutionResponse(
        execution_id=execution.execution_id,
        status=execution.status,
        result=execution.result,
        stdout=execution.stdout,
        stderr=execution.stderr,
        visualizations=execution.visualizations,
        execution_time_ms=execution.execution_time_ms
    )


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get execution result by ID."""
    result = await session.execute(
        select(Execution)
        .where(Execution.execution_id == execution_id)
        .where(Execution.user_id == current_user.user_id)
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )
    
    return ExecutionResponse(
        execution_id=execution.execution_id,
        status=execution.status,
        result=execution.result,
        stdout=execution.stdout,
        stderr=execution.stderr,
        visualizations=execution.visualizations,
        execution_time_ms=execution.execution_time_ms
    )


@router.post("/validate")
async def validate_code(
    execution_request: ExecutionRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Validate code without executing it.
    
    Returns validation result including:
    - Whether the code is safe to execute
    - Any detected security issues
    - Syntax errors
    """
    code = sanitizer.sanitize_code(execution_request.code)
    is_valid, error_msg = code_executor.validate_code(code)
    
    return {
        "valid": is_valid,
        "error": error_msg if not is_valid else None,
        "warnings": []  # Future: add warnings for potentially slow operations
    }
