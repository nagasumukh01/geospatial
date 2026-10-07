from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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

# Custom exception handlers for uniform error format
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."}
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
