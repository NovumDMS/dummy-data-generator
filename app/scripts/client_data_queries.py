def client_customer_query() -> str:
    return f"""
        SELECT C.customer_id, C.customer_name, C.company_id, C.credit_limit, C.credit_status, S.ship_to_id
        FROM p21s_customer C
            JOIN p21s_ship_to S ON S.customer_id = C.customer_id
        WHERE credit_limit > 5000
            AND (credit_status = 'GOOD' OR credit_status = 'OPEN')
            AND delete_flag = 'N';
    """

def client_data_query() -> str:
    return f"""
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
            COALESCE(C.id, DB.id) AS buyer_id, 
            COALESCE(C.contact_name, DB.contact_name) AS buyer_name, 
            M.inv_mast_uid, 
            M.item_desc
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
        LEFT JOIN p21s_contacts C 
            ON C.id = S.buyer_id::INTEGER
        CROSS JOIN default_buyer DB
        WHERE L.stockable = 'Y'
        AND L.sellable = 'Y'
        AND L.buy = 'Y'
        AND L.qty_on_hand > 0
        AND L.delete_flag = 'N'
        AND S.delete_flag = 'N';
    """