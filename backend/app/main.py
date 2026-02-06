"""
Beagle - Enterprise Data Intelligence Platform
Main FastAPI Application
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import init_db, close_db
from app.core.rate_limiter import limiter, rate_limit_exceeded_handler

# Import API routers
from app.api import auth, files, chat, execute, visualize


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info(f"Starting Beagle API v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Beagle API")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Enterprise AI-Powered Data Analysis Platform",
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan
)

# Add rate limiter to app state
app.state.limiter = limiter

# Add rate limit exceeded handler
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next: Callable):
    """Log all requests with timing"""
    start_time = time.time()
    
    # Generate request ID
    request_id = f"{time.time():.0f}"
    
    try:
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log request
        logger.info(
            f"{request.method} {request.url.path} "
            f"status={response.status_code} "
            f"duration={duration:.3f}s "
            f"client={request.client.host if request.client else 'unknown'}"
        )
        
        # Add timing header
        response.headers["X-Process-Time"] = f"{duration:.3f}"
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"{request.method} {request.url.path} "
            f"error={str(e)} "
            f"duration={duration:.3f}s"
        )
        raise


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.exception(f"Unhandled exception: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred" if not settings.debug else str(exc)
            }
        }
    )


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }


@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """Detailed health check with dependency status"""
    from sqlalchemy import text
    from app.database import async_session_maker
    import redis.asyncio as redis
    
    checks = {
        "api": True,
        "database": False,
        "redis": False
    }
    
    # Check database
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
            checks["database"] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    # Check Redis
    try:
        r = redis.from_url(settings.redis_url)
        await r.ping()
        await r.close()
        checks["redis"] = True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
    
    all_healthy = all(checks.values())
    
    return JSONResponse(
        status_code=200 if all_healthy else 503,
        content={
            "status": "healthy" if all_healthy else "unhealthy",
            "checks": checks,
            "version": settings.app_version,
            "environment": settings.environment
        }
    )


# Prometheus metrics
if settings.environment != "test":
    Instrumentator().instrument(app).expose(app)


# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(files.router, prefix="/api/files", tags=["Files"])
app.include_router(chat.router, prefix="/api/conversations", tags=["Conversations"])
app.include_router(execute.router, prefix="/api/execute", tags=["Execution"])
app.include_router(visualize.router, prefix="/api/visualizations", tags=["Visualizations"])


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """API root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "Enterprise AI-Powered Data Analysis Platform",
        "docs": "/docs" if settings.debug else None
    }
