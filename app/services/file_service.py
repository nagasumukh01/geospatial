import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.db.models import FileRecord, FeatureMeasurement
from app.utils.file_validation import validate_uploaded_file, validate_file_size
from app.utils.archive_utils import safe_extract_zip
from app.services.geospatial_service import GeoSpatialService
from app.services.measurement_service import MeasurementService

def utc_now():
    return datetime.now(timezone.utc)

class FileService:
    @classmethod
    def upload_and_process_file(cls, file: UploadFile, db: Session) -> FileRecord:
        """
        Orchestrates file uploading, validation, extraction, geometry processing,
        measurement calculation, and database persistence.
        """
        start_time = utc_now()

        # 1. Validate extension & file type
        file_type = validate_uploaded_file(file)

        # 2. Create database record
        file_id = str(uuid.uuid4())
        file_dir = settings.UPLOAD_DIR / file_id
        file_dir.mkdir(parents=True, exist_ok=True)
        file_path = file_dir / file.filename

        file_record = FileRecord(
            id=file_id,
            filename=file.filename,
            file_type=file_type,
            file_path=str(file_path),
            status="PENDING",
            upload_timestamp=start_time,
            processing_start_time=start_time
        )
        db.add(file_record)
        db.commit()
        db.refresh(file_record)

        try:
            # 3. Save file to disk safely
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Validate size
            validate_file_size(file_path)

            file_record.status = "PROCESSING"
            db.commit()

            # 4. Handle ZIP vs KML extraction
            if file_type == "ZIP_SHAPEFILE":
                extract_dir = file_dir / "extracted"
                extract_dir.mkdir(parents=True, exist_ok=True)
                target_file_path = safe_extract_zip(file_path, extract_dir)
            else:
                target_file_path = file_path

            # 5. Read GeoPandas dataset
            gdf = GeoSpatialService.read_geospatial_dataset(target_file_path, file_type)

            # Detect CRS
            crs_str = gdf.crs.to_string() if gdf.crs else "EPSG:4326"
            file_record.crs = crs_str
            file_record.feature_count = len(gdf)

            # 6. Process each feature and calculate measurements
            success_count = 0
            failed_count = 0

            for idx, row in gdf.iterrows():
                geom = row.geometry
                geom_type = geom.geom_type if geom is not None else "Unknown"

                # Extract feature properties (exclude geometry column)
                props = {}
                for k, v in row.items():
                    if k != "geometry":
                        # Convert non-serializable types to str
                        if isinstance(v, (datetime, Path)):
                            props[k] = str(v)
                        elif hasattr(v, "item"):  # numpy scalar
                            props[k] = v.item()
                        else:
                            try:
                                props[k] = v
                            except Exception:
                                props[k] = str(v)

                # Measure feature
                m_type, val, unit, m_status, err_msg = MeasurementService.measure_geometry(geom, gdf.crs)

                if m_status == "SUCCESS":
                    success_count += 1
                else:
                    failed_count += 1

                measurement_rec = FeatureMeasurement(
                    file_id=file_id,
                    feature_id=int(idx),
                    geometry_type=geom_type,
                    measurement_type=m_type,
                    value=val,
                    unit=unit,
                    status=m_status,
                    error_message=err_msg,
                    properties=props
                )
                db.add(measurement_rec)

            # 7. Update overall file processing status
            completion_time = utc_now()
            duration = (completion_time - start_time).total_seconds()

            file_record.processing_completion_time = completion_time
            file_record.processing_duration = round(duration, 3)

            if file_record.feature_count == 0:
                file_record.status = "FAILED"
                file_record.error_message = "Dataset contains no features."
            elif failed_count == 0:
                file_record.status = "COMPLETED"
            elif success_count > 0:
                file_record.status = "PARTIAL_SUCCESS"
            else:
                file_record.status = "FAILED"
                file_record.error_message = "All feature measurements failed."

            db.commit()
            db.refresh(file_record)
            return file_record

        except HTTPException as he:
            # Domain / Validation Exception
            completion_time = utc_now()
            file_record.status = "FAILED"
            file_record.error_message = he.detail
            file_record.processing_completion_time = completion_time
            file_record.processing_duration = round((completion_time - start_time).total_seconds(), 3)
            db.commit()
            raise he
        except Exception as e:
            # Internal server / unexpected error
            logger.error(f"Failed processing file {file_id}: {e}", exc_info=True)
            completion_time = utc_now()
            file_record.status = "FAILED"
            file_record.error_message = f"Processing error: {str(e)}"
            file_record.processing_completion_time = completion_time
            file_record.processing_duration = round((completion_time - start_time).total_seconds(), 3)
            db.commit()
            raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")

    @staticmethod
    def get_file_record(file_id: str, db: Session) -> FileRecord:
        record = db.query(FileRecord).filter(FileRecord.id == file_id).first()
        if not record:
            raise HTTPException(status_code=404, detail=f"File record with ID '{file_id}' not found.")
        return record

    @staticmethod
    def get_file_measurements(file_id: str, db: Session) -> Dict[str, Any]:
        file_record = FileService.get_file_record(file_id, db)
        measurements = db.query(FeatureMeasurement).filter(FeatureMeasurement.file_id == file_id).order_by(FeatureMeasurement.feature_id).all()

        measurement_items = []
        for m in measurements:
            measurement_items.append({
                "feature_id": m.feature_id,
                "geometry_type": m.geometry_type,
                "measurement_type": m.measurement_type,
                "value": m.value,
                "unit": m.unit,
                "status": m.status,
                "error": m.error_message,
                "properties": m.properties
            })

        return {
            "file_id": file_record.id,
            "status": file_record.status,
            "measurements": measurement_items
        }
