from datetime import datetime
import logging
import random
import csv
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
import sqlalchemy as sa
from sqlalchemy.orm import Session
from app.database import get_db
from app.security.access import login_required
from app.models.logging import GenerationLogs
from app.schemas import SalesOrderCreate

from app.helper.sales_order_helper import get_client_main_location, get_random_items, get_random_taker, generate_order_no, get_ship_to_name, HDR_DEFAULT_STRUCTURE, LINE_DEFAULT_STRUCTURE
from app.helper.file_helper import generate_tsv_file

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
async def generate_sales_order_hdr(sales_order_data: SalesOrderCreate, request: Request, response: Response, db: Session = Depends(get_db)):
    """Endpoint to trigger sales order header generation"""
    # customer_id, company_id, location_id, ship_to_id, taker, order_date

    # Pull Customer ID, Company ID AND ship_to_id from the request body
    # Generate the Location ID, taker from the database based on p21s_location table and p21s_oe_hdr table.
    client_id = sales_order_data.client_id
    customer_id = sales_order_data.customer_id
    customer_name = sales_order_data.customer_name
    company_id = sales_order_data.company_id
    ship_to_id = sales_order_data.ship_to_id if sales_order_data.ship_to_id else customer_id
    for i in range(sales_order_data.sales_order_count):
        number_of_items = random.randint(sales_order_data.lower_item_count, sales_order_data.upper_item_count)  # For example, you can make this dynamic based on your needs

        location_id = get_client_main_location(client_id, db)
        taker = get_random_taker(client_id, db)
        items = get_random_items(client_id, number_of_items, db)
        import_set_no = i + 1 # This should increment if we generate more than one sales order

        # Generate a unique order number starting in 98*****
        order_no = generate_order_no()

        contact_id = items[0]["contact_id"] if items else None  # Assuming contact_id can be derived from the first item
        contact_name = items[0]["contact_name"] if items else None  # Assuming contact_name can be derived from the first item
        ship_to_name = get_ship_to_name(ship_to_id, client_id, db) if ship_to_id else None

        header_data = HDR_DEFAULT_STRUCTURE.copy()
        header_data.update({
            # Required header columns
            "import_set_no": import_set_no,
            "customer_id": customer_id,
            "customer_name": customer_name,
            "company_id": company_id,
            "location_id": location_id,  # Sales Location ID
            "contact_id": contact_id,
            "contact_name": contact_name,
            "taker": taker,
            "ship_to_id": ship_to_id,
            "ship_to_name": ship_to_name,
            "packing_basis": "partial",
            "quote": 'N',

            # Additional non-required but useful fields
            "customer_po_no": f"PO{order_no}",
        })

        line_no = 1
        items_list = []
        for item in items:
            line_data = LINE_DEFAULT_STRUCTURE.copy()
            line_data.update({
                "import_set_no": import_set_no,
                "line_no": line_no,
                "item_id": item["item_id"],
                "unit_quantity": random.randint(1, int(item["qty_available"])),  # Random quantity up to available stock
                "unit_of_measure": item["base_unit"],
                "capture_usage": 'Y'
            })
            line_no += 1
            items_list.append(line_data)

        # Generate TSV files for header (SOH) and lines (SOL)
        generate_tsv_file([header_data], db, "SOH")
        generate_tsv_file(items_list, db, "SOL")
