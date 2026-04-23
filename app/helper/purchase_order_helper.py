from app.helper.client_db_helper import get_client_db_connection
from fastapi import Depends, Request
import sqlalchemy as sa
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.logging import GenerationLogs
from app.schemas import PurchaseOrderCreate
import app.scripts.data_queries as queries
from datetime import datetime

import logging
logger = logging.getLogger(__name__)

def generate_po_no() -> str:
    """Generate a random purchase order number beginning with 99"""
    import random
    return f"99{random.randint(10000, 99999)}"


def build_purchase_order_payload(order_data: PurchaseOrderCreate, user_id: str, db: Session = Depends(get_db)) -> list[dict]:
    """Build supplier-grouped purchase order payload with header and organized lines.

    Returns a list of dictionaries where each entry contains a `header` object
    (matching PURCHASE_ORDER_HDR shape) and an `organized_items` list containing
    PURCHASE_ORDER_LINE objects for the supplier.

    :param order_data: PurchaseOrderCreate object containing the input data for PO generation
    :param user_id: ID of the user generating the purchase orders, for logging purposes
    :param db: Database session for logging generation results
    :return: List of dictionaries with `header` and `lines` for each supplier
    """
    supplier_data = format_items(order_data.items)
    successful_count = 0
    failed_count = 0
    final_generated_ids = []


    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    purchase_orders: list[dict] = []

    for idx, supplier_group in enumerate(supplier_data["suppliers"], start=1):
        try:
            header = PURCHASE_ORDER_HDR.copy()
            header.update({
                "import_set_no": idx,
                "company_id": order_data.company_id,
                "location_id": order_data.location_id,
                "vendor_id": supplier_group.get("supplier_id", ""),
                "supplier_id": supplier_group.get("supplier_id", ""),
                "division_id": "",
                "buyer_id": supplier_group.get("buyer_id", ""),
                "purchase_order_type": order_data.purchase_order_type or "S",
                "po_date": today,
                "required_date": today,
                "approved": "Y",
                "current_timestamp": today,
                "external_po_num": generate_po_no(),
                "packing_basis": "partial",
            })

            lines = []
            for line_no, item in enumerate(supplier_group["items"].values(), start=1):
                line = PURCHASE_ORDER_LINE.copy()
                line.update({
                    "import_set_no": idx,
                    "line_no": line_no,
                    "item_id": item.get("item_id", ""),
                    "item_uom": item.get("uom", ""),
                    "item_qty": item.get("used_quantity", ""),
                    "pricing_uom": item.get("uom", ""),
                })
                lines.append(line)
                final_generated_ids.append(f"POH_{idx}_{item.get('item_id', '')}")
                final_generated_ids.append(f"POL_{idx}_{item.get('item_id', '')}")

            purchase_orders.append({
                "import_set_no": idx,
                "header": header,
                "lines": lines,
            })
            successful_count += 1
        except Exception as e:
            logger.error(f"Error building purchase order for supplier {supplier_group.get('supplier_id', 'Unknown')}: {e}", exc_info=True)
            failed_count += 1

    GenerationLogs.log_po_generation(db, order_data.client_id, user_id, True, successful_count=successful_count, failed_count=failed_count, successful_generated_ids=final_generated_ids)

    return purchase_orders

def format_items(items: list[dict]) -> dict:
    """
    Format input items into supplier-grouped structure for purchase order generation.
    
    :param items: List of item dictionaries containing purchase order data
    :return: Dictionary with suppliers as keys and their corresponding items as values
    """
    suppliers_map = {}

    for row in items:
        supplier_id = int(row['supplier_id'])
        supplier_name = row['supplier_name']

        # Initialize supplier bucket if not exists
        if supplier_id not in suppliers_map:
            suppliers_map[supplier_id] = {
                "supplier_id": supplier_id,
                "supplier_name": supplier_name,
                "buyer_id": row["buyer_id"],
                "buyer_name": row["buyer_name"],
                "items": {}
            }

        if row["inv_mast_uid"] in suppliers_map[supplier_id]["items"]:
            # If item already exists for this supplier, aggregate quantity
            existing_item = suppliers_map[supplier_id]["items"][row["inv_mast_uid"]]
            existing_item["used_quantity"] += int(row["used_quantity"])
        
        else:
            # Build item record
            item = {
                "item_id": row["item_id"],
                "item_desc": row["item_desc"],
                "used_quantity": int(row["used_quantity"]),
                "uom": row["base_unit"],
            }

            suppliers_map[supplier_id]["items"][row["inv_mast_uid"]] = item

    return {"suppliers": list(suppliers_map.values())}

PURCHASE_ORDER_HDR = {
    "import_set_no": "",
    "company_id": "",
    "location_id": "",
    "vendor_id": "",
    "supplier_id": "",
    "division_id": "",
    "buyer_id": "",
    "filler1": "",
    "purchase_order_type": "",
    "po_date": "",
    "required_date": "",
    "approved": "",
    "filler2": "",
    "filler3": "",
    "filler4": "",
    "current_timestamp": "",
    "filler5": "",
    "filler6": "",
    "filler7": "",
    "filler8": "",
    "filler9": "",
    "external_po_num": "",
    "filler10": "N",
    "filler11": "",
    "filler12": "",
    "filler13": "N",
    "filler14": "N",
    "filler15": "",
    "filler16": "",
    "filler17": "",
    "filler18": "",
    "filler19": "",
    "filler20": "",
    "filler21": "",
    "filler22": "",
    "packing_basis": "",
}

PURCHASE_ORDER_LINE = {
    "import_set_no": "",
    "line_no": "",
    "item_id": "",
    "item_uom": "",
    "item_qty": "",
    "pricing_uom": "",
    "filler1": "0",
    "filler2": "",
    "filler3": "",
    "filler4": "",
    "filler5": "",
}

