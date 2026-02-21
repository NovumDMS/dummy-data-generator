"""Data Routes (Placeholder for future dummy data endpoints)"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(prefix="/api/data", tags=["data"])


@router.get("/")
def get_data_info():
    """Get info about data generation endpoints"""
    return {
        "message": "Data generation endpoints coming soon",
        "version": "0.1.0"
    }
