import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

db_url = settings.database_url
connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

if db_url.startswith("sqlite:///"):
    db_path = db_url.replace("sqlite:///", "", 1)
    db_dir = os.path.dirname(db_path) or "."
    os.makedirs(db_dir, exist_ok=True)
    try:
        open(db_path, "a").close()
    except OSError as e:
        raise SystemExit(f"Database path is not writable: {db_path} ({e})")

engine = create_engine(db_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
