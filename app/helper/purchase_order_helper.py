from app.helper.client_db_helper import get_client_db_connection
from fastapi import Depends
import sqlalchemy as sa
from sqlalchemy.orm import Session
from app.database import get_db
import app.scripts.data_queries as queries
from datetime import datetime

def generate_po_no():
    """Generate a random purchase order number"""
    import random
    return f"99{random.randint(10000, 99999)}"

def organize_item_lists(items: list[dict]) -> list[dict]:
    """Aggregate sales order lines by item_id and return PO line dictionaries.

    Duplicate item_ids are merged by summing their quantities. The resulting
    list is formatted to match PURCHASE_ORDER_LINE, ready for TSV generation.
    """
    aggregated: dict[str, dict] = {}
    for item in items:
        item_id = item["item_id"]
        if item_id in aggregated:
            aggregated[item_id]["item_qty"] += item["unit_quantity"]
        else:
            aggregated[item_id] = {
                "item_id": item_id,
                "item_uom": item["unit_of_measure"],
                "item_qty": item["unit_quantity"],
                "pricing_uom": item["unit_of_measure"],
            }

    organized_items = []
    for idx, data in enumerate(aggregated.values(), start=1):
        organized_items.append({
            "import_set_no": "",
            "line_no": idx,
            "item_id": data["item_id"],
            "item_uom": data["item_uom"],
            "item_qty": data["item_qty"],
            "pricing_uom": data["pricing_uom"],
            "filler1": "0",
            "filler2": "",
            "filler3": "",
            "filler4": "",
            "filler5": "",
        })
    return organized_items


def get_client_item_supplier_data(client_id: str, db: Session = Depends(get_db)) -> list[dict]:
    """Return client inventory records enriched with supplier and buyer information."""
    with get_client_db_connection(client_id, db) as conn:
        item_rows = conn.execute(queries.client_data_query()).mappings().all()
    return [dict(row) for row in item_rows]


def build_purchase_order_payload(order_data: dict, items: list[dict], db: Session = Depends(get_db)) -> list[dict]:
    """Build supplier-grouped purchase order payload with header and organized lines.

    Returns a list of dictionaries where each entry contains a `header` object
    (matching PURCHASE_ORDER_HDR shape) and an `organized_items` list containing
    PURCHASE_ORDER_LINE objects for the supplier.
    """
    client_id = order_data["client_id"]
    client_item_rows = get_client_item_supplier_data(client_id, db)

    # Keep one canonical supplier/buyer mapping per item_id.
    item_to_supplier: dict[str, dict] = {}
    for row in client_item_rows:
        item_id = row.get("item_id")
        if item_id and item_id not in item_to_supplier:
            item_to_supplier[item_id] = row

    supplier_groups: dict[str, dict] = {}
    for item in items:
        item_id = item.get("item_id")
        if not item_id:
            continue

        supplier_data = item_to_supplier.get(item_id)
        if not supplier_data:
            continue

        supplier_id = str(supplier_data.get("supplier_id", "")).strip()
        if not supplier_id:
            continue

        if supplier_id not in supplier_groups:
            supplier_groups[supplier_id] = {
                "supplier_data": supplier_data,
                "items": [],
            }

        # Prefer sales-order values when present, fall back to inventory values.
        supplier_groups[supplier_id]["items"].append({
            "item_id": item_id,
            "unit_quantity": item.get("unit_quantity", 0),
            "unit_of_measure": item.get("unit_of_measure") or supplier_data.get("base_unit"),
        })

    today = datetime.now().strftime("%m/%d/%Y")
    purchase_orders: list[dict] = []

    for idx, supplier_group in enumerate(supplier_groups.values(), start=1):
        supplier_data = supplier_group["supplier_data"]

        organized_items = organize_item_lists(supplier_group["items"])
        for line_no, line in enumerate(organized_items, start=1):
            line["import_set_no"] = idx
            line["line_no"] = line_no

        header = PURCHASE_ORDER_HDR.copy()
        header.update({
            "import_set_no": idx,
            "company_id": order_data.get("company_id", ""),
            "location_id": order_data.get("location_id", ""),
            "vendor_id": supplier_data.get("supplier_id", ""),
            "supplier_id": supplier_data.get("supplier_id", ""),
            "division_id": "",
            "buyer_id": supplier_data.get("buyer_id", ""),
            "purchase_order_type": order_data.get("purchase_order_type") or "REG",
            "po_date": today,
            "required_date": today,
            "approved": "Y",
            "current_timestamp": datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
            "external_po_num": generate_po_no(),
            "packing_basis": "partial",
        })

        purchase_orders.append({
            "header": header,
            "organized_items": organized_items,
        })

    return purchase_orders

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

