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
    items = []

    with get_client_db_connection(client_id, db) as conn:
        items = conn.execute(queries.client_data_query()).fetchall()
        conn.close()

    for i in range(number_of_items):
        import random
        items.append(random.choice(items))

    return items