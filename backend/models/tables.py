from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    camera_id = Column(String, nullable=False)
    location = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    files = relationship("File", back_populates="session", cascade="all, delete-orphan")

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    best_frame_path = Column(String)
    file_type = Column(String, nullable=False)
    file_date = Column(Date)
    datetime_full = Column(DateTime)
    relative_path = Column(String)
    file_size_bytes = Column(Integer)
    duration_sec = Column(Float)
    status = Column(String, default="pending", index=True)

    animal_detected = Column(Boolean)
    detection_confidence = Column(Float)
    max_count = Column(Integer, default=0)

    species = Column(String)
    scientific_name = Column(String)
    species_confidence = Column(Float)
    species_source = Column(String)

    csv_result = Column(String, index=True)
    csv_count = Column(Integer)
    behaviour = Column(String, default="")
    needs_review = Column(Boolean, default=False)
    manually_verified = Column(Boolean, default=False)

    error_message = Column(String)
    processed_at = Column(DateTime)

    session = relationship("SessionModel", back_populates="files")
