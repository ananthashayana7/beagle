"""
File Schemas
Pydantic models for file uploads and data
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class FileUploadResponse(BaseModel):
    """Response after file upload"""
    file_id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    file_size_mb: float
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    columns: Optional[List[str]] = None
    dtypes: Optional[Dict[str, str]] = None
    processing_status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class FilePreview(BaseModel):
    """File data preview"""
    file_id: str
    filename: str
    columns: List[str]
    dtypes: Dict[str, str]
    row_count: int
    column_count: int
    preview_rows: List[Dict[str, Any]]  # First 10 rows
    sample_values: Dict[str, List[Any]]  # Sample values per column


class FileStatistics(BaseModel):
    """Statistical summary of file data"""
    file_id: str
    filename: str
    numeric_stats: Optional[Dict[str, Dict[str, float]]] = None  # describe() output
    categorical_stats: Optional[Dict[str, Dict[str, int]]] = None  # value counts
    missing_values: Optional[Dict[str, int]] = None
    correlations: Optional[Dict[str, Dict[str, float]]] = None
    data_quality_score: Optional[float] = None


class FileListItem(BaseModel):
    """File list item"""
    file_id: str
    original_filename: str
    file_type: str
    file_size_mb: float
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    processing_status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class FileList(BaseModel):
    """Paginated file list"""
    items: List[FileListItem]
    total: int
    page: int
    page_size: int


class ExecutionRequest(BaseModel):
    """Code execution request"""
    code: str = Field(..., min_length=1, max_length=100000)
    file_id: Optional[str] = None
    conversation_id: Optional[str] = None


class ExecutionResponse(BaseModel):
    """Code execution response"""
    execution_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    visualizations: Optional[List[Dict[str, Any]]] = None
    execution_time_ms: Optional[int] = None
    
    class Config:
        from_attributes = True


class VisualizationRequest(BaseModel):
    """Visualization generation request"""
    file_id: str
    chart_type: str  # bar, line, scatter, pie, heatmap, box, histogram
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    color_column: Optional[str] = None
    title: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class VisualizationResponse(BaseModel):
    """Visualization response"""
    viz_id: str
    chart_type: str
    config: Dict[str, Any]
    data: Dict[str, Any]  # Plotly figure data
    image_url: Optional[str] = None
