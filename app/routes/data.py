"""Data Routes (Placeholder for future dummy data endpoints)"""
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.security.access import login_required

router = APIRouter(prefix="/api/data", tags=["data"])


@router.get("/")
@login_required
def get_data_info(request: Request, response: Response):
    """Get info about data generation endpoints"""
    return {
        "message": "Data generation endpoints coming soon",
        "version": "0.1.0"
    }

@router.get("/sales-orders")
@login_required
def get_sales_orders(request: Request, response: Response):
    """Get info about sales orders data generation endpoint"""
    return {
        "message": "Sales orders data generation endpoint coming soon",
        "version": "0.1.0"
    }

@router.get("/purchase-orders")
@login_required
def get_purchase_orders(request: Request, response: Response):
    """Get info about purchase orders data generation endpoint"""
    return {
        "message": "Purchase orders data generation endpoint coming soon",
        "version": "0.1.0"
    }

@router.post("/generate-sales-orders")
@login_required
def generate_sales_orders(request: Request, response: Response):
    """Generate sales orders data"""
    return {
        "message": "Sales orders data generation endpoint coming soon",
        "version": "0.1.0"
    }

@router.post("/generate-purchase-orders")
@login_required
def generate_purchase_orders(request: Request, response: Response):
    """Generate purchase orders data"""
    return {
        "message": "Purchase orders data generation endpoint coming soon",
        "version": "0.1.0"
    }

@router.get("/generated-data-history")
@login_required
def get_generated_data_history(request: Request, response: Response, db: Session = Depends(get_db)):
    """Get history of generated data"""
    return {
        "message": "Generated data history endpoint coming soon",
        "version": "0.1.0"
    }