"""PricePeek FastAPI Application Entrypoint."""
import time
from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.config.database import engine, get_db, init_db
from app.api.v1.router import api_v1_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context: initialize database schema on startup."""
    try:
        init_db()
    except Exception as e:
        print(f"Warning: Database initialization exception: {e}")
    yield


app = FastAPI(
    title="PricePeek API",
    description=(
        "Universal Product Price Comparison Platform Backend API. "
        "Provides real-time cross-store price comparison, dynamic platform registry, "
        "and intelligent product matching with strict unit and variant separation."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 router
app.include_router(api_v1_router)


@app.get("/", tags=["System"])
def root() -> Dict[str, Any]:
    """Root entrypoint returning basic service descriptor."""
    return {
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "status": "operational",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "api_v1": "/api/v1"
    }


@app.get("/health", tags=["System"])
def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Health check endpoint verifying database connectivity and runtime status."""
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"unhealthy: {str(exc)}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "database": {
            "status": db_status,
            "engine": engine.dialect.name
        },
        "timestamp": time.time()
    }
