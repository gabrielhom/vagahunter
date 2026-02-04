from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import schemas, database
from ..models import job as models
from ..services.scraper import JobScraper

router = APIRouter()

@router.post("/jobs/search", response_model=List[schemas.Job])
def search_jobs(query: str, db: Session = Depends(database.get_db)):
    # 1. Scrape new jobs
    scraper = JobScraper()
    found_jobs = scraper.search_jobs(query)
    
    saved_jobs = []
    for job_data in found_jobs:
        # 2. Check if exists
        existing = db.query(models.Job).filter(models.Job.url == job_data.url).first()
        if not existing:
            # 3. Save to DB
            db_job = models.Job(**job_data.dict())
            db.add(db_job)
            db.commit()
            db.refresh(db_job)
            saved_jobs.append(db_job)
        else:
            saved_jobs.append(existing)
            
    return saved_jobs

@router.get("/jobs", response_model=List[schemas.Job])
def list_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    jobs = db.query(models.Job).offset(skip).limit(limit).all()
    return jobs
