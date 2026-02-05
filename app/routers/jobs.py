import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List
from .. import schemas, database
from ..models import job as models
from ..services.scraper import JobScraper
from ..services.ai_analyzer import analyze_job

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/jobs/search", response_model=List[schemas.Job])
async def search_jobs(query: str, db: Session = Depends(database.get_db)):
    query = (query or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    scraper = JobScraper()
    try:
        found_jobs = await scraper.search_jobs(query)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Scraper error: {e}")

    if not found_jobs:
        return []

    urls = [job.url for job in found_jobs]
    existing_jobs = db.query(models.Job).filter(models.Job.url.in_(urls)).all()
    existing_map = {job.url: job for job in existing_jobs}
    saved_jobs = list(existing_map.values())
    new_jobs = [job_data for job_data in found_jobs if job_data.url not in existing_map]

    semaphore = asyncio.Semaphore(3)

    async def _score_job(job_data: schemas.JobCreate):
        if not job_data.description:
            job_data.match_score = 0
            job_data.match_reason = "Descrição ausente"
            return
        async with semaphore:
            try:
                analysis = await asyncio.to_thread(analyze_job, job_data.description, query)
            except Exception as e:
                logger.exception("AI scoring failed for %s: %s", job_data.url, e)
                job_data.match_score = 0
                job_data.match_reason = "AI Error"
                return
        job_data.match_score = int(analysis.get("score", 0))
        job_data.match_reason = (analysis.get("reason", "N/A") or "N/A")[:400]

    await asyncio.gather(*(_score_job(job_data) for job_data in new_jobs))

    if new_jobs:
        db_jobs = [models.Job(**job_data.dict()) for job_data in new_jobs]
        db.add_all(db_jobs)
        try:
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Database is not writable") from e
        for db_job in db_jobs:
            db.refresh(db_job)
        saved_jobs.extend(db_jobs)

    return saved_jobs

@router.get("/jobs", response_model=List[schemas.Job])
def list_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    jobs = db.query(models.Job).offset(skip).limit(limit).all()
    return jobs
