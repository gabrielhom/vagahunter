from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from ..database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    company = Column(String)
    url = Column(String, unique=True)
    source = Column(String)
    is_remote = Column(Boolean, default=True)
    description = Column(String, nullable=True)
    match_score = Column(Integer, nullable=True)
    match_reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
