from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
import sqlalchemy as sa
from sqlalchemy.orm import Session
from app.database import get_db
from app.security.access import login_required
from app.models.logging import GenerationLogs
from app.schemas import SalesOrderHdrCreate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sales_orders", tags=["sales_orders"])

@router.get("/")
@login_required
def get_sales_orders(request: Request, response: Response, db: Session = Depends(get_db)):
    """Get all sales orders"""
    logs = GenerationLogs.pull_so_logs(db)
    return {
        "message": "Sales orders retrieved successfully",
        "sales_orders": logs
    }

@router.post("/generate-hdr")
@login_required
def generate_sales_order_hdr(sales_order_data: SalesOrderHdrCreate, request: Request, response: Response, db: Session = Depends(get_db)):
    """Endpoint to trigger sales order header generation"""
    # customer_id, company_id, location_id, ship_to_id, taker, order_date
    customer_id = sales_order_data.customer_id
    company_id = sales_order_data.company_id
    ship_to_id = sales_order_data.ship_to_id
    location_id = sa.query(sa.text(f"SELECT location_id FROM p21s_locations WHERE company_id = {sales_order_data.company_id} LIMIT 1")).scalar()
    taker = get_random_taker() # This function should use the oe_hdr table.
    order_date = datetime.now()