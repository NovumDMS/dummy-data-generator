import sqlalchemy as sa

def client_customer_query() -> sa.text:
    """
    Query to retrieve customers with a credit limit greater than 5000 and not on hold, CC, or COD.

    :return: SQL query to retrieve eligible customers
    """
    return sa.text(f"""
        SELECT C.customer_id, C.customer_name
        FROM p21s_customer C
        WHERE C.credit_limit > 5000
            AND C.credit_status NOT IN ('HOLD', 'CC', 'COD')
                AND C.delete_flag = 'N'
        ORDER BY C.customer_name;
    """)

def customer_data_query(customer_id: str) -> sa.text:
    """
    Query returns the required ship-to and contact information for a given customer to populate sales order fields.

    :param customer_id: The ID of the customer for which to retrieve ship-to and contact information
    :return: SQL query to retrieve ship-to and contact information for the specified customer
    """
    return sa.text(f"""
        SELECT S.ship_to_id, T.id AS contact_id, CONCAT(T.first_name, ' ', T.last_name) AS contact_name
        FROM p21s_customer C
            JOIN p21s_ship_to S ON S.customer_id = C.customer_id
            JOIN p21s_contacts T ON T.address_id = C.customer_id
        WHERE C.customer_id = {customer_id}
        LIMIT 1;
    """)

def client_data_query() -> sa.text:
    """
    Query to retrieve client data including supplier, buyer, and inventory information.

    :return: SQL query to retrieve client data for purchase order generation
    """
    return sa.text(f"""
        WITH default_buyer AS (
            SELECT
                id,
                contact_name
            FROM p21s_contacts
            WHERE buyer = 'Y'
            ORDER BY id
            LIMIT 1
        )
        SELECT 
            S.supplier_id, 
            S.supplier_name, 
            DB.id AS buyer_id, 
            DB.contact_name AS buyer_name, 
            M.inv_mast_uid, 
            M.item_id,
            M.item_desc,
            L.qty_on_hand - L.qty_allocated - L.qty_backordered AS qty_available,
            M.base_unit
        FROM p21s_inv_mast M
        JOIN p21s_inv_loc L 
            ON M.inv_mast_uid = L.inv_mast_uid
        JOIN p21s_inventory_supplier X 
            ON M.inv_mast_uid = X.inv_mast_uid
        JOIN p21s_inventory_supplier_x_loc W 
            ON X.inventory_supplier_uid = W.inventory_supplier_uid
        AND L.location_id = W.location_id
        AND W.primary_supplier = 'Y'
        JOIN p21s_supplier S 
            ON X.supplier_id = S.supplier_id
        CROSS JOIN default_buyer DB
        WHERE L.stockable = 'Y'
        AND L.sellable = 'Y'
        AND L.buy = 'Y'
        AND L.qty_on_hand > 0
        AND L.delete_flag = 'N'
        AND S.delete_flag = 'N'
        AND L.qty_on_hand - L.qty_allocated - L.qty_backordered > 0;
    """
    )
