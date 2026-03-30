from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
import sqlalchemy as sa
from sqlalchemy.orm import Session
from app.database import get_db
from app.security.access import login_required
from app.models.logging import GenerationLogs
from app.schemas import SalesOrderHdrCreate

from app.helper.sales_order_helper import get_client_main_location, get_random_taker, generate_order_no

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

@router.post("/generate")
@login_required
async def generate_sales_order_hdr(sales_order_data: SalesOrderHdrCreate, request: Request, response: Response, db: Session = Depends(get_db)):
    """Endpoint to trigger sales order header generation"""
    # customer_id, company_id, location_id, ship_to_id, taker, order_date
    client_id = sales_order_data.client_id
    order_no = generate_order_no()

    data = {
        "customer_id": sales_order_data.customer_id,
        "company_id": sales_order_data.company_id,
        "location_id": get_client_main_location(client_id, db),
        "ship_to_id": sales_order_data.ship_to_id if sales_order_data.ship_to_id else sales_order_data.customer_id,
        "taker": get_random_taker(client_id, db),
        "order_date": datetime.now(),
        "order_no": order_no,
        "po_no": f"Dummy Data {order_no}"
    }

    await insert_hdr(data)

async def insert_hdr(data):
    """Insert a new record into the sales order header table"""
    # This function should use the client database connection to insert a new record into the appropriate table.
    pass