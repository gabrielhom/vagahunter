from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from urllib.parse import urlparse

class JobBase(BaseModel):
    title: str
    company: str
    url: str
    source: str
    is_remote: bool = True
    description: Optional[str] = None
    match_score: Optional[int] = None
    match_reason: Optional[str] = None

    @field_validator("title", "company")
    @classmethod
    def _strip_and_limit(cls, v: str) -> str:
        text = (v or "").strip()
        return text[:200] or "N/A"

    @field_validator("url")
    @classmethod
    def _validate_url(cls, v: str) -> str:
        url = (v or "").strip()
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("URL inválida")
        return url

    @field_validator("description")
    @classmethod
    def _limit_description(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return str(v)[:5000]

class JobCreate(JobBase):
    pass

class Job(JobBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
