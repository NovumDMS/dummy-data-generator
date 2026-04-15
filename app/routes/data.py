"""Data Routes"""
from datetime import datetime
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.helper.client_db_helper import get_client_db_connection
from app.models.client import Clients
from app.security.access import login_required
from app.schemas import SalesOrderCreate, PurchaseOrderCreate
from app.helper.file_helper import zip_orders
from app.scripts.sales_order import generate_sales_orders
from app.scripts.purchase_order import generate_purchase_orders

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/data", tags=["data"])


@router.post("/generate")
@login_required
async def generate(order_data: SalesOrderCreate, request: Request, response: Response, db: Session = Depends(get_db)):
    """Generate sales and purchase orders and return them as a downloadable zip"""
    logger.info(f"Beginning order generation for client_id={order_data.client_id}, customer_id={order_data.customer_id}")
    client_name = db.query(Clients).filter(Clients.id == order_data.client_id).first().client_name  # Validate client exists
    sales_order_items = generate_sales_orders(order_data, db, user_id=request.state.user.id, username=request.state.user.username)

    logger.info(f"Sales order generated with {len(sales_order_items)} items. Building purchase order payload.")
    # po_data = PurchaseOrderCreate(
    #     client_id=order_data.client_id,
    #     customer_id=order_data.customer_id,
    #     customer_name=order_data.customer_name,
    #     company_id=order_data.company_id,
    #     ship_to_id=order_data.ship_to_id,
    #     location_id=order_data.location_id,
    #     item_data={"items": sales_order_items},
    # )
    # generate_purchase_orders(po_data, db)

    logger.info("Purchase order generation complete. Preparing zip file for download.")
    project_root = Path(__file__).resolve().parents[2]
    tsv_dir = project_root / "tsv_files"
    output_zip = tsv_dir / f"{order_data.client_id}_orders.zip"
    zip_orders(tsv_dir, output_zip)

    logger.info(f"Zip file created at {output_zip}. Outputting via FileResponse.")
    return FileResponse(
        path=str(output_zip),
        media_type="application/zip",
        filename=f"{client_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_dummy_orders.zip",
    )