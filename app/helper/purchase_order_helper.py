from app.helper.client_db_helper import get_client_db_connection
from fastapi import Depends
import sqlalchemy as sa
from sqlalchemy.orm import Session
from app.database import get_db
import app.scripts.data_queries as queries

def generate_po_no():
    """Generate a random purchase order number"""
    import random
    return f"99{random.randint(10000, 99999)}"

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

