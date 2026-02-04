from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class JobBase(BaseModel):
    title: str
    company: str
    url: str
    source: str
    is_remote: bool = True
    description: Optional[str] = None
    match_score: Optional[int] = None
    match_reason: Optional[str] = None

class JobCreate(JobBase):
    pass

class Job(JobBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
