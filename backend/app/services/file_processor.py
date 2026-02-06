"""
File Processor Service
Handle file uploads, parsing, and storage
"""

import io
import json
from typing import Any, Dict, Optional

import pandas as pd
import numpy as np

from app.config import settings


class FileProcessor:
    """Process and manage uploaded data files"""
    
    SUPPORTED_TYPES = {
        'csv': 'text/csv',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'xls': 'application/vnd.ms-excel',
        'json': 'application/json',
        'parquet': 'application/octet-stream'
    }
    
    async def process_file(
        self,
        content: bytes,
        filename: str,
        file_type: str
    ) -> Dict[str, Any]:
        """
        Process uploaded file and extract metadata.
        
        Returns:
            Dictionary containing schema, preview, and statistics
        """
        # Parse file into dataframe
        df = await self._parse_file(content, file_type)
        
        # Extract schema
        schema = {
            "columns": df.columns.tolist(),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "shape": list(df.shape)
        }
        
        # Generate preview (first 10 rows)
        preview_df = df.head(10)
        preview = {
            "rows": preview_df.to_dict(orient='records'),
            "sample_values": {
                col: df[col].dropna().head(5).tolist()
                for col in df.columns
            }
        }
        
        # Generate statistics
        statistics = await self._generate_statistics(df)
        
        return {
            "schema": schema,
            "preview": preview,
            "statistics": statistics,
            "row_count": len(df),
            "column_count": len(df.columns)
        }
    
    async def _parse_file(self, content: bytes, file_type: str) -> pd.DataFrame:
        """Parse file content into a pandas DataFrame"""
        file_buffer = io.BytesIO(content)
        
        if file_type == 'csv':
            # Try different encodings
            try:
                df = pd.read_csv(file_buffer, encoding='utf-8')
            except UnicodeDecodeError:
                file_buffer.seek(0)
                df = pd.read_csv(file_buffer, encoding='latin-1')
        
        elif file_type in ('xlsx', 'xls'):
            df = pd.read_excel(file_buffer)
        
        elif file_type == 'json':
            # Try regular JSON first, then JSON Lines
            try:
                file_buffer.seek(0)
                data = json.load(file_buffer)
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                elif isinstance(data, dict):
                    df = pd.DataFrame([data])
                else:
                    raise ValueError("Unsupported JSON structure")
            except json.JSONDecodeError:
                file_buffer.seek(0)
                df = pd.read_json(file_buffer, lines=True)
        
        elif file_type == 'parquet':
            df = pd.read_parquet(file_buffer)
        
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        return df
    
    async def _generate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate statistical summary for the dataframe"""
        stats = {}
        
        # Numeric statistics
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            numeric_stats = df[numeric_cols].describe().to_dict()
            # Convert numpy types to Python types
            stats["numeric"] = {
                col: {k: float(v) if pd.notna(v) else None for k, v in vals.items()}
                for col, vals in numeric_stats.items()
            }
        
        # Categorical statistics
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        if categorical_cols:
            stats["categorical"] = {}
            for col in categorical_cols[:10]:  # Limit to 10 columns
                value_counts = df[col].value_counts().head(10).to_dict()
                stats["categorical"][col] = {
                    str(k): int(v) for k, v in value_counts.items()
                }
        
        # Missing values
        missing = df.isnull().sum().to_dict()
        stats["missing"] = {k: int(v) for k, v in missing.items()}
        
        # Correlations (numeric only)
        if len(numeric_cols) >= 2:
            corr = df[numeric_cols].corr()
            stats["correlations"] = {
                col: {k: float(v) if pd.notna(v) else None for k, v in vals.items()}
                for col, vals in corr.to_dict().items()
            }
        
        # Data quality score
        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isnull().sum().sum()
        stats["quality_score"] = round((1 - missing_cells / total_cells) * 100, 2) if total_cells > 0 else 100.0
        
        return stats
    
    async def store_file(
        self,
        content: bytes,
        path: str,
        bucket: str
    ) -> str:
        """Store file in MinIO/S3 storage"""
        from minio import Minio
        from minio.error import S3Error
        
        client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        
        # Ensure bucket exists
        try:
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
        except S3Error as e:
            if "BucketAlreadyOwnedByYou" not in str(e):
                raise
        
        # Upload file
        file_buffer = io.BytesIO(content)
        client.put_object(
            bucket,
            path,
            file_buffer,
            length=len(content)
        )
        
        return path
    
    async def load_dataframe(
        self,
        path: str,
        bucket: str,
        file_type: str
    ) -> pd.DataFrame:
        """Load dataframe from storage"""
        from minio import Minio
        
        client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        
        # Download file
        response = client.get_object(bucket, path)
        content = response.read()
        response.close()
        response.release_conn()
        
        # Parse and return
        return await self._parse_file(content, file_type)
    
    async def delete_file(self, path: str, bucket: str) -> bool:
        """Delete file from storage"""
        from minio import Minio
        
        client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        
        try:
            client.remove_object(bucket, path)
            return True
        except Exception:
            return False
