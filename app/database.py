"""Database Configuration and Session Management"""
import os
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from dotenv import load_dotenv

load_dotenv()

# Create database engine
engine = create_engine(
    os.getenv("DATABASE_URL"), # os.environ.get("DATABASE_URL"),
    echo=False, #os.getenv("DEBUG", "False").lower() in ("true", "1", "t"),
    pool_pre_ping=True,  # Verify connections before using them
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for models
Base = declarative_base()


def get_db() -> Session:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def gen_uuid():
    """Generate a new UUID"""
    return str(uuid4())

