import os
from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.core.config import settings

def validate_uploaded_file(file: UploadFile) -> str:
    """
    Validates file extension, non-empty content, and max size.
    Returns detected file type ("KML" or "ZIP_SHAPEFILE").
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing in upload.")

    ext = Path(file.filename).suffix.lower()

    if ext not in settings.ALLOWED_EXTENSIONS:
        allowed = ", ".join(settings.ALLOWED_EXTENSIONS)
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Only {allowed} files are accepted."
        )

    # Determine file type
    file_type = "KML" if ext == ".kml" else "ZIP_SHAPEFILE"

    return file_type

def validate_file_size(file_path: Path):
    """
    Validates that the file is not empty and does not exceed MAX_UPLOAD_SIZE_MB.
    """
    if not file_path.exists():
        raise HTTPException(status_code=400, detail="Uploaded file missing on server.")

    file_size_bytes = file_path.stat().st_size
    if file_size_bytes == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size_bytes > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )
