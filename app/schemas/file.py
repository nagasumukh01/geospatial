from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict

class FeatureMeasurementItem(BaseModel):
    feature_id: int
    geometry_type: str
    measurement_type: str
    value: Optional[float] = None
    unit: Optional[str] = None
    status: str = "SUCCESS"
    error: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class FileUploadResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    feature_count: int
    crs: Optional[str] = None
    status: str
    upload_timestamp: datetime
    processing_start_time: Optional[datetime] = None
    processing_completion_time: Optional[datetime] = None
    processing_duration: Optional[float] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class FileInfoResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    feature_count: int
    crs: Optional[str] = None
    status: str
    upload_timestamp: datetime
    processing_start_time: Optional[datetime] = None
    processing_completion_time: Optional[datetime] = None
    processing_duration: Optional[float] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class FileMeasurementsResponse(BaseModel):
    file_id: str
    status: str
    measurements: List[FeatureMeasurementItem]

    model_config = ConfigDict(from_attributes=True)

class ErrorResponse(BaseModel):
    detail: str
