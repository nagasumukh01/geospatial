from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_db
from app.schemas.file import (
    FileUploadResponse,
    FileInfoResponse,
    FileMeasurementsResponse,
    ErrorResponse
)
from app.services.file_service import FileService

router = APIRouter(prefix="/files", tags=["Geospatial Files"])

@router.post(
    "/",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and process geospatial file",
    description="Accepts .kml files or .zip files containing a Shapefile (.shp, .dbf, .shx). Extracts features, detects CRS, performs coordinate transformations, and measures geometry area/length.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file, unsupported extension, missing shapefile components, or corrupted file."},
        500: {"model": ErrorResponse, "description": "Internal server processing failure."}
    }
)
def upload_file(
    file: UploadFile = File(..., description="Geospatial file (.kml or .zip shapefile)"),
    db: Session = Depends(get_db)
):
    return FileService.upload_and_process_file(file, db)

@router.get(
    "/{id}/",
    response_model=FileInfoResponse,
    summary="Get file information and status",
    description="Retrieves metadata, processing status, CRS, feature count, upload timestamp, and processing duration for a file by its ID.",
    responses={
        404: {"model": ErrorResponse, "description": "File record not found."}
    }
)
def get_file_info(
    id: str,
    db: Session = Depends(get_db)
):
    return FileService.get_file_record(id, db)

@router.get(
    "/{id}/measurements/",
    response_model=FileMeasurementsResponse,
    summary="Get measurements for file features",
    description="Returns geometric measurements (area for Polygons, length for LineStrings) and feature properties calculated for all valid features in the file.",
    responses={
        404: {"model": ErrorResponse, "description": "File record not found."}
    }
)
def get_file_measurements(
    id: str,
    db: Session = Depends(get_db)
):
    return FileService.get_file_measurements(id, db)
