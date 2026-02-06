"""
Visualization Service
Generate charts using Plotly
"""

from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np


class VisualizationService:
    """Generate interactive visualizations from data"""
    
    async def generate_chart(
        self,
        df: pd.DataFrame,
        chart_type: str,
        x_column: Optional[str] = None,
        y_column: Optional[str] = None,
        color_column: Optional[str] = None,
        title: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a Plotly chart configuration.
        
        Returns:
            Dictionary containing Plotly figure data and layout
        """
        import plotly.express as px
        import plotly.graph_objects as go
        
        config = config or {}
        
        # Set default title
        if not title:
            title = f"{chart_type.title()} Chart"
        
        # Generate chart based on type
        if chart_type == "bar":
            if not x_column or not y_column:
                raise ValueError("Bar chart requires x and y columns")
            
            fig = px.bar(
                df,
                x=x_column,
                y=y_column,
                color=color_column,
                title=title,
                template="plotly_dark"
            )
        
        elif chart_type == "line":
            if not x_column or not y_column:
                raise ValueError("Line chart requires x and y columns")
            
            fig = px.line(
                df,
                x=x_column,
                y=y_column,
                color=color_column,
                title=title,
                template="plotly_dark"
            )
        
        elif chart_type == "scatter":
            if not x_column or not y_column:
                raise ValueError("Scatter plot requires x and y columns")
            
            fig = px.scatter(
                df,
                x=x_column,
                y=y_column,
                color=color_column,
                title=title,
                template="plotly_dark"
            )
        
        elif chart_type == "pie":
            if not x_column:
                raise ValueError("Pie chart requires a column for values")
            
            # For pie, we need to aggregate
            values_col = y_column if y_column else df[x_column].value_counts().name
            if y_column:
                pie_data = df.groupby(x_column)[y_column].sum().reset_index()
            else:
                pie_data = df[x_column].value_counts().reset_index()
                pie_data.columns = [x_column, 'count']
                values_col = 'count'
            
            fig = px.pie(
                pie_data,
                names=x_column,
                values=values_col,
                title=title,
                template="plotly_dark"
            )
        
        elif chart_type == "histogram":
            if not x_column:
                raise ValueError("Histogram requires x column")
            
            fig = px.histogram(
                df,
                x=x_column,
                color=color_column,
                title=title,
                template="plotly_dark"
            )
        
        elif chart_type == "box":
            fig = px.box(
                df,
                x=x_column,
                y=y_column,
                color=color_column,
                title=title,
                template="plotly_dark"
            )
        
        elif chart_type == "heatmap":
            # Correlation heatmap
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if len(numeric_cols) < 2:
                raise ValueError("Heatmap requires at least 2 numeric columns")
            
            corr = df[numeric_cols].corr()
            
            fig = px.imshow(
                corr,
                text_auto=True,
                aspect="auto",
                title=title or "Correlation Heatmap",
                template="plotly_dark"
            )
        
        elif chart_type == "area":
            if not x_column or not y_column:
                raise ValueError("Area chart requires x and y columns")
            
            fig = px.area(
                df,
                x=x_column,
                y=y_column,
                color=color_column,
                title=title,
                template="plotly_dark"
            )
        
        elif chart_type == "violin":
            fig = px.violin(
                df,
                x=x_column,
                y=y_column,
                color=color_column,
                title=title,
                template="plotly_dark"
            )
        
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        
        # Customize layout
        fig.update_layout(
            font=dict(family="Inter, sans-serif", size=12),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=50, r=50, t=80, b=50),
            hovermode="closest"
        )
        
        # Convert to JSON-serializable format
        return fig.to_dict()
    
    async def recommend_charts(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Recommend appropriate visualizations based on data structure.
        
        Analyzes column types and relationships to suggest charts.
        """
        recommendations = []
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        
        # Single numeric column → Histogram
        for col in numeric_cols[:3]:
            recommendations.append({
                "type": "histogram",
                "config": {"x": col},
                "description": f"Distribution of {col}",
                "priority": "high"
            })
        
        # Two numeric columns → Scatter plot
        if len(numeric_cols) >= 2:
            recommendations.append({
                "type": "scatter",
                "config": {"x": numeric_cols[0], "y": numeric_cols[1]},
                "description": f"Relationship between {numeric_cols[0]} and {numeric_cols[1]}",
                "priority": "high"
            })
        
        # Categorical + Numeric → Bar chart
        if categorical_cols and numeric_cols:
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            
            # Only if not too many categories
            if df[cat_col].nunique() <= 20:
                recommendations.append({
                    "type": "bar",
                    "config": {"x": cat_col, "y": num_col},
                    "description": f"{num_col} by {cat_col}",
                    "priority": "high"
                })
                
                recommendations.append({
                    "type": "box",
                    "config": {"x": cat_col, "y": num_col},
                    "description": f"Distribution of {num_col} by {cat_col}",
                    "priority": "medium"
                })
        
        # Time series
        if datetime_cols and numeric_cols:
            recommendations.append({
                "type": "line",
                "config": {"x": datetime_cols[0], "y": numeric_cols[0]},
                "description": f"{numeric_cols[0]} over time",
                "priority": "high"
            })
        
        # Categorical distribution → Pie chart
        for cat_col in categorical_cols[:2]:
            if df[cat_col].nunique() <= 10:
                recommendations.append({
                    "type": "pie",
                    "config": {"x": cat_col},
                    "description": f"Distribution of {cat_col}",
                    "priority": "medium"
                })
        
        # Correlation heatmap
        if len(numeric_cols) >= 3:
            recommendations.append({
                "type": "heatmap",
                "config": {},
                "description": "Correlations between numeric variables",
                "priority": "medium"
            })
        
        return recommendations
