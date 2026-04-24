"""Data Routes"""
from datetime import datetime
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.helper.client_db_helper import get_client_db_connection
from app.helper.sales_order_helper import get_client_main_location
from app.models.client import Clients
from app.models.logging import GenerationLogs
from app.security.access import login_required
from app.schemas import SalesOrderCreate, PurchaseOrderCreate
from app.helper.file_helper import generate_master_order_files, zip_orders
from app.scripts.sales_order import generate_sales_orders
from app.scripts.purchase_order import generate_purchase_orders

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/data", tags=["data"])


@router.post("/generate")
@login_required
async def generate(order_data: SalesOrderCreate, request: Request, response: Response, db: Session = Depends(get_db)):
    """Generate sales and purchase orders and return them as a downloadable zip"""
    user_id = request.state.user.id

    logger.info(f"Beginning order generation for client_id={order_data.client_id}, customer_id={order_data.customer_id}")
    client_name = db.query(Clients).filter(Clients.id == order_data.client_id).first().client_name.replace(" ", "")  # Validate client exists and remove spaces
    sales_order_items = generate_sales_orders(order_data, db, user_id=user_id, username=request.state.user.username)

    po_data = PurchaseOrderCreate(
        client_id=order_data.client_id,
        company_id=order_data.company_id,
        location_id=get_client_main_location(order_data.client_id, db),
        items=sales_order_items,
    )
    generate_purchase_orders(po_data, user_id=user_id, db=db)

    logger.info("Purchase order generation complete. Preparing zip file for download.")
    project_root = Path(__file__).resolve().parents[2]
    tsv_dir = project_root / "tsv_files"
    generate_master_order_files(tsv_dir)
    output_zip = tsv_dir / f"{order_data.client_id}_orders.zip"
    zip_orders(tsv_dir, output_zip)

    logger.info(f"Zip file created at {output_zip}. Outputting via FileResponse.")
    return FileResponse(
        path=str(output_zip),
        media_type="application/zip",
        filename=f"{client_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_dummy_orders.zip",
    )

@router.get("/validation_items")
@login_required
async def get_logged_orders() -> dict:
    sales_orders = GenerationLogs.pull_so_logs()
    purchase_orders = GenerationLogs.pull_po_logs()
    return {
        "sales_orders": sales_orders,
        "purchase_orders": purchase_orders
    }

@router.post("/validate")
@login_required
async def validate_orders(client_id: str, order_nums: list[str | int], file_type: str, db: Session = Depends(get_db)) -> bool:
    """Placeholder for order validation logic"""
    # The main idea is that this should pull in a list of custom PO/SO numbers
    # And then should use the P21 API to check against P21 ensuring that they have been properly uploaded.
    

    file_type = file_type.capitalize
    if file_type == "PO":
        
        return True
    elif file_type == "SO":
        
        return True
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No files of type {file_type}"
        )