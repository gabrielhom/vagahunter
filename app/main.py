from fastapi import FastAPI
from .database import engine, Base
from .routers import jobs
from .config import settings

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
)

app.include_router(jobs.router, tags=["jobs"])

@app.get("/")
def read_root():
    return {"message": "Welcome to VagaHunter API! Go to /docs for Swagger UI."}
