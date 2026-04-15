import logging
import csv
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
import sqlalchemy as sa
from sqlalchemy.orm import Session
from app.database import get_db
from app.security.access import login_required
from app.models.logging import GenerationLogs
from app.schemas import PurchaseOrderCreate

from app.helper.file_helper import generate_tsv_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sales_orders", tags=["sales_orders"])

@router.post("/generate", status_code=status.HTTP_201_CREATED)
@login_required
def generate_purchase_order(purchase_order_data: PurchaseOrderCreate, request: Request, response: Response, db: Session = Depends(get_db)):
    """Endpoint to trigger purchase order header generation"""
    # company_id, location_id, vendor_id, supplier_id, division_id, buyer_id, purchase_order_type, po_date, required_date, approved

    # Pull company_id, location_id, vendor_id, supplier_id, division_id, buyer_id, purchase_order_type, po_date, required_date and approved from the request body
    # Generate the import_set_no and po_no for the purchase order header.
    # For the line details, generate random item details such as item_id (you can pull random item_ids from the database based on the client), item_uom, item_qty and pricing_uom.
    # Generate a TSV file for the purchase order header and line details using the `generate_tsv_file` function.

    return {
        "message": "Purchase order generated successfully",
        "purchase_order": {
            "company_id": purchase_order_data.company_id,
            "location_id": purchase_order_data.location_id
        }
    }