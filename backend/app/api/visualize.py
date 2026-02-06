"""
Visualization API Routes
Generate charts and visualizations from data
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_session
from app.models.user import User
from app.models.file import File as FileModel
from app.schemas.file import VisualizationRequest, VisualizationResponse
from app.core.security import get_current_active_user
from app.config import settings
from app.services.visualization_service import VisualizationService


router = APIRouter()
viz_service = VisualizationService()


@router.post("/generate", response_model=VisualizationResponse)
async def generate_visualization(
    viz_request: VisualizationRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Generate a visualization from file data.
    
    Supported chart types:
    - bar: Bar chart
    - line: Line chart
    - scatter: Scatter plot
    - pie: Pie chart
    - histogram: Histogram
    - box: Box plot
    - heatmap: Correlation heatmap
    """
    # Get file
    result = await session.execute(
        select(FileModel)
        .where(FileModel.file_id == viz_request.file_id)
        .where(FileModel.user_id == current_user.user_id)
        .where(FileModel.is_deleted == False)
    )
    file_record = result.scalar_one_or_none()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Validate chart type
    valid_types = ["bar", "line", "scatter", "pie", "histogram", "box", "heatmap", "area", "violin"]
    if viz_request.chart_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid chart type. Supported: {', '.join(valid_types)}"
        )
    
    # Load dataframe
    from app.services.file_processor import FileProcessor
    file_processor = FileProcessor()
    
    try:
        df = await file_processor.load_dataframe(
            path=file_record.storage_path,
            bucket=file_record.storage_bucket,
            file_type=file_record.file_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load data: {str(e)}"
        )
    
    # Validate columns exist
    columns = df.columns.tolist()
    if viz_request.x_column and viz_request.x_column not in columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Column '{viz_request.x_column}' not found in data"
        )
    if viz_request.y_column and viz_request.y_column not in columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Column '{viz_request.y_column}' not found in data"
        )
    if viz_request.color_column and viz_request.color_column not in columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Column '{viz_request.color_column}' not found in data"
        )
    
    # Generate visualization
    try:
        viz_data = await viz_service.generate_chart(
            df=df,
            chart_type=viz_request.chart_type,
            x_column=viz_request.x_column,
            y_column=viz_request.y_column,
            color_column=viz_request.color_column,
            title=viz_request.title,
            config=viz_request.config
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate visualization: {str(e)}"
        )
    
    return VisualizationResponse(
        viz_id=str(uuid.uuid4()),
        chart_type=viz_request.chart_type,
        config={
            "x_column": viz_request.x_column,
            "y_column": viz_request.y_column,
            "color_column": viz_request.color_column,
            "title": viz_request.title
        },
        data=viz_data
    )


@router.get("/suggest/{file_id}")
async def suggest_visualizations(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get visualization suggestions based on data structure.
    
    Analyzes the data types and relationships to recommend
    appropriate chart types.
    """
    # Get file
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
    
    # Load dataframe
    from app.services.file_processor import FileProcessor
    file_processor = FileProcessor()
    
    try:
        df = await file_processor.load_dataframe(
            path=file_record.storage_path,
            bucket=file_record.storage_bucket,
            file_type=file_record.file_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load data: {str(e)}"
        )
    
    # Get suggestions
    suggestions = await viz_service.recommend_charts(df)
    
    return {
        "success": True,
        "data": {
            "suggestions": suggestions,
            "columns": df.columns.tolist(),
            "dtypes": df.dtypes.astype(str).to_dict()
        }
    }


@router.get("/types")
async def get_chart_types():
    """Get list of available chart types with descriptions."""
    return {
        "chart_types": [
            {
                "type": "bar",
                "name": "Bar Chart",
                "description": "Compare values across categories",
                "requires": {"x": True, "y": True}
            },
            {
                "type": "line",
                "name": "Line Chart",
                "description": "Show trends over time or continuous data",
                "requires": {"x": True, "y": True}
            },
            {
                "type": "scatter",
                "name": "Scatter Plot",
                "description": "Show relationship between two numeric variables",
                "requires": {"x": True, "y": True}
            },
            {
                "type": "pie",
                "name": "Pie Chart",
                "description": "Show proportion of categories",
                "requires": {"x": True, "y": False}
            },
            {
                "type": "histogram",
                "name": "Histogram",
                "description": "Show distribution of a numeric variable",
                "requires": {"x": True, "y": False}
            },
            {
                "type": "box",
                "name": "Box Plot",
                "description": "Show distribution and outliers",
                "requires": {"x": False, "y": True}
            },
            {
                "type": "heatmap",
                "name": "Heatmap",
                "description": "Show correlations between numeric variables",
                "requires": {"x": False, "y": False}
            },
            {
                "type": "area",
                "name": "Area Chart",
                "description": "Show cumulative values over time",
                "requires": {"x": True, "y": True}
            },
            {
                "type": "violin",
                "name": "Violin Plot",
                "description": "Show distribution shape and statistics",
                "requires": {"x": False, "y": True}
            }
        ]
    }
