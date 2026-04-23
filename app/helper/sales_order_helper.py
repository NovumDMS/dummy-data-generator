from app.helper.client_db_helper import get_client_db_connection
from fastapi import Depends
import sqlalchemy as sa
from sqlalchemy.orm import Session
from app.database import get_db
import app.scripts.data_queries as queries

import logging

logger = logging.getLogger(__name__)

def get_client_main_location(client_id: str, db: Session = Depends(get_db)) -> int: 
    """
    Fetch the main location for the client.
    The main location varies from client to client

    :param client_id: ID of the client (Novum DB)
    :param db: Database session
    :return: ID of the main location for the client 
    """
    with get_client_db_connection(client_id, db) as conn:
        location_id = conn.execute(sa.text("SELECT location_id FROM p21s_location LIMIT 1")).scalar()
    return int(location_id)

def get_customer_data(customer_id: str, client_id: str, db: Session = Depends(get_db)) -> dict | None:
    """
    Fetch customer-related data such as ship_to_id and contact information
    This is data like the ship_to information and contact information for a given customer.

    :param customer_id: ID of the customer
    :param client_id: ID of the client (Novum DB)
    :param db: Database session
    :return: Dictionary containing customer data or None if not found
    """
    with get_client_db_connection(client_id, db) as conn:
        result = conn.execute(queries.customer_data_query(customer_id)).mappings().first()
    if not result:
        logger.warning(f"No customer data found for customer_id={customer_id} in client_id={client_id}. Returning None.")
        return None
    return result

def get_takers(client_id: str, db: Session = Depends(get_db)) -> list[str]:
    """
    Fetch all distinct takers from the oe_hdr table.
    Return all takers so it can be randomized within a single order set.

    :param client_id: ID of the client (Novum DB)
    :param db: Database session
    :return: List of distinct takers
    """
    with get_client_db_connection(client_id, db) as conn:
        takers = conn.execute(sa.text("SELECT DISTINCT taker FROM p21s_oe_hdr")).fetchall()
    return [t[0] for t in takers] if takers else []

def generate_order_no():
    """Generate a random order number starting with 98"""
    import random
    return f"98{random.randint(10000, 99999)}"

def get_items(client_id: str, db: Session = Depends(get_db)) -> list[dict]:
    """
    Fetch all available items for the client from the database
    This includes relevant information about the items and supplier associated for easier processing later
    
    :param client_id: ID of the client (Novum DB)
    :param db: Database session
    :return: List of dictionaries containing item data
    """
    with get_client_db_connection(client_id, db) as conn:
        items = conn.execute(queries.client_data_query()).mappings().all()
    if not items:
        logger.warning(f"No items found for client_id={client_id}. Returning empty item list.")
    return items

def get_ship_to_name(ship_to_id: str, client_id: str, db: Session = Depends(get_db)) -> str:
    """
    Fetch ship_to_name based on ship_to_id
    
    :param ship_to_id: ID of the ship_to location
    :param client_id: ID of the client (Novum DB)
    :param db: Database session
    :return: Name of the ship_to location or "Unknown Ship To Name" if not found
    """
    with get_client_db_connection(client_id, db) as conn:
        ship_to_name = conn.execute(sa.text("SELECT DISTINCT H.ship2_name FROM p21s_oe_hdr H JOIN p21s_ship_to S ON S.customer_id = H.customer_id WHERE S.ship_to_id = :ship_to_id"), {"ship_to_id": ship_to_id}).scalar()
    return ship_to_name if ship_to_name else "Unknown Ship To Name"

HDR_DEFAULT_STRUCTURE = {
    "import_set_no": "",
    "customer_id": "",
    "customer_name": "",
    "company_id": "",
    "location_id": "",
    "customer_po_no": "",
    "contact_id": "",
    "contact_name": "",
    "taker": "",
    "job_name": "",
    "order_date": "",
    "requested_date": "",
    "quote": "",
    "approved": "",
    "ship_to_id": "",
    "ship_to_name": "",
    "ship_to_address1": "",
    "ship_to_address2": "",
    "ship_to_city": "",
    "ship_to_state": "",
    "ship_to_zip_code": "",
    "ship_to_country": "",
    "source_location_id": "",
    "carrier_id": "",
    "carrier_name": "",
    "route": "",
    "packing_basis": "",
    "delivery_instructions": "",
    "terms": "",
    "terms_desc": "",
    "will_call": "",
    "class_1": "",
    "class_2": "",
    "class_3": "",
    "class_4": "",
    "class_5": "",
    "rma_flag": "",
    "freight_code": "",
    "third_party_billing_flag_desc": "",
    "capture_usage_default": "",
    "allocate": "",
    "contract_number": "",
    "invoice_batch_number": "",
    "ship_to_email_address": "",
    "set_invoice_exchange_rate_source_desc": "",
    "ship_to_phone": "",
    "currency_id": "",
    "apply_builder_allowance_flag": "",
    "quote_expiration_date": "",
    "promise_date": "",
    "import_as_quote": "",
    "quote_number": "",
    "web_reference_number": "",
    "create_invoice": "",
    "strategic_pricing_library_id": "",
    "merchandise_credit": "",
    "order_type_priority": "",
    "ups_code": "",
    "supplier_order_no": "",
    "supplier_release_no": "",
    "placed_by_name": "",
    "req_payment_upon_release": "",
    "freight_out":"",
}


LINE_DEFAULT_STRUCTURE = {
    "import_set_no": "",
    "line_no": "",
    "item_id": "",
    "unit_quantity": "",
    "unit_of_measure": "",
    "unit_price": "",
    "extended_description": "",
    "source_location_id": "",
    "ship_location_id": "",
    "product_group_id": "",
    "supplier_id": "",
    "supplier_name": "",
    "required_date": "",
    "expedite_date": "",
    "will_call": "",
    "tax_item": "",
    "ok_to_interchange": "",
    "pricing_unit": "",
    "commission_cost": "",
    "other_cost": "",
    "po_cost": "",
    "disposition": "",
    "scheduled": "",
    "manual_price_override": "",
    "commission_cost_edited": "",
    "other_cost_edited": "",
    "capture_usage": ""
}