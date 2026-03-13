"""Data Routes (Placeholder for future dummy data endpoints)"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.security.access import admin_required, login_required

router = APIRouter(prefix="/api/data", tags=["data"])


@router.get("/")
@login_required
@admin_required
def get_data_info():
    """Get info about data generation endpoints"""
    return {
        "message": "Data generation endpoints coming soon",
        "version": "0.1.0"
    }
