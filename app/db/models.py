import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class FileRecord(Base):
    __tablename__ = "file_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_path = Column(String(512), nullable=False)
    status = Column(String(50), nullable=False, default="PENDING")
    crs = Column(String(100), nullable=True)
    feature_count = Column(Integer, default=0)
    upload_timestamp = Column(DateTime, default=utc_now)
    processing_start_time = Column(DateTime, nullable=True)
    processing_completion_time = Column(DateTime, nullable=True)
    processing_duration = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)

    measurements = relationship("FeatureMeasurement", back_populates="file_record", cascade="all, delete-orphan")

class FeatureMeasurement(Base):
    __tablename__ = "feature_measurements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(String(36), ForeignKey("file_records.id", ondelete="CASCADE"), nullable=False)
    feature_id = Column(Integer, nullable=False)
    geometry_type = Column(String(50), nullable=False)
    measurement_type = Column(String(50), nullable=False)  # "area", "length", "none"
    value = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)  # "square_meters", "meters", etc.
    status = Column(String(50), nullable=False, default="SUCCESS")  # "SUCCESS", "FAILED", "UNSUPPORTED"
    error_message = Column(Text, nullable=True)
    properties = Column(JSON, nullable=True)

    file_record = relationship("FileRecord", back_populates="measurements")
