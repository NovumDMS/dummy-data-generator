from app.helper.client_db_helper import get_client_db_connection
from fastapi import Depends
import sqlalchemy as sa
from sqlalchemy.orm import Session
from app.database import get_db
import app.scripts.data_queries as queries

def get_client_main_location(client_id: str, db: Session = Depends(get_db)):
    """Fetch the main location for the client"""
    with get_client_db_connection(client_id, db) as conn:
        location_id = conn.execute(sa.text("SELECT location_id FROM p21s_location LIMIT 1")).scalar()
    return location_id

def get_random_taker(client_id: str, db: Session = Depends(get_db)):
    """Fetch a random taker from the oe_hdr table"""
    with get_client_db_connection(client_id, db) as conn:
        takers = conn.execute(sa.text("SELECT DISTINCT taker FROM p21s_oe_hdr")).fetchall()
        conn.close()
    if takers:
        import random
        return random.choice(takers)[0]  # Return the taker value from the tuple
    return None

def generate_order_no():
    """Generate a random order number"""
    import random
    return f"98{random.randint(10000, 99999)}"

def get_random_items(client_id: str, number_of_items: int, db: Session = Depends(get_db)):
    """Generate random items for the sales order"""
    # This is a placeholder function. You can implement logic to fetch random items from the database or generate them as needed.
    items_list = []

    with get_client_db_connection(client_id, db) as conn:
        items = conn.execute(queries.client_data_query()).mappings().all()  # Fetch all items as dictionaries
        conn.close()

    for i in range(number_of_items):
        import random
        items_list.append(random.choice(items))

    return items_list

def get_ship_to_name(ship_to_id: str, client_id: str, db: Session = Depends(get_db)):
    """Fetch ship_to_name based on ship_to_id"""
    with get_client_db_connection(client_id, db) as conn:
        ship_to_name = conn.execute(sa.text("SELECT DISTINCT H.ship2_name FROM p21s_oe_hdr H JOIN p21s_ship_to S ON S.customer_id = H.customer_id WHERE S.ship_to_id = :ship_to_id"), {"ship_to_id": ship_to_id}).scalar()
    return ship_to_name

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