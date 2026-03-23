def client_customer_query() -> str:
    return f"""
        SELECT * FROM customers
        WHERE credit_limit > 1000
            (AND status = 'GOOD' OR status = 'OPEN')
    """

def client_item_query() -> str:
    return f"""
        SELECT * FROM inv_mast_uid
        WHERE 
    """