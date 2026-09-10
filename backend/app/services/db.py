import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load .env file before reading env vars
load_dotenv()

# SQLite by default for local dev (matches .env: DATABASE_URL=sqlite:///./flare.db)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./flare.db"
)

# SQLite needs check_same_thread=False because FastAPI uses multiple threads
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
