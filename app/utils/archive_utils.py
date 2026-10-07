import os
import zipfile
from pathlib import Path
from typing import List, Tuple
from fastapi import HTTPException

# Required shapefile component extensions
REQUIRED_SHAPEFILE_EXTENSIONS = {".shp", ".shx", ".dbf"}

def safe_extract_zip(zip_path: Path, extract_to: Path) -> Path:
    """
    Safely extract a ZIP archive while preventing path traversal attacks (Zip Slip)
    and verifying Shapefile components.
    Returns the path to the main .shp file.
    """
    if not zipfile.is_zipfile(zip_path):
        raise HTTPException(status_code=400, detail="Corrupted or invalid ZIP file.")

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Check for path traversal attacks
        for member in zip_ref.namelist():
            # Resolve absolute path to prevent extraction outside extract_to
            target_path = (extract_to / member).resolve()
            if not str(target_path).startswith(str(extract_to.resolve())):
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsafe file path detected in ZIP archive: {member}"
                )

        zip_ref.extractall(extract_to)

    # Search for .shp file inside extracted directory (including subdirectories if zipped with folder)
    shp_files = list(extract_to.rglob("*.shp"))
    if not shp_files:
        raise HTTPException(
            status_code=400,
            detail="ZIP archive does not contain a Shapefile (.shp)."
        )

    # Prefer root .shp or first found
    shp_path = shp_files[0]
    shp_dir = shp_path.parent
    base_name = shp_path.stem

    # Check for mandatory companion files (.shx, .dbf)
    found_exts = {p.suffix.lower() for p in shp_dir.glob(f"{base_name}.*")}
    missing_exts = REQUIRED_SHAPEFILE_EXTENSIONS - found_exts

    if missing_exts:
        missing_str = ", ".join(sorted(missing_exts))
        raise HTTPException(
            status_code=400,
            detail=f"Missing required Shapefile components for '{base_name}': {missing_str}"
        )

    return shp_path
