def client_customer_query() -> str:
    return f"""
        SELECT C.customer_id, C.customer_name, C.company_id, C.credit_limit, C.credit_status, S.ship_to_id
        FROM p21s_customer C
            JOIN p21s_ship_to S ON S.customer_id = C.customer_id
        WHERE credit_limit > 5000
            AND (credit_status = 'GOOD' OR credit_status = 'OPEN')
            AND delete_flag = 'N';
    """

def client_item_query() -> str:
    return f"""
        SELECT L.inv_mast_uid, M.item_id, M.item_desc, M.buyer_id
        FROM p21s_inv_mast M
            JOIN p21s_inv_loc L ON L.inv_mast_uid = M.inv_mast_uid
        WHERE L.stockable = 'Y'
            AND L.sellable = 'Y'
            AND L.buy = 'Y'
            AND L.qty_on_hand > 0;
    """

def client_supplier_query(item_id: int) -> str:
    return f"""
        SELECT S.supplier_id, S.buyer_id, S.supplier_name
        FROM p21s_supplier S
            JOIN p21s_inventory_supplier I ON I.supplier_id = S.supplier_id
        WHERE I.inv_mast_uid = {item_id}
            AND S.delete_flag = 'N';
    """