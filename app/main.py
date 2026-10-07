from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.db.database import engine, Base
from app.api.routes.files import router as files_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: setup logging & initialize database tables
    setup_logging()
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    # Automatic SQLite schema migration for missing columns
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            columns = [c['name'] for c in inspector.get_columns('feature_measurements')]
            if 'geometry_geojson' not in columns:
                logger.info("Migrating database: Adding 'geometry_geojson' column to feature_measurements table...")
                conn.execute(text("ALTER TABLE feature_measurements ADD COLUMN geometry_geojson JSON"))
                conn.commit()
    except Exception as e:
        logger.warning(f"Schema check error: {e}")

    logger.info("Application startup complete.")
    yield
    # Shutdown
    logger.info("Application shutdown.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Production-ready RESTful API for measuring geospatial file features (.kml and Shapefile .zip) with automated CRS transformations.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handler for unhandled non-HTTP exceptions
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None)
        )
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"An internal server error occurred: {str(exc)}"}
    )

# Mount static files and sample datasets
static_dir = Path(__file__).parent / "static"
sample_data_dir = Path(__file__).parent.parent / "sample_data"

if sample_data_dir.exists():
    app.mount("/sample_data", StaticFiles(directory=sample_data_dir), name="sample_data")

# Include API routes
app.include_router(files_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Web Interface"])
def serve_web_interface():
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {
        "title": settings.PROJECT_NAME,
        "status": "online",
        "documentation": "/docs"
    }

@app.get("/health", tags=["Health Check"])
def health_check():
    return {"status": "healthy"}
